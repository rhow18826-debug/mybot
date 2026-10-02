import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7281188442

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 به ربات چالش خوش آمدید!\n\n"
        "اسم شرکت‌کننده رو بفرست تا بنر لایک‌دار برات بسازم."
    )

# ساخت بنر در پیوی ربات
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
    await update.message.reply_text(f"🏆 چالش: {name}", reply_markup=InlineKeyboardMarkup(keyboard))

# مدیریت کلیک روی دکمه لایک
async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # اگر پیام معمولی باشه (نه اینلاین)
    if query.message and query.message.reply_markup:
        current_text = query.message.reply_markup.inline_keyboard[0][0].text
        numbers = re.findall(r'\d+', current_text)
        current_likes = int(numbers[0]) if numbers else 0
        
        new_likes = current_likes + 1
        keyboard = [[InlineKeyboardButton(f"{new_likes} ❤️", callback_data="like")]]
        
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer("❤️ لایک ثبت شد!")
    else:
        # اگر پیام اینلاین باشه تلگرام متن دکمه رو نمیده
        await query.answer("⚠️ لطفاً پست را مستقیم از ربات به کانال فوروارد کنید.", show_alert=True)

# دستور تغییر تعداد لایک توسط ادمین
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
        await update.message.reply_text("روش استفاده:\n/addlike @channel_id msg_id 150")

if __name__ == '__main__':
    
