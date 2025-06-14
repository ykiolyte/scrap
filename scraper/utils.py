# ============ utils.py ============
import random, time, functools
from typing import Tuple
from playwright.sync_api import Page

def rnd_sleep(r: Tuple[float, float]):
    time.sleep(random.uniform(*r))

def human_type(el, text: str, delay: Tuple[float, float]):
    """Набираем текст как человек."""
    for ch in text:
        el.type(ch)
        time.sleep(random.uniform(*delay))

def human_scroll(page: Page, step_range: Tuple[int, int], pause: Tuple[float, float]):
    page.mouse.wheel(0, random.randint(*step_range))
    rnd_sleep(pause)

def retry(times=3, exceptions=(Exception,)):
    """Повторяет вызов при исключениях."""
    def wrap(f):
        @functools.wraps(f)
        def inner(*a, **kw):
            for i in range(times):
                try:
                    return f(*a, **kw)
                except exceptions:
                    if i == times - 1:
                        raise
        return inner
    return wrap
