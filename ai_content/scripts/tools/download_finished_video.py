import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STORAGE_STATE = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\storage_state.json")
OUTPUT_DIR = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\output")
RAW_TARGET = OUTPUT_DIR / "renders" / "raw" / "scene_demo_01_raw.mp4"
RAW_TARGET.parent.mkdir(parents=True, exist_ok=True)


def download_video():
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

        # Inspect all video elements
        videos = page.locator("video").all()
        logger.info(f"Total <video> elements: {len(videos)}")
        for idx, v in enumerate(videos):
            src = v.get_attribute("src")
            current_src = v.evaluate("el => el.currentSrc")
            logger.info(f"Video {idx}: src={src}, currentSrc={current_src}")
            if current_src and (current_src.startswith("http") or current_src.startswith("blob:")):
                try:
                    res = page.request.get(current_src)
                    if res.ok and len(res.body()) > 10000:
                        RAW_TARGET.write_bytes(res.body())
                        logger.info(f"[SUCCESS] Saved video {idx} directly via currentSrc -> {RAW_TARGET} ({len(res.body())} bytes)")
                        browser.close()
                        return True
                except Exception as e:
                    logger.info(f"Fetch failed: {e}")

        # If direct fetch didn't catch it, let's click on the video card on canvas to open player/context menu
        logger.info("Attempting click on canvas video card...")
        # Look for the card or play button on the main canvas
        canvas_item = page.locator("main, [role='main']").locator("div:has(video), div:has-text('100%'), [role='button']").first
        if canvas_item.count() == 0:
            canvas_item = page.locator(".media-card, [role='listitem']").first

        logger.info(f"Found canvas item matches: {canvas_item.count()}")
        # Click on the center of the canvas where the video is
        page.mouse.click(360, 230)
        page.wait_for_timeout(2000)
        page.screenshot(path=str(OUTPUT_DIR / "flow_clicked_video.png"))

        # Look for download button
        dl_buttons = page.locator("button[aria-label*='Download'], [data-tooltip*='Download'], button:has-text('Download'), [aria-label*='download']").all()
        logger.info(f"Download buttons found: {len(dl_buttons)}")
        for btn in dl_buttons:
            if btn.is_visible():
                logger.info(f"Clicking visible download button: {btn.get_attribute('aria-label')}")
                try:
                    with page.expect_download(timeout=15000) as download_info:
                        btn.click()
                    download = download_info.value
                    download.save_as(str(RAW_TARGET))
                    logger.info(f"[SUCCESS] Downloaded via button -> {RAW_TARGET}")
                    browser.close()
                    return True
                except Exception as err:
                    logger.info(f"Download click error: {err}")

        # Check Videos tab on left sidebar
        videos_tab = page.locator("span:has-text('Videos'), [role='button']:has-text('Videos'), a:has-text('Videos')").first
        if videos_tab.count() > 0:
            logger.info("Clicking 'Videos' tab on left sidebar...")
            videos_tab.click()
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUTPUT_DIR / "flow_videos_tab.png"))

        browser.close()
        return False


if __name__ == "__main__":
    download_video()
