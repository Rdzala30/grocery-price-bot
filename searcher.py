import time
from ddgs import DDGS

def search_item_price(item_name, platform):
    """
    Searches DuckDuckGo for the price of a specific item on a given platform in India.
    Returns the top 3 result snippets joined as a string.
    """
    query = f"{item_name} price {platform} India"
    try:
        # Use DDGS context manager to search DuckDuckGo
        with DDGS() as ddgs:
            # Fetch top 3 results
            results = ddgs.text(query, max_results=3)
            snippets = [r['body'] for r in results if 'body' in r]
            
            # Add sleep to avoid rate limiting as requested.
            # Note: Some items may return "No data found" if DuckDuckGo throttles rapid requests.
            time.sleep(1)
            
            return " ".join(snippets)
    except Exception as e:
        # Return empty string on failure as requested
        print(f"Search failed for {platform}: {e}")
        return ""

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
