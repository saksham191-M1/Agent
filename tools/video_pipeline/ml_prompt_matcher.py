import os
import sys
import json
import re
import joblib
import numpy as np
from typing import Dict, List, Any, Optional

sys.stdout.reconfigure(encoding='utf-8')

class OpusPromptMLMatcher:
    def __init__(self, models_dir: Optional[str] = None, data_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = models_dir or os.path.join(base_dir, "models")
        self.data_path = data_path or os.path.join(base_dir, "data", "opus_videos.json")
        
        # Load dataset
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Opus dataset not found at: {self.data_path}")
            
        with open(self.data_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)
            
        # Load classifier and vectorizer
        clf_path = os.path.join(self.models_dir, "category_classifier.joblib")
        vec_path = os.path.join(self.models_dir, "tfidf_vectorizer.joblib")
        
        if not os.path.exists(clf_path) or not os.path.exists(vec_path):
            raise FileNotFoundError(f"Model artifacts missing. Run train_prompt_classifier.py first.")
            
        self.classifier = joblib.load(clf_path)
        self.vectorizer = joblib.load(vec_path)
        
        # Precompute matrix for all 703 prompts in dataset
        self.prompt_texts = []
        for item in self.dataset:
            p = item.get("prompt", "").strip()
            tags = " ".join(item.get("tech_tags", []))
            self.prompt_texts.append(f"{p} {tags} {tags}")
            
        self.corpus_tfidf = self.vectorizer.transform(self.prompt_texts)
        self.classes = self.classifier.classes_
        
    def predict_category(self, query: str) -> Dict[str, Any]:
        """Classify the input product query into the optimal Opus video category."""
        q_vec = self.vectorizer.transform([query])
        probs = self.classifier.predict_proba(q_vec)[0]
        prob_dict = {cls: round(float(prob), 4) for cls, prob in zip(self.classes, probs)}
        best_cat = self.classes[np.argmax(probs)]
        
        return {
            "predicted_category": best_cat,
            "confidence": round(float(np.max(probs)), 4),
            "probabilities": prob_dict
        }

    def _extract_matched_keywords(self, query: str, prompt_text: str) -> List[str]:
        """Extract matching non-stopword tokens between query and prompt."""
        q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))
        p_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', prompt_text.lower()))
        stopwords = {
            "the", "and", "with", "for", "this", "that", "from", "into", "using", "your",
            "should", "have", "make", "will", "show", "video", "create", "style", "page"
        }
        matches = (q_words & p_words) - stopwords
        return sorted(list(matches))

    def find_best_prompts(
        self,
        product_name: str,
        description: str,
        preferred_category: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Multi-factor ML retrieval:
        Combines Category Prior + TF-IDF Cosine Similarity + Keyword Overlap Density.
        """
        full_query = f"{product_name} {description}".strip()
        
        # 1. Predict optimal category
        cat_info = self.predict_category(full_query)
        target_category = preferred_category.lower() if preferred_category else cat_info["predicted_category"]
        
        # 2. Compute TF-IDF Cosine Similarity against all 703 prompts
        q_vec = self.vectorizer.transform([full_query])
        
        # Normalize and compute dot product
        from sklearn.metrics.pairwise import cosine_similarity
        sim_scores = cosine_similarity(q_vec, self.corpus_tfidf)[0]
        
        # 3. Score blending across all items
        candidates = []
        for idx, item in enumerate(self.dataset):
            tfidf_sim = float(sim_scores[idx])
            cat = item.get("category", "").lower()
            tags = item.get("tech_tags", [])
            prompt = item.get("prompt", "")
            
            # Category alignment prior
            cat_prior = cat_info["probabilities"].get(cat, 0.1)
            cat_bonus = 1.0 if cat == target_category else (0.5 if cat_prior > 0.25 else 0.2)
            
            # Keyword overlap
            matched_kw = self._extract_matched_keywords(full_query, prompt)
            kw_score = min(len(matched_kw) * 0.15, 0.6)
            
            # Composite scoring formula
            final_score = (0.50 * tfidf_sim) + (0.30 * kw_score) + (0.20 * (cat_prior * cat_bonus))
            
            candidates.append({
                "index": idx,
                "score": round(final_score, 4),
                "tfidf_similarity": round(tfidf_sim, 4),
                "slug": item.get("slug"),
                "author": item.get("author"),
                "post_url": item.get("post_url"),
                "skillry_url": item.get("skillry_url"),
                "category": cat,
                "tech_tags": tags,
                "matched_keywords": matched_kw,
                "prompt": prompt,
            })
            
        # Rank by composite score
        ranked = sorted(candidates, key=lambda x: x["score"], reverse=True)
        top_matches = ranked[:top_k]
        
        return {
            "product_name": product_name,
            "query": full_query,
            "ml_category_prediction": cat_info,
            "enforced_category": target_category,
            "total_candidates_analyzed": len(self.dataset),
            "top_matches": top_matches
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Opus 5.5 ML Prompt Matcher")
    parser.add_argument("--product", type=str, default="ChatGPT", help="Product or app name")
    parser.add_argument("--desc", type=str, default="AI conversational assistant with streaming code tokens and real-time neural throughput metrics", help="Product description or visual requirements")
    parser.add_argument("--cat", type=str, default=None, help="Explicit category override (motion, 3d, explainer, interactive)")
    parser.add_argument("--top_k", type=int, default=3, help="Number of matching prompts to return")
    
    args = parser.parse_args()
    
    matcher = OpusPromptMLMatcher()
    result = matcher.find_best_prompts(
        product_name=args.product,
        description=args.desc,
        preferred_category=args.cat,
        top_k=args.top_k
    )
    
    print("\n" + "="*80)
    print(f"🎯 OPUS 5.5 ML PROMPT MATCHER — PRODUCT: {result['product_name'].upper()}")
    print("="*80)
    print(f"Query: {result['query']}")
    pred = result['ml_category_prediction']
    print(f"Predicted Category: {pred['predicted_category'].upper()} (Confidence: {pred['confidence']*100:.1f}%)")
    print(f"Category Probabilities: {pred['probabilities']}")
    print(f"Total Database Pool: {result['total_candidates_analyzed']} curated video prompts\n")
    
    for rank, match in enumerate(result["top_matches"], 1):
        print(f"--- [RANK #{rank}] Match Score: {match['score']:.4f} (TF-IDF: {match['tfidf_similarity']:.4f}) ---")
        print(f"Category: {match['category'].upper()} | Tags: {', '.join(match['tech_tags'])} | Author: @{match['author']}")
        print(f"Matched Keywords: {', '.join(match['matched_keywords']) if match['matched_keywords'] else 'Contextual semantic'}")
        print(f"Skillry Live Remake: {match['skillry_url']}")
        print(f"Original Post: {match['post_url']}")
        print(f"Ready-to-Use Prompt:\n\"{match['prompt'][:280]}...\"\n")
