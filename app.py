import os
import threading
from flask import Flask, request
import bot

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram File Bot is running on Railway!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    bot.main()

if __name__ == "__main__":
    # পোলিং বট আলাদা থ্রেডে চালান
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
