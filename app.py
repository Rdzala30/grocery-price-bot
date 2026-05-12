from flask import Flask, request
import threading
import traceback
import google.generativeai as genai
import requests
import os
from config import TELEGRAM_TOKEN, GEMINI_API_KEY
from searcher import build_price_context

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
# Using gemini-1.5-flash for broader availability and speed
model = genai.GenerativeModel("gemini-1.5-flash")

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

def process_and_reply(chat_id, items):
    """Background task to fetch prices and send analysis back to user."""
    try:
        analysis = compare_prices(items)
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
    
    # Check if response has text (Gemini sometimes blocks content)
    if response and response.text:
        return response.text
    else:
        return "⚠️ Gemini AI was unable to generate a comparison for these items. The search data might be unclear."

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
