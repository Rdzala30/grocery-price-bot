from duckduckgo_search import DDGS
import re, time

def extract_price_from_text(text):
    """Pull out ₹ amounts from any text"""
    patterns = [
        r'₹\s*(\d+(?:\.\d+)?)',
        r'Rs\.?\s*(\d+(?:\.\d+)?)',
        r'INR\s*(\d+(?:\.\d+)?)',
        r'price[:\s]+₹?\s*(\d+(?:\.\d+)?)',
        r'for\s+₹\s*(\d+)',
        r'at\s+₹\s*(\d+)',
        r'(\d+)\s*(?:/-|rupees)',
    ]
    found = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        for m in matches:
            val = float(m)
            if 5 < val < 5000:  # filter out garbage like ₹1 or ₹99999
                found.append(val)
    if not found:
        return None
    found.sort()
    return f"₹{int(found[len(found)//2])}"  # return median price

def search_item_on_platform(item, platform):
    queries = [
        f'{item} price {platform} india',
        f'buy {item} online india ₹ {platform}',
    ]
    all_text = ""
    try:
        with DDGS() as ddgs:
            for query in queries:
                results = list(ddgs.text(query, max_results=5))
                for r in results:
                    all_text += r.get('title','') + " " + r.get('body','') + " "
                time.sleep(1)
    except Exception as e:
        return "Search error"

    price = extract_price_from_text(all_text)
    return price if price else "Not found"

def get_prices_for_item(item):
    platforms = ["Blinkit", "Zepto", "Swiggy Instamart", "BigBasket"]
    results = {}
    for platform in platforms:
        results[platform] = search_item_on_platform(item, platform)
        time.sleep(2)  # avoid DDG rate limiting
    return results

def build_price_context(grocery_list):
    context = ""
    for item in grocery_list:
        context += f"\n\nItem: {item}\n"
        prices = get_prices_for_item(item)
        for platform, price in prices.items():
            context += f"  {platform}: {price}\n"
    return context
