import os
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

FILENAME, COLLECT_CONTENT = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📁 ফাইল জেনারেটর বট\n/create দিয়ে ফাইল তৈরি শুরু করুন\n"
        "বড় টেক্সট একাধিক মেসেজে পাঠিয়ে /done দিন"
    )

async def create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ফাইলের নাম লিখুন (যেমন: data.txt, script.py):")
    return FILENAME

async def get_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = update.message.text.strip()
    if ".." in filename or "/" in filename or "\\" in filename:
        await update.message.reply_text("❌ অবৈধ নাম। আবার দিন:")
        return FILENAME
    context.user_data['filename'] = filename
    context.user_data['content_parts'] = []
    await update.message.reply_text("✍️ টেক্সট পাঠান। শেষে /done দিন।\nবাতিলে /cancel")
    return COLLECT_CONTENT

async def collect_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['content_parts'].append(update.message.text)
    await update.message.reply_text("✅ অংশ জমা নিলাম। আরও পাঠান বা /done দিন")
    return COLLECT_CONTENT

async def finish_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = context.user_data.get('filename')
    parts = context.user_data.get('content_parts', [])
    if not filename or not parts:
        await update.message.reply_text("ত্রুটি, /create দিয়ে শুরু করুন")
        return ConversationHandler.END
    
    full_content = "\n".join(parts)
    try:
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix=suffix) as tmp:
            tmp.write(full_content)
            tmp_path = tmp.name
        with open(tmp_path, 'rb') as f:
            await update.message.reply_document(document=f, filename=filename, caption=f"✅ {filename}\nঅক্ষর: {len(full_content)}")
        os.unlink(tmp_path)
    except Exception as e:
        await update.message.reply_text(f"❌ ব্যর্থ: {e}")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ বাতিল। /create দিয়ে শুরু করুন")
    return ConversationHandler.END

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN environment variable not set")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("create", create)],
        states={
            FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_filename)],
            COLLECT_CONTENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_content),
                CommandHandler("done", finish_file),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    print("🤖 বট চালু হয়েছে (পোলিং মোড)")
    app.run_polling()

if __name__ == "__main__":
    main()
