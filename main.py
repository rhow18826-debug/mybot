import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, InlineQueryHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7281188442

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide_text = (
        "👋 به ربات چالش و لایک خوش آمدید!\n\n"
        "📖 راهنمای استفاده:\n"
        "1️⃣ ارسال اسم در پیوی ربات برای ساخت بنر لایک‌دار\n"
        "2️⃣ استفاده به صورت اینلاین در گروه و کانال:\n"
        "@Chahchahvarz_bot اسم_شرکت‌کننده"
    )
    await update.message.reply_text(guide_text)

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
    await update.message.reply_text(name, reply_markup=InlineKeyboardMarkup(keyboard))

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return

    keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
    results = [
        InlineQueryResultArticle(
            id="1",
            title=f"ایجاد چالش برای: {query}",
            input_message_content=InputTextMessageContent(query),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    ]
    await update.inline_query.answer(results, cache_time=0)

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # استخراج متن فعلی روی دکمه (مثلا "150 ❤️")
    current_text = "0"
    if query.message and query.message.reply_markup:
        current_text = query.message.reply_markup.inline_keyboard[0][0].text
    elif query.inline_message_id:
        # در حالت اینلاین از reply_markup استفاده می‌کنیم
        try:
            current_text = query.message.reply_markup.inline_keyboard[0][0].text if query.message else "0"
        except Exception:
            current_text = "0"

    # پیدا کردن اولین عدد موجود در متن دکمه با الگوی منظم
    numbers = re.findall(r'\d+', current_text)
    current_likes = int(numbers[0]) if numbers else 0

    # اضافه کردن ۱ واحد به عدد فعلی
    new_likes = current_likes + 1
    await query.answer("❤️ لایک شما ثبت شد!")

    keyboard = [[InlineKeyboardButton(f"{new_likes} ❤️", callback_data="like")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if query.inline_message_id:
            await context.bot.edit_message_reply_markup(
                inline_message_id=query.inline_message_id,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_reply_markup(reply_markup=reply_markup)
    except Exception as e:
        print(f"Error: {e}")

async def add_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        chat_id = context.args[0]
        msg_id = int(context.args[1])
        count = int(context.args[2])

        keyboard = [[InlineKeyboardButton(f"{count} ❤️", callback_data="like")]]
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(f"✅ لایک پست به {count} تغییر یافت!")
    except Exception:
        await update.message.reply_text("فرمت دستور:\n/addlike @channel_id msg_id 150")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addlike", add_likes))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_name))
    
    app.run_polling()
    
