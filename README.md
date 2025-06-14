# Tradeindata Africa Scraper (Playwright)

Скрипт собирает контактную информацию об импортёрах/экспортёрах по **всем странам Африки**  
за период с 01.01.2024 по сегодня и сохраняет в `data/output_africa.xlsx`.

## Установка

```bash
python -m venv venv          # создаём окружение (один раз)
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
playwright install chrome    # скачиваем драйвер реального Chrome
