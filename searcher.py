from duckduckgo_search import DDGS
import re, time

def extract_price_from_text(text):
    """Refined regex to catch common Indian price formats in snippets"""
    patterns = [
        r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'(?:Price|MRP|Offer Price)[:\s]+(?:₹|Rs\.?)\s*(\d+)',
    ]
    found = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        for m in matches:
            # Remove commas and convert to float
            val = float(m.replace(',', ''))
            if 10 < val < 5000: # Filter outliers
                found.append(val)
    
    if not found: return None
    # Return the lowest price found (usually the discounted price)
    return f"₹{int(min(found))}"

def search_item_on_platform(item, platform):
    site_map = {
        "Blinkit": "blinkit.com",
        "Zepto": "zeptonow.com",
        "Swiggy Instamart": "swiggy.com/instamart",
        "BigBasket": "bigbasket.com"
    }
    
    domain = site_map.get(platform, "")
    # The 'site:' operator is the key to 99% accuracy
    query = f"site:{domain} {item}" if domain else f"{item} price {platform} India"
    
    all_text = ""
    try:
        with DDGS() as ddgs:
            # Just 1 targeted search is enough and faster
            results = list(ddgs.text(query, max_results=3))
            for r in results:
                all_text += f"{r.get('title','')} {r.get('body','')} "
    except Exception:
        return "Search error"

    price = extract_price_from_text(all_text)
    return price if price else "Not found"

def get_prices_for_item(item):
    platforms = ["Blinkit", "Zepto", "Swiggy Instamart", "BigBasket"]
    results = {}
    for platform in platforms:
        results[platform] = search_item_on_platform(item, platform)
        time.sleep(1.5) # Reduced sleep since we do fewer queries
    return results

def build_price_context(grocery_list):
    context = ""
    for item in grocery_list:
        context += f"\nItem: {item}\n"
        prices = get_prices_for_item(item)
        for platform, price in prices.items():
            context += f"  - {platform}: {price}\n"
    return context
