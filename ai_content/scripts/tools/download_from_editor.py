import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STORAGE_STATE = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\storage_state.json")
OUTPUT_DIR = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\output")
RAW_TARGET = OUTPUT_DIR / "renders" / "raw" / "scene_demo_01_raw.mp4"
RAW_TARGET.parent.mkdir(parents=True, exist_ok=True)


def download_from_editor():
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

        video_urls = []
        def handle_response(response):
            content_type = response.headers.get("content-type", "")
            url = response.url
            if "video" in content_type or url.endswith(".mp4") or "videoplayback" in url or "blob:" in url:
                logger.info(f"[NETWORK VIDEO DETECTED] Content-Type: {content_type}, URL: {url[:100]}")
                video_urls.append(url)
                try:
                    body = response.body()
                    if len(body) > 50000:
                        logger.info(f"Captured video stream ({len(body)} bytes)! Saving...")
                        RAW_TARGET.write_bytes(body)
                except Exception:
                    pass

        page.on("response", handle_response)

        logger.info("Opening Google Flow...")
        page.goto("https://flow.google.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Open latest project
        latest_proj = page.locator("a[href*='/project/'], [data-project-id]").first
        if latest_proj.count() > 0:
            latest_proj.click()
            page.wait_for_timeout(4000)

        # Click on canvas video to enter editor
        page.mouse.click(360, 230)
        page.wait_for_timeout(3000)

        # Check <video> tags inside editor
        videos = page.locator("video").all()
        logger.info(f"Videos found in editor: {len(videos)}")
        for i, v in enumerate(videos):
            src = v.get_attribute("src")
            current_src = v.evaluate("el => el.currentSrc")
            logger.info(f"Video {i}: src={src}, currentSrc={current_src}")
            if (current_src and current_src.startswith("http")) or (src and src.startswith("http")):
                target_url = current_src if (current_src and current_src.startswith("http")) else src
                try:
                    res = page.request.get(target_url)
                    if res.ok and len(res.body()) > 50000:
                        RAW_TARGET.write_bytes(res.body())
                        logger.info(f"[SUCCESS] Downloaded video via direct request: {RAW_TARGET} ({len(res.body())} bytes)")
                        browser.close()
                        return True
                except Exception as e:
                    logger.info(f"Direct request error: {e}")

        # Look for the download button in the editor header
        # The download icon in the header (has SVG or aria-label containing Download)
        dl_icon = page.locator("button:has(svg), [role='button']:has(svg)").filter(has=page.locator("[aria-label*='Download'], [data-tooltip*='Download'], [title*='Download'], svg"))
        logger.info(f"Header button candidates: {dl_icon.count()}")

        # Let's inspect all buttons in the editor header
        header_buttons = page.locator("button, [role='button']").all()
        for b in header_buttons:
            aria = b.get_attribute("aria-label") or ""
            title = b.get_attribute("title") or ""
            tooltip = b.get_attribute("data-tooltip") or ""
            text = b.text_content().strip()
            if any("download" in x.lower() for x in [aria, title, tooltip, text]):
                logger.info(f"Found specific download button! aria={aria}, title={title}, text={text}")
                try:
                    with page.expect_download(timeout=10000) as download_info:
                        b.click()
                    download = download_info.value
                    download.save_as(str(RAW_TARGET))
                    logger.info(f"[SUCCESS] Download saved to {RAW_TARGET}")
                    browser.close()
                    return True
                except Exception as ex:
                    logger.info(f"expect_download error: {ex}")
                    # In case it didn't fire browser download event, let's wait 3s to see if network response captured it
                    page.wait_for_timeout(3000)

        # If raw video target was populated by network listener
        if RAW_TARGET.exists() and RAW_TARGET.stat().st_size > 50000:
            logger.info(f"[SUCCESS] RAW_TARGET populated by network interceptor! Size={RAW_TARGET.stat().st_size}")
            browser.close()
            return True

        # Fallback: check page evaluation for video blob conversion
        logger.info("Evaluating video element blob in browser...")
        try:
            video_base64 = page.evaluate("""async () => {
                const video = document.querySelector('video');
                if (!video) return null;
                const src = video.currentSrc || video.src;
                if (!src) return null;
                const resp = await fetch(src);
                const blob = await resp.blob();
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                });
            }""")
            if video_base64 and "base64," in video_base64:
                import base64
                data = base64.b64decode(video_base64.split("base64,")[1])
                RAW_TARGET.write_bytes(data)
                logger.info(f"[SUCCESS] Downloaded video via JS fetch blob! Size={len(data)} bytes")
                browser.close()
                return True
        except Exception as eval_err:
            logger.info(f"Evaluation error: {eval_err}")

        browser.close()
        return False


if __name__ == "__main__":
    download_from_editor()
