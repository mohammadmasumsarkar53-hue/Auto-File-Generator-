import os
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# States
FILENAME, COLLECT_CONTENT = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📁 **ফাইল জেনারেটর বট**\n"
        "একটি ফাইল তৈরি করতে /create কমান্ড দিন।\n\n"
        "বিশেষ সুবিধা: আপনি চাইলে অনেক বড় টেক্সট কয়েকটি মেসেজে ভাগ করে পাঠাতে পারেন।\n"
        "টেক্সট পাঠানো শেষ হলে `/done` লিখুন।"
    )

async def create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📄 ফাইলের নাম লিখুন (উদা: data.txt, mycode.py, index.html):")
    return FILENAME

async def get_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = update.message.text.strip()
    if ".." in filename or "/" in filename or "\\" in filename:
        await update.message.reply_text("❌ অবৈধ নাম। '..', '/', '\\' ব্যবহার করা যাবে না। আবার দিন:")
        return FILENAME
    
    context.user_data['filename'] = filename
    context.user_data['content_parts'] = []
    
    await update.message.reply_text(
        "✍️ এখন আপনার টেক্সট পাঠান। আপনি কয়েকটি মেসেজে ভাগ করেও পাঠাতে পারেন।\n"
        "সব পাঠানো শেষ হলে `/done` কমান্ড দিন।\n"
        "বাতিল করতে `/cancel` লিখুন।"
    )
    return COLLECT_CONTENT

async def collect_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['content_parts'].append(text)
    await update.message.reply_text("✅ টেক্সট অংশ জমা নিলাম। আরও পাঠাতে পারেন বা `/done` দিন।")
    return COLLECT_CONTENT

async def finish_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = context.user_data.get('filename')
    parts = context.user_data.get('content_parts', [])
    
    if not filename:
        await update.message.reply_text("ত্রুটি, আবার /create দিয়ে শুরু করুন।")
        return ConversationHandler.END
    
    if not parts:
        await update.message.reply_text("❌ কোনো টেক্সট পাওয়া যায়নি। ফাইল তৈরি করা সম্ভব নয়। /create দিন আবার।")
        return ConversationHandler.END
    
    full_content = "\n".join(parts)
    
    try:
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix=suffix) as tmp:
            tmp.write(full_content)
            tmp_path = tmp.name
        
        with open(tmp_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption=f"✅ ফাইল তৈরি হয়েছে: `{filename}`\nমোট অক্ষর: {len(full_content)}"
            )
        
        os.unlink(tmp_path)
        
    except Exception as e:
        await update.message.reply_text(f"❌ ব্যর্থ: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ বাতিল করা হয়েছে। /create দিয়ে নতুন করে শুরু করুন।")
    return ConversationHandler.END

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("No TELEGRAM_TOKEN found in environment variables")
    
    app = Application.builder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('create', create)],
        states={
            FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_filename)],
            COLLECT_CONTENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_content),
                CommandHandler('done', finish_file),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)
    
    print("Bot is polling...")
    app.run_polling()
