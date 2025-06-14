# ============ tradeindata_scraper.py ============
from bs4 import BeautifulSoup
import pandas as pd, random
from playwright.sync_api import TimeoutError as PWTimeout
from .browser_playwright import get_context
from .utils import rnd_sleep, human_type, human_scroll, retry
import config as cfg
import time
import csv
import os

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
        # self.page.wait_for_selector("a[href*='/logout']",
        #                             timeout=60000)
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
        # for role in ("0","1"):                     # 0=import,1=export
        #     for country in cfg.COUNTRIES:
        #         print(f"{country}  ({'Imp' if role=='0' else 'Exp'})")
        #         self.apply_filters(country, role)
        #         links=self.collect_links(cfg.MAX_COMPANIES_PER_COUNTRY)
        #         print("  links:",len(links))
        #         random.shuffle(links)
        #         for lnk in links: self.parse_company(lnk,country,role)
        data_dir = "./data"
        csv_files = sorted(
            [f for f in os.listdir(data_dir) if f.endswith("_items.csv")],
            key=lambda x: int(x.split("_")[0]) if x.split("_")[0].isdigit() else 0
        )
        all_links = []
        for csv_file in csv_files:
            csv_path = os.path.join(data_dir, csv_file)
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_links.append(row["link"])

        print(f"Всего ссылок из файлов: {len(all_links)}")
        for lnk in all_links:
            print(f"Обработка {lnk}")
            # self.parse_company(BASE + lnk, "Unknown", "Unknown")
            try:
                self.page.goto("https://www.tradeindata.com" + lnk, wait_until="domcontentloaded", timeout=60000)
                self.page.wait_for_selector(".highcharts-data-label", timeout=60000)
                labels = self.page.query_selector_all(".highcharts-data-label")
                print(f"Найдено {len(labels)} элементов с классом highcharts-data-label")
                for i, label in enumerate(labels, 1):
                    print(f"{i}: {label.inner_text()}")
            except:
                print(f"Ошибка при переходе на {lnk}, пропускаем.")
                continue





    def get_items(self):
        print("→ Перенаправляем на страницу покупателя…")
        time.sleep(10)
        response = self.page.goto("https://www.tradeindata.com/buyer/?CId=eJwzNDY2MDA0AgAFcwFb", wait_until="domcontentloaded", timeout=60000)
        time.sleep(10)
        print(response.status)
        print(response.url)
        def get_links():
            all_links = []
            page = 0
            while True:
                self.page.wait_for_selector("li.page_last a.page_button", timeout=60000)
                html = self.page.content()
                soup = BeautifulSoup(html, "lxml")
                items = soup.find_all("div", class_="item")

                new_links = [
                    a["href"] for item in items
                    if (a := item.find("a")) and a.has_attr("href") and a["href"].startswith("/detail/")
                ]
                print("Ссылки на этой странице:", new_links)
                all_links.extend(new_links)
                # Save new_links to CSV file for each page
                csv_filename = f"./data/{page}_items.csv"
                with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["link"])
                    for link in new_links:
                        writer.writerow([link])
                print(f"Сохранено {len(new_links)} ссылок в файл {csv_filename}")
                page += 1

                next_btn = self.page.query_selector("li.page_last a.page_button")
                if next_btn:
                    print("Переход на следующую страницу…")
                    next_btn.click()
                    self.page.wait_for_load_state("networkidle", timeout=60000)
                else:
                    print("Кнопка 'Следующая страница' не найдена. Конец.")
                    break

            print("Всего ссылок собрано:", len(all_links))
            return all_links
        links = get_links()
        return links



    # ---------- сохранить Excel -----
    def save(self, path):
        pd.DataFrame(self.data).to_excel(path, index=False)
