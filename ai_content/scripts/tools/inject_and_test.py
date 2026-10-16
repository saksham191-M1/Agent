import json
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

OUTPUT_PATH = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\storage_state.json")

# Token values
V_1PSID = "g.a000DgmZJ9ji_Ls9nOovWB3d1RteOHQfLOQ_A0FUEJECdKqsMhi1bIigPJm5N2Ll_1AS5cQ-_wACgYKARASARUSFQHGX2MiBeWNfUq_KFw-JgcYZar4pRoVAUF8yKorKaYSlFpUEkHPUadgApoa0076"
V_1PSIDTS = "sidts-CjYBkldj_xc1QMBPl0EAt-LuQ1Sd0RojoORm1QjIrFPdIxq18nks4rzS6R-WmXA-o5BLCYBxzsoQAA"
V_1PSIDCC = "AKEyXzWnHhuy1SIkWCJpngSYoNMjLoij3SxxitDmeSkOAUPwGJhVKHFYuXiwHoZ52E0yvtXcqaw"
V_3PSID = "g.a000DgmZJ9ji_Ls9nOovWB3d1RteOHQfLOQ_A0FUEJECdKqsMhi1YA2mv_b1RSMIvqBvFsguXAACgYKAY4SARUSFQHGX2MiV4LAGJLkwqmrs8zptfB7xRoVAUF8yKoBsjgnJlrNE1HL7MOF9pXa0076"
V_HOST_1PLSID = "o.flow.google.com|s.IN:g.a000DgmZJ1SuUoHFDTZsg5fwyUCdYm5hbHbhwZXtpIKi0nZks9r9WOsJMATZpmgtviecrdDb1gACgYKASISARUSFQHGX2MimTpEjFVc-6QTBooS_btbnxoVAUF8yKq2eVSmC03EwYADWy8BE8uU0076"


def inject_and_test():
    cookies = []

    # Target domains
    flow_domains = [".google.com", "flow.google.com", ".flow.google.com", "accounts.google.com"]

    for d in flow_domains:
        base = {
            "domain": d,
            "path": "/",
            "expires": 1893456000,
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax"
        }
        cookies.append({"name": "__Secure-1PSID", "value": V_1PSID, **base})
        cookies.append({"name": "__Secure-1PSIDTS", "value": V_1PSIDTS, **base})
        cookies.append({"name": "__Secure-1PSIDCC", "value": V_1PSIDCC, **base})
        cookies.append({"name": "__Secure-3PSID", "value": V_3PSID, **base})
        cookies.append({"name": "__Secure-3PSIDCC", "value": V_1PSIDCC, **base})

    # Host specific cookie
    cookies.append({
        "name": "__Host-1PLSID",
        "value": V_HOST_1PLSID,
        "domain": "accounts.google.com",
        "path": "/",
        "expires": 1893456000,
        "httpOnly": True,
        "secure": True,
        "sameSite": "Lax"
    })
    cookies.append({
        "name": "__Host-1PLSID",
        "value": V_HOST_1PLSID,
        "domain": "flow.google.com",
        "path": "/",
        "expires": 1893456000,
        "httpOnly": True,
        "secure": True,
        "sameSite": "Lax"
    })

    storage_state = {
        "cookies": cookies,
        "origins": []
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(storage_state, indent=2))
    logger.info(f"Saved {len(cookies)} cookies to {OUTPUT_PATH}")

    # Launch Playwright and test
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            storage_state=str(OUTPUT_PATH),
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        logger.info("Opening https://flow.google.com/ ...")
        page.goto("https://flow.google.com/", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)

        logger.info(f"Page Title: {page.title()} | URL: {page.url}")
        page.screenshot(path=r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\output\flow_live_test.png")
        logger.info("Screenshot captured at output/flow_live_test.png")

        # Save any updated tokens back to storage state
        context.storage_state(path=str(OUTPUT_PATH))

        browser.close()


if __name__ == "__main__":
    inject_and_test()
