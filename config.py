from pathlib import Path
from datetime import date
import os, random

### TradeInData учётка
TRADEINDATA_USER = os.getenv("TRADE_USER", "poiskzapchast@yandex.ru")
TRADEINDATA_PASS = os.getenv("TRADE_PASS", "Trade2510")

### Даты фильтра
START_DATE = "01/01/2024"
END_DATE   = date.today().strftime("%d/%m/%Y")

### Целевые страны — Африка (демо: одна страна)
COUNTRIES = ["Kenya"]  # можно заменить на все страны Африки

### Поведение скролла / задержек
MAX_COMPANIES_PER_COUNTRY = 500
SCROLL_PAUSE = (1.0, 2.0)
DETAIL_PAUSE = (1.8, 3.2)
TYPING_DELAY = (0.09, 0.15)
MOUSE_STEP   = (200, 400)

### Прокси-пул: 10 HTTP-прокси с авторизацией
LOGIN = "bbimba385"
PWD   = "JiR3qrNcgt"

IP_LIST = [
    "217.194.153.11"
]

Disabled_IP_LIST = [ "45.153.162.123",
    "45.153.162.122", "45.153.163.193", "45.10.156.92",  "45.153.163.113",
    "45.153.163.112",]

PROXY_POOL = [{"host": ip, "port": "50100", "user": LOGIN, "pass": PWD} for ip in IP_LIST]

def pick_proxy():
    """Берёт случайный прокси-словарь из пула."""
    return random.choice(PROXY_POOL)

# Выбираем активный прокси
PROXY = pick_proxy()
PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS = (
    PROXY["host"], PROXY["port"], PROXY["user"], PROXY["pass"]
)
PROXY_SERVER = f"http://{PROXY_HOST}:{PROXY_PORT}"

### Настройки запуска браузера
HEADLESS    = False  # Включите True после ручного логина и прогрева
PROFILE_DIR = Path("user_data").resolve()

### Папки и выходной Excel-файл
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_EXCEL = DATA_DIR / "output_africa.xlsx"

### Для offline-демонстрации
OFFLINE_HTML = Path("Tradeindata - Global Manufacturers and Importers Directory.html")
DEMO_EXCEL   = DATA_DIR / "demo_kenya.xlsx"
