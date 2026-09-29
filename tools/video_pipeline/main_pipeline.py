import os
import sys
import argparse

# Add jarvis root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from colorama import Fore, init

init(autoreset=True)

from type1_ai.viral_ai import run_type1_viral_pipeline
from type1_ai.product_ad_ai import run_type1_ad_pipeline

def run_type1_viral(keyword, audience):
    print(f"{Fore.CYAN}[Type 1 - Viral AI]{Fore.RESET} Starting viral content generation for: {keyword} (Audience: {audience})")
    run_type1_viral_pipeline(keyword, audience)
    
def run_type1_ad():
    # Keyword is not used here because the ad pipeline has its own intake flow
    run_type1_ad_pipeline()
    
def run_type2_motion(keyword):
    print(f"{Fore.MAGENTA}[Type 2 - Motion Graphics]{Fore.RESET} Starting motion graphic video for: {keyword}")
    # TODO: Fetch Stock/Screenshots -> Ken Burns/Pan -> Text overlays
    print(f"{Fore.YELLOW}-> Step 1: Fetching stock media & screenshots...{Fore.RESET}")

def run_type2_repost(keyword):
    print(f"{Fore.MAGENTA}[Type 2 - Reposter]{Fore.RESET} Starting viral repost transformation for: {keyword}")
    # TODO: yt-dlp fetch viral video -> add commentary/voice -> add watermark
    print(f"{Fore.YELLOW}-> Step 1: Searching for viral videos matching '{keyword}'...{Fore.RESET}")

def main():
    print(f"{Fore.GREEN}=== Video Generation Pipeline ==={Fore.RESET}")
    print("\nSelect the Video Type:")
    print("1. [Type 1] AI Viral Entertainment")
    print("2. [Type 1] AI Product Ad")
    print("3. [Type 2] Motion Graphics (Stock / Screenshots)")
    print("4. [Type 2] Viral Reposter (Download & Transform)")
    
    choice = input("\nEnter choice (1-4): ")
    
    print("\n" + "="*40)
    if choice == '1':
        keyword = input("Enter the Keyword or Topic: ")
        audience = input("Enter Target Audience (e.g., Kids, Gen Z, General): ")
        if not audience.strip():
            audience = "General"
        run_type1_viral(keyword, audience)
    elif choice == '2':
        run_type1_ad()
    elif choice == '3':
        keyword = input("Enter the Keyword or Topic: ")
        run_type2_motion(keyword)
    elif choice == '4':
        keyword = input("Enter the Keyword or Topic: ")
        run_type2_repost(keyword)
    else:
        print(f"{Fore.RED}Invalid choice.{Fore.RESET}")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
