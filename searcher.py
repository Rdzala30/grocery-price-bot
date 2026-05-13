import time
import re
from ddgs import DDGS

def search_item_price(item_name, platform):
    """
    Searches DuckDuckGo for the price of a specific item on a given platform in India.
    Returns the combined snippets and extracted prices.
    """
    query = f"{item_name} price {platform} India"
    
    all_snippets = []
    
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=3)
            for r in results:
                if 'body' in r:
                    all_snippets.append(r['body'])
            time.sleep(1) # sleep to avoid rate limiting
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
        
    # Truncate combined_text here, THEN append extracted_info
    # so the regex extracted prices are never cut off
    truncated_text = combined_text[:250]
    return truncated_text + extracted_info

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
            # Truncation is now handled inside search_item_price to preserve extracted prices
            snippet = data if data else "No data found."
            full_context.append(f"[{platform}]: {snippet}")
        
        full_context.append("-" * 20) # Separator between items
        
    return "\n".join(full_context)
