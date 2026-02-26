from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from scraper import ProductInfo, ScrapeResult, scrape_products

logger = logging.getLogger(__name__)


@dataclass
class FAQEntry:
    id: str
    question: str
    answer: str


@dataclass
class UpdateResult:
    entries_added: int = 0
    entries: List[FAQEntry] = field(default_factory=list)
    scrape_errors: List[str] = field(default_factory=list)
    products_found: int = 0


def _product_to_faq_entries(product: ProductInfo, idx: int) -> List[FAQEntry]:
    """Convert a single product into one or more FAQ entries."""
    entries: List[FAQEntry] = []
    name = product.name
    price = product.price
    category = product.category

    price_question = f"Giá {name} là bao nhiêu?"
    price_answer = (
        f"{name} hiện có giá {price} tại Thế Giới Di Động."
    )
    if product.old_price:
        price_answer += f" Giá gốc: {product.old_price}."
    if product.discount:
        price_answer += f" Giảm {product.discount}."
    if product.promo:
        price_answer += f" Khuyến mãi: {product.promo}."

    entries.append(
        FAQEntry(
            id=f"tgdd_price_{idx}",
            question=price_question,
            answer=price_answer,
        )
    )

    stock_question = f"{name} còn hàng không?"
    stock_answer = (
        f"Dạ, {name} ({category}) hiện đang được bán tại "
        f"Thế Giới Di Động với giá {price}. "
        f"Quý khách có thể xem chi tiết tại: {product.url}"
    )
    entries.append(
        FAQEntry(
            id=f"tgdd_stock_{idx}",
            question=stock_question,
            answer=stock_answer,
        )
    )

    return entries


def build_faq_entries(products: List[ProductInfo]) -> List[FAQEntry]:
    """Convert a list of scraped products into FAQ entries."""
    entries: List[FAQEntry] = []
    for idx, product in enumerate(products):
        entries.extend(_product_to_faq_entries(product, idx))
    return entries


def fetch_and_build(
    categories: Optional[List[str]] = None,
    max_view_more_clicks: int = 2,
) -> UpdateResult:
    """Scrape products from thegioididong.com and build FAQ entries.

    Args:
        categories: Category slugs to scrape (None = all defaults).
        max_view_more_clicks: Pagination depth per category.

    Returns:
        UpdateResult with generated FAQ entries and metadata.
    """
    logger.info("Starting product scrape …")
    scrape_result: ScrapeResult = scrape_products(
        categories=categories,
        max_view_more_clicks=max_view_more_clicks,
    )

    faq_entries = build_faq_entries(scrape_result.products)

    return UpdateResult(
        entries_added=len(faq_entries),
        entries=faq_entries,
        scrape_errors=scrape_result.errors,
        products_found=len(scrape_result.products),
    )
