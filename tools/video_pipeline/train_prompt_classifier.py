import os
import json
import joblib
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix, ConfusionMatrixDisplay

def run_training_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "opus_videos.json")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    with open(data_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    print(f"Loaded {len(dataset)} video records from {data_path}")
    
    # Feature extraction & text normalization
    texts = []
    labels = []
    
    for item in dataset:
        prompt = item.get("prompt", "").strip()
        tags = " ".join(item.get("tech_tags", []))
        # Combine prompt with tech tags to create rich multi-modal context
        enriched_text = f"{prompt} {tags} {tags}"
        category = item.get("category", "").strip().lower()
        if prompt and category:
            texts.append(enriched_text)
            labels.append(category)
            
    print(f"Cleaned dataset: {len(texts)} samples across {len(set(labels))} categories: {sorted(list(set(labels)))}")
    
    # 1. Stratified Train / Test Split (80% train, 20% test)
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=42, stratify=labels
    )
    
    # 2. TF-IDF Feature Representation
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2,
        max_df=0.85,
        stop_words="english"
    )
    
    X_train = vectorizer.fit_transform(X_train_raw)
    X_test = vectorizer.transform(X_test_raw)
    print(f"TF-IDF Vocabulary size: {len(vectorizer.vocabulary_)} n-grams")
    
    # 3. Model Comparison
    models = {
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.1),
        "Logistic Regression (L2)": LogisticRegression(C=2.0, class_weight="balanced", max_iter=1000, random_state=42),
        "Calibrated Linear SVC": CalibratedClassifierCV(LinearSVC(C=1.0, class_weight="balanced", random_state=42), cv=5),
    }
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    comparison_results = {}
    
    print("\n--- 5-FOLD STRATIFIED CROSS-VALIDATION ---")
    for name, model in models.items():
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1_weighted")
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        comparison_results[name] = {"cv_mean": mean_score, "cv_std": std_score}
        print(f"{name:30} : Mean F1 = {mean_score:.4f} (+/- {std_score:.4f})")
        
    # 4. Final Evaluation on Test Set
    best_name = max(comparison_results, key=lambda k: comparison_results[k]["cv_mean"])
    print(f"\nSelected Best Model: {best_name}")
    
    best_model = models[best_name]
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    f1_w = f1_score(y_test, y_pred, average="weighted")
    f1_m = f1_score(y_test, y_pred, average="macro")
    
    print(f"\n--- HELD-OUT TEST EVALUATION ({len(y_test)} samples) ---")
    print(f"Accuracy : {acc * 100:.2f}%")
    print(f"Weighted F1: {f1_w:.4f}")
    print(f"Macro F1   : {f1_m:.4f}\n")
    
    report = classification_report(y_test, y_pred, digits=4)
    print(report)
    
    # 5. Confusion Matrix Visualization
    classes = sorted(list(set(labels)))
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    
    fig, ax = plt.subplots(figsize=(7, 6))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes)
    disp.plot(cmap="Blues", ax=ax, values_format="d")
    plt.title(f"Confusion Matrix: {best_name}\n(Opus 5.5 Category Classification, Test Acc: {acc*100:.1f}%)")
    plt.tight_layout()
    
    plot_path = os.path.join(models_dir, "category_confusion_matrix.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"Confusion matrix plot saved to: {plot_path}")
    
    # 6. Save Model Artifacts
    joblib.dump(best_model, os.path.join(models_dir, "category_classifier.joblib"))
    joblib.dump(vectorizer, os.path.join(models_dir, "tfidf_vectorizer.joblib"))
    
    metadata = {
        "best_model": best_name,
        "test_accuracy": round(float(acc), 4),
        "test_f1_weighted": round(float(f1_w), 4),
        "test_f1_macro": round(float(f1_m), 4),
        "num_classes": len(classes),
        "classes": classes,
        "vocab_size": len(vectorizer.vocabulary_),
        "num_samples": len(dataset)
    }
    
    with open(os.path.join(models_dir, "model_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"All model artifacts successfully serialized to: {models_dir}")
    return metadata

if __name__ == "__main__":
    run_training_pipeline()
