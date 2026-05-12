# Grocery Price Bot 🛒

A Telegram bot that checks grocery prices across Blinkit, Zepto, Swiggy Instamart, and Amazon Fresh using DuckDuckGo search and Gemini AI.

## Setup
1. Clone the repository.
2. Create a `.env` file based on `.env.example` and add your API keys.
3. Install dependencies: `pip install -r requirements.txt`.
4. Install playwright: `playwright install chromium`.

## Usage
- Run `python main.py` to start the Flask server.
- Set up a Telegram webhook to your server URL.
- Send a list of grocery items to the bot.

> **Note:** Some items may return "No data found" during searches, which often happens if DuckDuckGo throttles rapid requests. The 1-second sleep in the code helps mitigate this.