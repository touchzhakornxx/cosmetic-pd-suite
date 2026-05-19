import re
from typing import Any, Dict, List, Optional
import httpx
from playwright.sync_api import sync_playwright
from .base import BaseScraper
from backend.parser.normalizer import parse_ingredient_text


def scrape_category_links(category_url: str) -> List[str]:
    """
    Discover every product URL across all pagination pages of a MySkinRecipes
    category (PrestaShop).  Uses sequential numeric probing (?page=1, ?page=2,
    …) so the loop is fully deterministic — no HTML link-chasing, no asyncio.

    All network actions are capped at 10 s.  Stops immediately when:
      - a page adds zero new product links, OR
      - the running total has not grown since the previous page (duplicate page guard).
    Hard cap: 50 listing pages.
    Runs synchronously; intended to be called from a dedicated thread.
    """
    base = 'https://www.myskinrecipes.com'
    MAX_PAGES   = 50
    NAV_TIMEOUT = 10_000  # ms
    JS_SETTLE   =    800  # ms — let lazy-loaded product cards render

    def _page_url(pg: int) -> str:
        if pg == 1:
            return category_url
        sep = '&' if '?' in category_url else '?'
        return f"{category_url}{sep}page={pg}"

    def _abs(href: str) -> str:
        return href if href.startswith('http') else base + href

    def _norm(url: str) -> str:
        return url.split('?')[0].split('#')[0].rstrip('/')

    seen_products: set = set()
    product_urls: List[str] = []
    prev_total = -1  # sentinel for duplicate-page guard

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        )

        for page_num in range(1, MAX_PAGES + 1):
            listing_url = _page_url(page_num)
            # Print BEFORE navigating so terminal shows exactly where a hang occurs
            print(f'[discover] Page {page_num} -> {listing_url}', flush=True)

            page = context.new_page()
            try:
                page.goto(listing_url, wait_until='domcontentloaded', timeout=NAV_TIMEOUT)
                page.wait_for_timeout(JS_SETTLE)
                html = page.content()
            except Exception as exc:
                print(
                    f'[discover] Page {page_num} load failed ({type(exc).__name__}) -- stopping',
                    flush=True,
                )
                page.close()
                break
            page.close()

            count_before = len(seen_products)

            for m in re.finditer(
                r'href=["\']([^"\']*?/\d+-[^"\']+?\.html)["\']',
                html, re.IGNORECASE,
            ):
                href = _abs(m.group(1))
                norm = _norm(href)
                if 'myskinrecipes.com' in norm and norm not in seen_products:
                    seen_products.add(norm)
                    product_urls.append(norm)

            new_on_page = len(seen_products) - count_before
            print(
                f'[discover] Page {page_num}: +{new_on_page} new items '
                f'(total {len(product_urls)})',
                flush=True,
            )

            # Guard 1: page yielded no new products -> end of catalogue
            if new_on_page == 0:
                print(f'[discover] Page {page_num}: no new items -- end of catalogue', flush=True)
                break

            # Guard 2: total unchanged vs previous page -> duplicate/loop detected
            current_total = len(product_urls)
            if current_total == prev_total:
                print(
                    f'[discover] Total unchanged ({current_total}) -- breaking to prevent loop',
                    flush=True,
                )
                break
            prev_total = current_total

        browser.close()

    print(f'[discover] Done -- {len(product_urls)} product URLs found', flush=True)
    return product_urls


