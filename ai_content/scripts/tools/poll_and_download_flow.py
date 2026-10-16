import re
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STORAGE_STATE = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\storage_state.json")
OUTPUT_DIR = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\output")
RAW_TARGET = OUTPUT_DIR / "renders" / "raw" / "scene_demo_01_raw.mp4"
RAW_TARGET.parent.mkdir(parents=True, exist_ok=True)


def poll_and_download():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            storage_state=str(STORAGE_STATE),
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            accept_downloads=True
        )
        page = context.new_page()

        logger.info("Opening Google Flow...")
        page.goto("https://flow.google.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Open latest project
        latest_proj = page.locator("a[href*='/project/'], [data-project-id]").first
        if latest_proj.count() > 0:
            logger.info("Entering latest project...")
            latest_proj.click()
            page.wait_for_timeout(5000)

        downloaded = False
        max_minutes = 6
        start_time = time.time()

        while time.time() - start_time < max_minutes * 60:
            # Check percentage or progress
            text_content = page.content()
            percentages = re.findall(r"(\d{1,3})%", text_content)
            if percentages:
                logger.info(f"[Progress] Video rendering status: {percentages[0]}%")

            # 1. Check for video tags
            videos = page.locator("video")
            if videos.count() > 0:
                for idx in range(videos.count()):
                    src = videos.nth(idx).get_attribute("src")
                    if src and (src.startswith("http") or src.startswith("blob:")):
                        logger.info(f"Found active video element src: {src[:80]}...")
                        try:
                            res = page.request.get(src)
                            if res.ok and len(res.body()) > 50000:
                                RAW_TARGET.write_bytes(res.body())
                                downloaded = True
                                logger.info(f"[SUCCESS] Downloaded raw video directly via src: {RAW_TARGET} ({len(res.body())} bytes)")
                                break
                        except Exception as e:
                            logger.info(f"Direct fetch note: {e}")

            if downloaded:
                break

            # 2. Check for download buttons or action menus on canvas / media items
            # In Google Flow, hovering or right clicking media card or clicking 3 dots exposes download
            # Look for 3-dots menu button or download buttons
            dl_btn = page.locator("button[aria-label*='Download'], [data-tooltip*='Download'], button:has-text('Download')").first
            if dl_btn.count() > 0 and dl_btn.is_visible():
                logger.info("Found visible download button! Clicking...")
                with page.expect_download(timeout=30000) as download_info:
                    dl_btn.click()
                download = download_info.value
                download.save_as(str(RAW_TARGET))
                downloaded = True
                logger.info(f"[SUCCESS] Downloaded via download button -> {RAW_TARGET}")
                break

            # 3. Check if percentage is 100% or gone, hover over the rendered media tile
            # The media tile is in the main canvas
            media_cards = page.locator("main mat-card, .media-card, [role='listitem'], .gallery-item, div:has(> [class*='percent']), div:has(> video)")
            # Take periodic progress screenshot
            page.screenshot(path=str(OUTPUT_DIR / "flow_rendering_latest.png"))

            # If no more percent indicator and no videos found yet, try clicking the media tile in the canvas
            if not percentages:
                # Video might have finished rendering!
                logger.info("No percentage found. Checking if media card is clickable...")
                card = page.locator("div[role='button']:has(video), div[role='button']:has(img), .asset-card").first
                if card.count() > 0:
                    card.hover()
                    page.wait_for_timeout(1000)
                    card.click()
                    page.wait_for_timeout(2000)

            time.sleep(10)

        page.screenshot(path=str(OUTPUT_DIR / "flow_rendering_final_state.png"))
        browser.close()
        return downloaded


if __name__ == "__main__":
    poll_and_download()
