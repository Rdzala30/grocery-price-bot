import sys
from searcher import build_price_context

# Ensure the terminal handles UTF-8 (for symbols like ₹)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("Starting Search Test...")
    sample_items = ["milk 1 litre", "onion 1kg", "bread"]
    
    print(f"Searching for: {', '.join(sample_items)}")
    print("This will take a moment due to rate-limit protection (1s sleep per search)...\n")
    
    context = build_price_context(sample_items)
    
    print("Search Results Context:")
    print("="*50)
    print(context)
    print("="*50)
    print("\nTest completed!")

if __name__ == "__main__":
    main()
