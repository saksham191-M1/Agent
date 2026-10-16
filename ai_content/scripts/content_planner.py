import json
from typing import Dict, Any, List

class ContentPlanner:
    def __init__(self, model_version="omni-1.1"):
        """
        Initializes the Content Planner for planning, writing, and script generation.
        Includes a feedback loop to re-feed responses for continuous improvement.
        """
        self.model_version = model_version

    def generate_draft(self, topic: str, content_type: str, direction: Dict[str, Any]) -> str:
        """
        Generates the initial draft of the content (script, blog, plan, etc.).
        """
        print(f"[{self.__class__.__name__}] Generating initial {content_type} draft for: {topic}...")
        # Mocking the initial Omni 1.1 generation
        draft = f"Initial draft for {content_type} about {topic}. The tone is {direction.get('tone', 'standard')}."
        draft += "\nScene 1: Introduction.\nScene 2: Main features.\nScene 3: Call to action."
        return draft

    def critique_and_improve(self, draft: str, content_type: str, iterations: int = 1) -> str:
        """
        Refeeds the response back to the model for further improvement.
        """
        current_version = draft
        for i in range(iterations):
            print(f"[{self.__class__.__name__}] Refeeding response for improvement (Iteration {i+1}/{iterations})...")
            # Mocking the Omni 1.1 refinement process
            current_version = current_version.replace("Initial draft", "Refined and polished version")
            current_version += f"\n[Refinement {i+1}]: Added stronger hooks, better pacing, and more engaging language suitable for {content_type}."
        
        return current_version

    def create_optimized_content(self, topic: str, content_type: str, direction: Dict[str, Any], feedback_iterations: int = 2) -> str:
        """
        End-to-end process: Generate draft, then re-feed it for improvements.
        """
        print(f"[{self.__class__.__name__}] Starting creation process for {content_type}")
        draft = self.generate_draft(topic, content_type, direction)
        
        # Refeed the response to improve it
        final_content = self. critique_and_improve(draft, content_type, iterations=feedback_iterations)
        
        print(f"[{self.__class__.__name__}] Final {content_type} is ready.")
        return final_content

if __name__ == "__main__":
    planner = ContentPlanner()
    test_direction = {"tone": "Energetic and persuasive"}
    
    print("\n--- Script Writing ---")
    script = planner.create_optimized_content("Smart Coffee Maker", "Video Script", test_direction, feedback_iterations=2)
    print(script)
    
    print("\n--- Content Planning ---")
    plan = planner.create_optimized_content("Smart Coffee Maker", "Social Media Content Plan", test_direction, feedback_iterations=1)
    print(plan)
