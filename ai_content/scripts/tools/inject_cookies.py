import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_STORAGE = PROJECT_ROOT / "jarvis" / "ai_content" / "storage_state.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Full cookies provided
SEC_1PSID = "g.a000DgmZJ9ji_Ls9nOovWB3d1RteOHQfLOQ_A0FUEJECdKqsMhi1bIigPJm5N2Ll_1AS5cQ-_wACgYKARASARUSFQHGX2MiBeWNfUq_KFw-JgcYZar4pRoVAUF8yKorKaYSlFpUEkHPUadgApoa0076"
SEC_1PSIDTS = "sidts-CjYBkldj_xc1QMBPl0EAt-LuQ1Sd0RojoORm1QjIrFPdIxq18nks4rzS6R-WmXA-o5BLCYBxzsoQAA"
SEC_1PSIDCC = "AKEyXzWnHhuy1SIkWCJpngSYoNMjLoij3SxxitDmeSkOAUPwGJhVKHFYuXiwHoZ52E0yvtXcqaw"
SEC_3PSID = "g.a000DgmZJ9ji_Ls9nOovWB3d1RteOHQfLOQ_A0FUEJECdKqsMhi1YA2mv_b1RSMIvqBvFsguXAACgYKAY4SARUSFQHGX2MiV4LAGJLkwqmrs8zptfB7xRoVAUF8yKoBsjgnJlrNE1HL7MOF9pXa0076"
HOST_1PLSID = "o.flow.google.com|s.IN:g.a000DgmZJ1SuUoHFDTZsg5fwyUCdYm5hbHbhwZXtpIKi0nZks9r9WOsJMATZpmgtviecrdDb1gACgYKASISARUSFQHGX2MimTpEjFVc-6QTBooS_btbnxoVAUF8yKq2eVSmC03EwYADWy8BE8uU0076"


def inject():
    cookies = []

    # 1. Google Root Domain Cookies
    base_google = {
        "domain": ".google.com",
        "path": "/",
        "expires": 1893456000,
        "httpOnly": True,
        "secure": True,
        "sameSite": "Lax"
    }
    cookies.append({"name": "__Secure-1PSID", "value": SEC_1PSID, **base_google})
    cookies.append({"name": "__Secure-3PSID", "value": SEC_3PSID, **base_google})
    cookies.append({"name": "__Secure-1PSIDTS", "value": SEC_1PSIDTS, **base_google})
    cookies.append({"name": "__Secure-1PSIDCC", "value": SEC_1PSIDCC, **base_google})
    cookies.append({"name": "__Secure-3PSIDCC", "value": SEC_1PSIDCC, **base_google})

    # 2. Host-specific cookie for accounts.google.com
    base_accounts = {
        "domain": "accounts.google.com",
        "path": "/",
        "expires": 1893456000,
        "httpOnly": True,
        "secure": True,
        "sameSite": "Lax"
    }
    cookies.append({"name": "__Host-1PLSID", "value": HOST_1PLSID, **base_accounts})

    # 3. Cookies for flow.google.com
    base_flow = {
        "domain": "flow.google.com",
        "path": "/",
        "expires": 1893456000,
        "httpOnly": True,
        "secure": True,
        "sameSite": "Lax"
    }
    cookies.append({"name": "__Secure-1PSID", "value": SEC_1PSID, **base_flow})
    cookies.append({"name": "__Secure-3PSID", "value": SEC_3PSID, **base_flow})
    cookies.append({"name": "__Secure-1PSIDTS", "value": SEC_1PSIDTS, **base_flow})
    cookies.append({"name": "__Secure-1PSIDCC", "value": SEC_1PSIDCC, **base_flow})

    storage_data = {
        "cookies": cookies,
        "origins": []
    }

    OUTPUT_STORAGE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_STORAGE.write_text(json.dumps(storage_data, indent=2), encoding="utf-8")
    logger.info(f"[SUCCESS] Injected {len(cookies)} cookies into: {OUTPUT_STORAGE}")

    # Verify session with Playwright
    try:
        from playwright.sync_api import sync_playwright
        logger.info("Testing authentication on https://flow.google.com/ ...")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                storage_state=str(OUTPUT_STORAGE),
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            page.goto("https://flow.google.com/", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(4000)

            logger.info(f"Page title: {page.title()} | URL: {page.url}")
            page.screenshot(path="jarvis/ai_content/output/flow_auth_test.png")
            logger.info("Screenshot saved to jarvis/ai_content/output/flow_auth_test.png")

            # Check if there is a 'Create with Google Flow' button to click
            try:
                btn = page.get_by_text("Create with Google Flow").first
                if btn.is_visible():
                    logger.info("Clicking 'Create with Google Flow'...")
                    btn.click()
                    page.wait_for_timeout(5000)
                    logger.info(f"Post-click Page title: {page.title()} | URL: {page.url}")
                    page.screenshot(path="jarvis/ai_content/output/flow_auth_test_after_click.png")
            except Exception as e:
                logger.info(f"Button click check: {e}")

            # Re-export active cookies from the verified session
            context.storage_state(path=str(OUTPUT_STORAGE))
            logger.info(f"Full updated session saved to {OUTPUT_STORAGE}")

            browser.close()
            return True
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return False


if __name__ == "__main__":
    inject()
