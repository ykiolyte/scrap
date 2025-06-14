# ============ tradeindata_scraper.py ============
from bs4 import BeautifulSoup
import pandas as pd, random
from playwright.sync_api import TimeoutError as PWTimeout
from .browser_playwright import get_context
from .utils import rnd_sleep, human_type, human_scroll, retry
import config as cfg

# -------- URL & селекторы (февр-июн 2025) --------------
BASE        = "https://www.tradeindata.com"
LOGIN_URL   = f"{BASE}/login"
LIST_URL    = f"{BASE}/supplier"     # роль меняем параметром Role

# элементы формы фильтров
ROLE_BTN    = 'div.role_choose .btn[data-role="{role}"]'
COUNTRY_INP = 'input[name="Country2"]'
DATE_ONEYEAR= 'div[regf="search-date"] input[value="12"]'
SEARCH_BTN  = '#filter_form .btn_list .btn.search'

# список компаний
CARD_LINK   = '.bg_container > .item a.top_msg_out.company_detail_url'
LOAD_MORE   = '#turn_page a.page_button[title="Next page"]'

# карточка детали
NAME        = '.detail_name, .title'
CONTACT_VAL = 'span.sec_name:has-text("{label}") + span.sec_value'
TOP_COUNTRY = 'div.new_name:has-text("Top Countries") ~ div.highcharts-container text.highcharts-text-outline'
TOP_HSCODE  = 'div.new_name:has-text("Top HSCODE") ~ div.num_value li'

class TradeScraper:
    def __init__(self):
        self.pw, self.ctx = get_context()
        self.page = self.ctx.new_page()
        self.data = []

    # ---------- авторизация ----------
    def login(self):
        print("→ Переходим на главную страницу…")
        self.page.goto("https://www.tradeindata.com", timeout=60000)

        # 1) кликаем «Login» в шапке
        print("→ Нажимаем кнопку Login…")
        self.page.wait_for_selector("a.login", timeout=60000)
        self.page.click("a.login")

        # 2) ждём появления формы
        self.page.wait_for_selector('input[name="Email"]', timeout=60000)
        print("→ Вводим учётные данные…")

        human_type(self.page.locator('input[name="Email"]'),
                   cfg.TRADEINDATA_USER, cfg.TYPING_DELAY)
        human_type(self.page.locator('input[name="Password"]'),
                   cfg.TRADEINDATA_PASS, cfg.TYPING_DELAY)

        rnd_sleep((0.4, 0.8))
        self.page.click('input.btn_submit')          # «Sign In»
        self.page.wait_for_selector("a[href*='/logout']",
                                    timeout=60000)
        print("✓ Вход выполнен.")




    # ---------- выбор фильтров -------
    def apply_filters(self, country: str, role: str):
        """role: '0' = importer, '1' = exporter"""
        self.page.goto(LIST_URL, timeout=60000)
        # роль
        self.page.click(ROLE_BTN.format(role=role))
        # страна
        self.page.click(COUNTRY_INP)
        human_type(self.page.locator(COUNTRY_INP), country, cfg.TYPING_DELAY)
        self.page.keyboard.press("Enter")
        # дата – past 1 year
        self.page.check(DATE_ONEYEAR)
        # поиск
        rnd_sleep((0.4, 0.7))
        self.page.click(SEARCH_BTN)
        self.page.wait_for_selector(CARD_LINK, timeout=60000)

    # ---------- собираем ссылки -----
    def collect_links(self, limit: int):
        links=set()
        while len(links)<limit:
            links |= set(self.page.eval_on_selector_all(
                CARD_LINK, "els=>els.map(e=>e.href)"
            ))
            if len(links)>=limit: break
            try:
                self.page.click(LOAD_MORE, timeout=60000)
            except PWTimeout: break
            human_scroll(self.page, cfg.MOUSE_STEP, cfg.SCROLL_PAUSE)
        return list(links)[:limit]

    # ---------- разбираем карточку --
    @retry()
    def parse_company(self, url:str,country:str,role:str):
        self.page.goto(url, timeout=60000)
        self.page.wait_for_selector(NAME, timeout=60000)
        soup=BeautifulSoup(self.page.content(),"lxml")
        name=soup.select_one(NAME).text.strip()
        website = soup.select_one(CONTACT_VAL.format(label="Website"))
        email   = soup.select_one(CONTACT_VAL.format(label="E-mail"))
        phone   = soup.select_one(CONTACT_VAL.format(label="Telephone")) \
              or soup.select_one(CONTACT_VAL.format(label="Mobile"))
        # топ-страны и HS-коды
        top_country=", ".join(e.text.strip() for e in soup.select(TOP_COUNTRY)[:5])
        top_hs=", ".join(e.text.strip() for e in soup.select(TOP_HSCODE)[:10])
        self.data.append(dict(
            Name=name, Country=country, Role=("Importer" if role=="0" else "Exporter"),
            TopCountries=top_country, TopHSCode=top_hs,
            Website=website.text.strip() if website else "",
            Email=email.text.strip() if email else "",
            Phone=phone.text.strip() if phone else ""
        ))
        rnd_sleep(cfg.DETAIL_PAUSE)

    # ---------- основной обход ------
    def run(self):
        self.login()
        for role in ("0","1"):                     # 0=import,1=export
            for country in cfg.COUNTRIES:
                print(f"{country}  ({'Imp' if role=='0' else 'Exp'})")
                self.apply_filters(country, role)
                links=self.collect_links(cfg.MAX_COMPANIES_PER_COUNTRY)
                print("  links:",len(links))
                random.shuffle(links)
                for lnk in links: self.parse_company(lnk,country,role)

    # ---------- сохранить Excel -----
    def save(self, path):
        pd.DataFrame(self.data).to_excel(path, index=False)
