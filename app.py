import os
import threading
from bot import main as bot_main
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram File Generator Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    bot_main()

if __name__ == "__main__":
    # বটকে আলাদা থ্রেডে চালান
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
