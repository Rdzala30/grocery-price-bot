from flask import Flask, request
import threading
import traceback
import requests
import os
from config import TELEGRAM_TOKEN, GROQ_API_KEY
from searcher import build_price_context
from groq import Groq

# Configure Groq
client = Groq(api_key=GROQ_API_KEY)

app = Flask(__name__)

def send_telegram_message(chat_id, text, parse_mode="Markdown"):
    """Sends a message back to the user via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def enrich_grocery_list(items):
    """Uses AI to convert generic items into popular brand-specific queries for better search results."""
    prompt = (
        "You are a grocery assistant in India. Rewrite the following list of generic grocery items "
        "into concise, popular brand names that would yield better search results on Indian grocery apps "
        "(like Blinkit or BigBasket). "
        "For example, 'Milk 1L' -> 'Amul Milk 1L', 'Salt' -> 'Tata Salt 1kg'. "
        "IMPORTANT: Keep names SHORT and concise (max 3-5 words). Avoid overly long descriptions. "
        "Return ONLY the rewritten list, one item per line, with no extra text or numbering.\n\n"
        "Original list:\n" + "\n".join(items)
    )
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        # Split by newline and clean up (removing bullets if AI added them)
        enriched_items = []
        for line in response.choices[0].message.content.split('\n'):
            cleaned = line.strip()
            if cleaned.startswith('-') or cleaned.startswith('*'):
                cleaned = cleaned[1:].strip()
            # Remove numbering like "1. "
            import re
            cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
            if cleaned:
                enriched_items.append(cleaned)
                
        # Fallback to original if AI fails or returns empty
        return enriched_items if enriched_items else items
    except Exception as e:
        print(f"Error enriching grocery list: {e}")
        return items

def process_and_reply(chat_id, items):
    """Background task to fetch prices and send analysis back to user."""
    try:
        send_telegram_message(chat_id, "✨ *Enhancing your list for better results...*")
        enriched_items = enrich_grocery_list(items)
        
        # Show user the enriched items if they changed
        if enriched_items != items:
            enriched_msg = "🔍 *Searching for specific brands:*\n" + "\n".join([f"• {i}" for i in enriched_items])
            send_telegram_message(chat_id, enriched_msg)
            
        analysis = compare_prices(enriched_items)
        send_telegram_message(chat_id, analysis)
    except Exception as e:
        # Send full traceback to Telegram as requested for debugging
        # Truncate to avoid exceeding Telegram's 4096 character limit
        error_trace = traceback.format_exc()[:4000]
        # Use parse_mode=None because tracebacks often contain characters that break Markdown
        send_telegram_message(chat_id, f"DEBUG ERROR:\n{error_trace}", parse_mode=None)

def compare_prices(grocery_list):
    """Gets search context and uses Gemini to compare prices."""
    # Get search results context
    context = build_price_context(grocery_list)
    
    # Prepare AI prompt
    prompt = f"""
You are a premium grocery comparison assistant for Indian users.

Analyze the grocery price data carefully.

RULES:
- Keep response visually clean and modern
- Use emojis properly
- NO markdown tables
- NO ### headings
- NO long paragraphs
- Keep spacing clean
- Use bullet formatting
- Mention only useful information
- If price is unavailable, write "Not Found"

FORMAT EXACTLY LIKE THIS:

🛒 Grocery Price Comparison

🥛 Milk 1L
• Blinkit: ₹68
• Zepto: ₹70
• Swiggy: ₹69
• BigBasket: ₹72
✅ Cheapest: Blinkit (₹68)

🧅 Onion 1kg
• Blinkit: ₹34
• Zepto: ₹35
• Swiggy: ₹30
• BigBasket: ₹106
✅ Cheapest: Swiggy (₹30)

━━━━━━━━━━━━━━

💰 Best Deals Summary
• Milk 1L → Blinkit
• Onion 1kg → Swiggy

━━━━━━━━━━━━━━

⚠️ Note:
Prices are estimated from public web results and may vary slightly in-app.

Here is the search data:

{context}
"""
    
    # Generate response using Groq
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    return response.choices[0].message.content

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    """Main webhook endpoint for Telegram updates."""
    update = request.get_json()
    
    if not update or "message" not in update:
        return "OK", 200
    
    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")
    
    if not text:
        return "OK", 200

    if text == "/start":
        msg = (
            "🛒 *Welcome to Grocery Price Bot!*\n\n"
            "Send me a list of grocery items (one per line) and I'll find the best prices "
            "across Blinkit, Zepto, Swiggy Instamart, and BigBasket in India.\n\n"
            "Example:\n`Milk 1L`\n`Eggs 12pcs`\n`Bread`"
        )
        send_telegram_message(chat_id, msg)
        
    elif text == "/help":
        msg = (
            "💡 *How to use:*\n"
            "1. Type your grocery list with each item on a new line.\n"
            "2. I will search multiple platforms for you.\n"
            "3. Groq AI will analyze the results and tell you where to buy!\n\n"
            "Currently searching: Blinkit, Zepto, Swiggy Instamart, BigBasket."
        )
        send_telegram_message(chat_id, msg)
        
    else:
        # Process the grocery list
        items = [i.strip() for i in text.split("\n") if i.strip()]
        
        if not items:
            send_telegram_message(chat_id, "⚠️ Please send a valid list of grocery items.")
            return "OK", 200
        
        # Notify user that search is starting
        send_telegram_message(chat_id, "🔍 *Searching prices across platforms...* This may take a minute.")
        
        # Start background thread to handle searching and AI analysis
        # This prevents Telegram from timing out and sending duplicate requests
        thread = threading.Thread(target=process_and_reply, args=(chat_id, items))
        thread.start()
        
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
