import time
import re
from ddgs import DDGS

def search_item_price(item_name, platform):
    """
    Searches DuckDuckGo for the price of a specific item on a given platform in India.
    Runs multiple query variations to maximize useful snippets.
    Returns the combined snippets and extracted prices.
    """
    queries = [
        f"{item_name} {platform} price India",
        f"{item_name} {platform} today",
        f"{item_name} {platform} app"
    ]
    
    all_snippets = []
    
    try:
        with DDGS() as ddgs:
            for query in queries:
                try:
                    results = ddgs.text(query, max_results=2)
                    for r in results:
                        if 'body' in r and r['body'] not in all_snippets:
                            all_snippets.append(r['body'])
                    time.sleep(1) # sleep between variations
                except Exception as e:
                    print(f"Query '{query}' failed: {e}")
    except Exception as e:
        print(f"Search failed for {platform}: {e}")
        
    combined_text = " ".join(all_snippets)
    
    # Extract prices using regex
    # Matches: ₹34, Rs 45, ₹120.50, Rs. 100, etc.
    prices = re.findall(r'(?:₹|Rs\.?\s*)\s?\d+(?:,\d+)*(?:\.\d{1,2})?', combined_text, re.IGNORECASE)
    # Deduplicate while preserving order
    unique_prices = list(dict.fromkeys(prices))
    
    if unique_prices:
        extracted_info = f" [EXTRACTED PRICES: {', '.join(unique_prices)}]"
    else:
        extracted_info = ""
        
    return combined_text + extracted_info

def get_prices_for_item(item_name):
    """
    Searches across Blinkit, Zepto, Swiggy Instamart, and Amazon Fresh for an item.
    Returns a dictionary of search result snippets for each platform.
    """
    platforms = ["Blinkit", "Zepto", "Swiggy Instamart", "Amazon Fresh"]
    platform_data = {}
    
    for platform in platforms:
        platform_data[platform] = search_item_price(item_name, platform)
        
    return platform_data

def build_price_context(grocery_list):
    """
    Builds a large formatted string containing search context for all grocery items.
    Each platform result is truncated to 250 characters for brevity.
    """
    full_context = []
    
    for item in grocery_list:
        full_context.append(f"### SEARCH RESULTS FOR: {item}")
        prices = get_prices_for_item(item)
        
        for platform, data in prices.items():
            # Truncate to 250 characters as requested
            snippet = data[:250] if data else "No data found."
            full_context.append(f"[{platform}]: {snippet}")
        
        full_context.append("-" * 20) # Separator between items
        
    return "\n".join(full_context)