class MySkinRecipesScraper(BaseScraper):
    def scrape(self, url: str) -> Dict[str, Any]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
            except Exception as e:
                browser.close()
                return {"raw_html": None, "parsed": [], "errors": [str(e)]}

            html = page.content()
            body_text = page.inner_text('body')

            parsed = []
            errors = []

            # Prefer HTML INCI block from product-technical-pdf when available
            m_pdf_quick = re.search(
                r"<div[^>]*id=\"product-technical-pdf\"[^>]*>([\s\S]*?)</div>",
                html, flags=re.IGNORECASE,
            )
            if m_pdf_quick:
                block_quick = m_pdf_quick.group(1)
                m_inci_quick = re.search(
                    r"<tr[^>]*class=\"field_inci\"[^>]*>[\s\S]*?<ul[^>]*>([\s\S]*?)</ul>",
                    block_quick, flags=re.IGNORECASE,
                )
                if m_inci_quick:
                    ul_html_q = m_inci_quick.group(1)
                    li_texts_q = re.findall(r"<li[^>]*>([\s\S]*?)</li>", ul_html_q, flags=re.IGNORECASE)
                    cleaned_q = [
                        re.sub(r"<[^>]+>", "", li).strip()
                        for li in li_texts_q
                        if re.sub(r"<[^>]+>", "", li).strip()
                    ]
                    if cleaned_q:
                        parsed = parse_ingredient_text('\n'.join(cleaned_q))
                        browser.close()
                        return {"raw_html": html, "parsed": parsed, "errors": errors}

            # Attempt 1: product id → AJAX INCI endpoint
            prod_id = None
            m = re.search(r"currentProductId\s*=\s*(\d+)", html)
            if not m:
                m = re.search(r"id_product\s*[:=]\s*(\d+)", html)
            if m:
                prod_id = m.group(1)

            if prod_id:
                try:
                    ajax_url = "https://www.myskinrecipes.com/shop/th/module/ajaxmodule/getInci?ajax=1"
                    with httpx.Client(timeout=20.0) as client:
                        r = client.post(ajax_url, data={"ajax": "1", "id_product": prod_id})
                        if r.status_code == 200:
                            j = r.json()
                            inci_data = None
                            if isinstance(j, dict):
                                if 'data' in j and isinstance(j['data'], list) and j['data']:
                                    for el in j['data']:
                                        if isinstance(el, dict) and 'inci_data' in el and el['inci_data']:
                                            inci_data = el['inci_data']
                                            break
                                elif 'inci_data' in j and j['inci_data']:
                                    inci_data = j['inci_data']

                            if inci_data:
                                raw_text = '\n'.join([
                                    item.get('name') or item.get('ingredient') or ''
                                    for item in inci_data if item
                                ])
                                parsed = parse_ingredient_text(raw_text)
                                browser.close()
                                return {"raw_html": html, "parsed": parsed, "errors": errors}
                except Exception as e:
                    errors.append(f'AJAX inci fetch failed: {e}')

            # Fallback 2: INCI block in rendered HTML
            m_pdf = re.search(
                r"<div[^>]*id=\"product-technical-pdf\"[^>]*>([\s\S]*?)</div>",
                html, flags=re.IGNORECASE,
            )
            if m_pdf:
                block = m_pdf.group(1)
                m_inci = re.search(
                    r"<tr[^>]*class=\"field_inci\"[^>]*>[\s\S]*?<ul[^>]*>([\s\S]*?)</ul>",
                    block, flags=re.IGNORECASE,
                )
                if m_inci:
                    ul_html = m_inci.group(1)
                    li_texts = re.findall(r"<li[^>]*>([\s\S]*?)</li>", ul_html, flags=re.IGNORECASE)
                    cleaned = [
                        re.sub(r"<[^>]+>", "", li).strip()
                        for li in li_texts
                        if re.sub(r"<[^>]+>", "", li).strip()
                    ]
                    if cleaned:
                        parsed = parse_ingredient_text('\n'.join(cleaned))
                        browser.close()
                        return {"raw_html": html, "parsed": parsed, "errors": errors}

            # Fallback heuristics
            text_candidates = []

            for pat in [
                r"Ingredients[:\s]*([\s\S]{1,400})",
                r"INCI[:\s]*([\s\S]{1,400})",
                r"ส่วนผสม[:\s]*([\s\S]{1,400})",
            ]:
                m = re.search(pat, html, flags=re.IGNORECASE)
                if m:
                    candidate = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                    if candidate:
                        text_candidates.append(candidate)

            if not text_candidates:
                lines = body_text.splitlines()
                for i, line in enumerate(lines):
                    if ('ingredient' in line.lower() or 'inci' in line.lower()
                            or 'ส่วนผสม' in line):
                        buf = [
                            lines[j].strip()
                            for j in range(i, min(i + 5, len(lines)))
                            if lines[j].strip()
                        ]
                        if buf:
                            text_candidates.append(' '.join(buf))
                            break

            if not text_candidates:
                m = re.search(r"([A-Za-z\s,\(\)\-]{50,})%", body_text)
                if m:
                    text_candidates.append(m.group(0))

            if text_candidates:
                parsed = parse_ingredient_text(text_candidates[0])
            else:
                errors.append('No ingredient block found')

            browser.close()
            return {"raw_html": html, "parsed": parsed, "errors": errors}
