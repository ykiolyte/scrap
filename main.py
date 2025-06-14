# ============ main.py ============
from scraper.tradeindata_scraper import TradeScraper
import config as cfg

def main():
    print(">>> PARSER START")
    sc = TradeScraper()
    try:
        sc.run()
    finally:
        sc.save(cfg.OUTPUT_EXCEL)
        print("Файл:", cfg.OUTPUT_EXCEL.resolve())

if __name__ == "__main__":
    main()
