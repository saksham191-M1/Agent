import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

STORAGE_STATE = Path(r"c:\Users\hemam\multi lingo\jar\jarvis\ai_content\storage_state.json")

def inspect_buttons():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(STORAGE_STATE))
        page = context.new_page()
        page.goto("https://flow.google.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        latest_proj = page.locator("a[href*='/project/'], [data-project-id]").first
        if latest_proj.count() > 0:
            latest_proj.click()
            page.wait_for_timeout(4000)

        matches = page.get_by_text("Approve", exact=False).all()
        print(f"Total elements matching Approve: {len(matches)}")
        for i, m in enumerate(matches):
            try:
                tag = m.evaluate("el => el.tagName")
                text = m.text_content().strip()
                html = m.evaluate("el => el.outerHTML")[:200]
                print(f"Match {i}: tag={tag}, text={text}")
                print(f"   HTML: {html}")
            except Exception as e:
                print(f"Match {i} error: {e}")

        # Also let's check with get_by_role('button')
        buttons = page.get_by_role("button").all()
        print(f"\nTotal buttons on page: {len(buttons)}")
        for b in buttons:
            txt = b.text_content().strip()
            if "approve" in txt.lower() or "reject" in txt.lower():
                print(f"Button text: {txt}, HTML: {b.evaluate('el => el.outerHTML')[:200]}")

        browser.close()

if __name__ == "__main__":
    inspect_buttons()
