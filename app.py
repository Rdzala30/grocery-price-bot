from flask import Flask, request
import threading
import google.generativeai as genai
import requests
import os
from config import TELEGRAM_TOKEN, GEMINI_API_KEY
from searcher import build_price_context

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

app = Flask(__name__)

def send_telegram_message(chat_id, text):
    """Sends a message back to the user via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def process_and_reply(chat_id, items):
    """Background task to fetch prices and send analysis back to user."""
    analysis = compare_prices(items)
    send_telegram_message(chat_id, analysis)

def compare_prices(grocery_list):
    """Gets search context and uses Gemini to compare prices."""
    try:
        # Get search results context
        context = build_price_context(grocery_list)
        
        # Prepare AI prompt
        prompt = (
            "You are a smart grocery shopping assistant for Indian users. "
            "Based on these web search results, for each grocery item tell me: "
            "(1) estimated price on each platform, (2) which platform is cheapest. "
            "End with a final summary table showing the cheapest option for each item. "
            "Use ₹ symbol. Format the response cleanly with emojis for readability. "
            "If price data is unclear, say 'Price unclear' rather than guessing.\n\n"
            f"SEARCH CONTEXT:\n{context}"
        )
        
        # Generate response using Gemini
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Price comparison logic failed: {e}")
        return "❌ Sorry, I encountered an error while comparing prices. Please try again later."

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
            "across Blinkit, Zepto, Swiggy Instamart, and Amazon Fresh in India.\n\n"
            "Example:\n`Milk 1L`\n`Eggs 12pcs`\n`Bread`"
        )
        send_telegram_message(chat_id, msg)
        
    elif text == "/help":
        msg = (
            "💡 *How to use:*\n"
            "1. Type your grocery list with each item on a new line.\n"
            "2. I will search multiple platforms for you.\n"
            "3. Gemini AI will analyze the results and tell you where to buy!\n\n"
            "Currently searching: Blinkit, Zepto, Swiggy Instamart, Amazon Fresh."
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
        
        # Start background thread to handle searching and Gemini analysis
        # This prevents Telegram from timing out and sending duplicate requests
        thread = threading.Thread(target=process_and_reply, args=(chat_id, items))
        thread.start()
        
    return "OK", 200

if __name__ == "__main__":
    # Standard Flask runner for local testing
    app.run(port=5000, debug=True)
