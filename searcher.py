from playwright.sync_api import sync_playwright
import time, re

def scrape_bigbasket(item):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set Indian headers to avoid blocks
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-IN,en;q=0.9"
            })
            
            search_url = f"https://www.bigbasket.com/ps/?q={item.replace(' ', '+')}"
            page.goto(search_url, timeout=15000)
            page.wait_for_timeout(3000)
            
            # Extract product names and prices
            results = []
            products = page.query_selector_all("li.PaginateItems___StyledLi")
            
            for product in products[:3]:  # top 3 results
                try:
                    name_el = product.query_selector("h3")
                    price_el = product.query_selector("span.Pricing___StyledLabel")
                    if name_el and price_el:
                        name = name_el.inner_text().strip()
                        price = price_el.inner_text().strip()
                        results.append(f"{name}: {price}")
                except:
                    continue
            
            browser.close()
            return "\n".join(results) if results else "Not found"
    except Exception as e:
        return f"Search error: {str(e)}"

def scrape_jiomart(item):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            search_url = f"https://www.jiomart.com/search/{item.replace(' ', '%20')}"
            page.goto(search_url, timeout=15000)
            page.wait_for_timeout(3000)
            
            results = []
            products = page.query_selector_all("div.plp-card-details-name")
            prices = page.query_selector_all("span.jm-heading-xxs")
            
            for i in range(min(3, len(products), len(prices))):
                try:
                    name = products[i].inner_text().strip()
                    price = prices[i].inner_text().strip()
                    results.append(f"{name}: {price}")
                except:
                    continue
            
            browser.close()
            return "\n".join(results) if results else "Not found"
    except Exception as e:
        return f"Search error: {str(e)}"

def get_prices_for_item(item):
    return {
        "BigBasket": scrape_bigbasket(item),
        "JioMart": scrape_jiomart(item),
    }

def build_price_context(grocery_list):
    context = ""
    for item in grocery_list:
        context += f"\n\nItem: {item}\n"
        prices = get_prices_for_item(item)
        for platform, data in prices.items():
            context += f"{platform}:\n{data}\n"
        time.sleep(1)
    return context
