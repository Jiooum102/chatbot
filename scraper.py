from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

BASE_URL = "https://www.thegioididong.com"

CATEGORIES: Dict[str, str] = {
    "dtdd": "Điện thoại",
    "laptop": "Laptop",
    "may-tinh-bang": "Máy tính bảng",
    "dong-ho-thong-minh": "Đồng hồ thông minh",
    "tablet": "Tablet",
}


@dataclass
class ProductInfo:
    name: str
    price: str
    category: str
    url: str
    old_price: Optional[str] = None
    discount: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[str] = None
    promo: Optional[str] = None


@dataclass
class ScrapeResult:
    products: List[ProductInfo] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    categories_scraped: List[str] = field(default_factory=list)


def _build_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


def _scroll_to_load(driver: webdriver.Chrome, max_clicks: int = 3) -> None:
    """Click the 'Xem thêm' (View more) button to load additional products."""
    for _ in range(max_clicks):
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "a.viewmore")
            if not btn.is_displayed():
                break
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            btn.click()
            time.sleep(2)
        except Exception:
            break


def _parse_listing_page(html: str, category_slug: str) -> List[ProductInfo]:
    """Parse product info from a category listing page."""
    soup = BeautifulSoup(html, "html.parser")
    products: List[ProductInfo] = []
    category_label = CATEGORIES.get(category_slug, category_slug)

    product_items = soup.select("ul.listproduct li.item")

    if not product_items:
        product_items = soup.select("ul.homeproduct li")

    if not product_items:
        product_items = soup.select(".item.__phone, .item.__laptop, .item.__tablet")

    for item in product_items:
        try:
            link_tag = item.select_one("a")
            if not link_tag:
                continue

            href = link_tag.get("href", "")
            product_url = href if href.startswith("http") else BASE_URL + href

            name_tag = item.select_one("h3") or item.select_one(".item-name") or item.select_one("a")
            name = name_tag.get_text(strip=True) if name_tag else ""
            if not name:
                continue

            price_tag = (
                item.select_one("strong.price")
                or item.select_one(".item-compare .price")
                or item.select_one(".box-p strong")
                or item.select_one(".price")
            )
            price = price_tag.get_text(strip=True) if price_tag else "Liên hệ"

            old_price_tag = item.select_one(".price-old") or item.select_one(".item-price-old")
            old_price = old_price_tag.get_text(strip=True) if old_price_tag else None

            discount_tag = item.select_one(".percent") or item.select_one(".item-discount")
            discount = discount_tag.get_text(strip=True) if discount_tag else None

            img_tag = item.select_one("img")
            image_url = None
            if img_tag:
                image_url = img_tag.get("data-src") or img_tag.get("src")

            promo_tag = item.select_one(".item-gift") or item.select_one(".item-promo")
            promo = promo_tag.get_text(strip=True) if promo_tag else None

            products.append(
                ProductInfo(
                    name=name,
                    price=price,
                    category=category_label,
                    url=product_url,
                    old_price=old_price,
                    discount=discount,
                    image_url=image_url,
                    promo=promo,
                )
            )
        except Exception as exc:
            logger.debug("Failed to parse product item: %s", exc)

    return products


def scrape_category(
    driver: webdriver.Chrome,
    category_slug: str,
    max_view_more_clicks: int = 2,
) -> List[ProductInfo]:
    """Scrape all visible products from a single category page."""
    url = f"{BASE_URL}/{category_slug}"
    logger.info("Scraping category: %s → %s", category_slug, url)

    driver.get(url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(3)

    _scroll_to_load(driver, max_clicks=max_view_more_clicks)

    html = driver.page_source
    return _parse_listing_page(html, category_slug)


def scrape_products(
    categories: Optional[List[str]] = None,
    max_view_more_clicks: int = 2,
) -> ScrapeResult:
    """Scrape product listings from thegioididong.com.

    Args:
        categories: List of category slugs to scrape. Defaults to all.
        max_view_more_clicks: How many times to click "Xem thêm" per category.

    Returns:
        ScrapeResult with products, errors, and categories scraped.
    """
    if categories is None:
        categories = list(CATEGORIES.keys())

    result = ScrapeResult()
    driver: Optional[webdriver.Chrome] = None

    try:
        driver = _build_driver()

        for slug in categories:
            try:
                products = scrape_category(driver, slug, max_view_more_clicks)
                result.products.extend(products)
                result.categories_scraped.append(slug)
                logger.info(
                    "Category '%s': found %d products", slug, len(products)
                )
            except Exception as exc:
                msg = f"Failed to scrape category '{slug}': {exc}"
                logger.error(msg)
                result.errors.append(msg)

    except Exception as exc:
        msg = f"Failed to initialise browser: {exc}"
        logger.error(msg)
        result.errors.append(msg)
    finally:
        if driver is not None:
            driver.quit()

    return result
