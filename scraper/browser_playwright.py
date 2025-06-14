"""
Запускает persistent-Chromium + прокси с авторизацией через
встроенный механизм Playwright (`proxy={server,username,password}`).
"""

from playwright.sync_api import sync_playwright
import config as cfg

def get_context():
    pw = sync_playwright().start()

    context = pw.chromium.launch_persistent_context(
        user_data_dir=str(cfg.PROFILE_DIR),
        headless=cfg.HEADLESS,
        proxy={
            "server":   cfg.PROXY_SERVER,   # «http://ip:port»
            "username": cfg.PROXY_USER,
            "password": cfg.PROXY_PASS,
        },
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 800},
    )

    # Stealth-патч (чтобы не палился Headless)
    from playwright_stealth import stealth_sync
    stealth_sync(context)

    print(f"✓ используем: {cfg.PROXY_SERVER} ({cfg.PROXY_USER})")
    return pw, context
