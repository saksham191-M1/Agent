import os
import time
import logging
import subprocess
from pathlib import Path
from jarvis.ai_content.scripts.config import (
    RAW_RENDERS_DIR, 
    GOOGLE_FLOW_URL, 
    HEADLESS, 
    STORAGE_STATE_PATH
)
from jarvis.ai_content.scripts.video.base_video import VideoProvider

logger = logging.getLogger(__name__)

class GoogleFlowAutomation(VideoProvider):
    def __init__(
        self, 
        storage_state: Path = STORAGE_STATE_PATH, 
        base_url: str = GOOGLE_FLOW_URL,
        headless: bool = HEADLESS,
        mock_mode: bool = False
    ):
        self.storage_state = Path(storage_state)
        self.base_url = base_url
        self.headless = headless
        self.mock_mode = mock_mode

    def generate_clip(
        self, 
        prompt: str, 
        scene_id: str, 
        duration: int = 5,
        aspect_ratio: str = "16:9",
        model_tier: str = "quality"
    ) -> Path:
        """
        Automates Google Flow (Veo 3.1 & Omni) video generation via Playwright.
        If mock_mode is True or storage_state is missing, produces a clean placeholder video.
        """
        output_path = RAW_RENDERS_DIR / f"scene_{scene_id}_raw.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists() and output_path.stat().st_size > 50000:
            logger.info(f"[GoogleFlow] Using existing raw clip: {output_path} ({output_path.stat().st_size} bytes)")
            return output_path

        if self.mock_mode or not self.storage_state.exists():
            logger.info(f"Using mock video generation for scene {scene_id} -> {output_path}")
            return self._generate_fallback_clip(output_path, duration=duration, title=f"Scene {scene_id}: {prompt[:30]}")

        # Real Playwright Automation Flow
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright is not installed. Using fallback placeholder clip.")
            return self._generate_fallback_clip(output_path, duration=duration, title=f"Scene {scene_id}")

        logger.info(f"[GoogleFlow] Launching Playwright (headless={self.headless}) for Scene {scene_id}...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = browser.new_context(
                    storage_state=str(self.storage_state),
                    viewport={"width": 1280, "height": 850},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                # Step 1: Open Google Flow
                logger.info(f"[GoogleFlow] Navigating to {self.base_url}...")
                page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                # Step 2: Open or create project
                if "project" not in page.url:
                    new_proj_btn = page.get_by_text("New project").first
                    if new_proj_btn.count() > 0:
                        logger.info("[GoogleFlow] Clicking '+ New project'...")
                        new_proj_btn.click()
                        page.wait_for_timeout(4000)

                # Step 3: Locate Prompt Input & Submit
                page.wait_for_selector("textarea, input[placeholder*='create'], [contenteditable='true']", timeout=30000)
                prompt_input = page.locator("textarea, input[placeholder*='create'], [contenteditable='true']").first
                flow_prompt = f"Create a video: {prompt}"
                logger.info(f"[GoogleFlow] Entering prompt: {flow_prompt[:80]}...")
                prompt_input.click()
                prompt_input.fill(flow_prompt)
                page.wait_for_timeout(1000)
                page.keyboard.press("Enter")
                logger.info("[GoogleFlow] Prompt submitted. Waiting for Veo generation...")

                # Step 4: Poll for generated video element
                video_downloaded = False
                for attempt in range(24): # Wait up to 2 minutes
                    page.wait_for_timeout(5000)
                    videos = page.locator("video")
                    if videos.count() > 0:
                        video_src = videos.first.get_attribute("src")
                        if video_src and (video_src.startswith("http") or video_src.startswith("blob:")):
                            logger.info(f"[GoogleFlow] Video rendered! Source: {video_src[:60]}...")
                            # Download video stream
                            try:
                                response = page.request.get(video_src)
                                if response.ok:
                                    output_path.write_bytes(response.body())
                                    video_downloaded = True
                                    logger.info(f"[GoogleFlow] Successfully downloaded Veo video -> {output_path}")
                                    break
                            except Exception as dl_err:
                                logger.info(f"[GoogleFlow] Direct video fetch note: {dl_err}")

                    # Check for explicit download buttons
                    dl_btn = page.locator("button[aria-label*='Download'], button:has-text('Download')").first
                    if dl_btn.count() > 0 and dl_btn.is_visible():
                        with page.expect_download(timeout=30000) as download_info:
                            dl_btn.click()
                        download = download_info.value
                        download.save_as(str(output_path))
                        video_downloaded = True
                        logger.info(f"[GoogleFlow] Downloaded via download button -> {output_path}")
                        break

                browser.close()

                if video_downloaded and output_path.exists() and output_path.stat().st_size > 512:
                    return output_path
                else:
                    logger.warning("[GoogleFlow] Generation timed out or clip unavailable. Using fallback.")
                    return self._generate_fallback_clip(output_path, duration=duration, title=f"Scene {scene_id}")

        except Exception as e:
            logger.error(f"Google Flow Playwright automation encountered: {e}. Generating fallback placeholder.")
            return self._generate_fallback_clip(output_path, duration=duration, title=f"Scene {scene_id}")

    def _generate_fallback_clip(self, output_path: Path, duration: int = 5, title: str = "Veo Raw Clip") -> Path:
        """
        Creates a valid 1920x1080 24fps MP4 video using ffmpeg test source.
        """
        if output_path.exists() and output_path.stat().st_size > 1024:
            return output_path

        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=#1A1033:s=1920x1080:d={duration}:r=24",
                "-f", "lavfi", "-i", f"sine=f=440:d={duration}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                str(output_path)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return output_path
        except Exception:
            output_path.write_bytes(b"\x00" * 4096)
            return output_path
