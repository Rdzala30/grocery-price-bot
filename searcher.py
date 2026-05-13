from duckduckgo_search import DDGS
import re, time

def extract_price_from_text(text):
    """Refined regex to catch common Indian price formats in snippets"""
    patterns = [
        r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'Rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'(?:Price|MRP|Offer Price|Selling Price)[:\s]+(?:₹|Rs\.?)\s*(\d+)',
        r'(\d+)\s*(?:/-|rupees)',
    ]
    found = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        for m in matches:
            # Remove commas and convert to float
            val_str = m.replace(',', '')
            try:
                val = float(val_str)
                if 10 < val < 5000: # Filter outliers
                    found.append(val)
            except ValueError:
                continue
    
    if not found: return None
    # Return the lowest price found (usually the discounted price)
    return f"₹{int(min(found))}"

def get_prices_for_item(item):
    """
    Consolidated search: one query for all platforms to avoid rate limits.
    """
    platforms = ["Blinkit", "Zepto", "Swiggy", "BigBasket"]
    results = {p: "Not found" for p in platforms}
    
    # We combine platforms into a single search to get one set of snippets
    # that likely contains results for all of them.
    query = f"{item} price Blinkit Zepto Swiggy BigBasket India"
    
    try:
        with DDGS() as ddgs:
            # Get more results to increase the chance of hitting all platforms
            search_results = list(ddgs.text(query, max_results=10))
            
            for p in platforms:
                p_text = ""
                # Look for snippets mentioning this platform
                for r in search_results:
                    title = r.get('title', '').lower()
                    body = r.get('body', '').lower()
                    if p.lower() in title or p.lower() in body:
                        p_text += f"{r.get('title','')} {r.get('body','')} "
                
                if p_text:
                    price = extract_price_from_text(p_text)
                    if price:
                        results[p] = price
            
            # Rate limit protection between items
            time.sleep(2)
            
    except Exception as e:
        print(f"Search failed for {item}: {e}")
        
    return results

def build_price_context(grocery_list):
    context = ""
    for item in grocery_list:
        context += f"\nItem: {item}\n"
        prices = get_prices_for_item(item)
        for platform, price in prices.items():
            # Standardize Swiggy name for the AI
            display_name = "Swiggy Instamart" if platform == "Swiggy" else platform
            context += f"  - {display_name}: {price}\n"
    return context
