import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = "8696587166:AAEqiiMPkfV71cEH12mzyfjHWNvy44SFpqs"
ADMIN_ID = 7281188442

# ذخیره شناسه کاربرانی که لایک کرده‌اند
# format: { message_key: set(user_ids) }
votes = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! متن بنر یا اسم شرکت‌کننده رو بفرست تا بنر چالش با دکمه لایک برات ساخته بشه.")

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    text = f"🏆 **چالش لایکی**\n\n👤 شرکت‌کننده: **{name}**\n\n❤️ برای حمایت لایک کنید!"
    
    keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # کلید اختصاصی برای هر پست
    if query.inline_message_id:
        msg_key = query.inline_message_id
    else:
        msg_key = f"{query.message.chat_id}_{query.message.message_id}"

    if msg_key not in votes:
        votes[msg_key] = set()

    current_text = query.message.reply_markup.inline_keyboard[0][0].text
    current_likes = int(current_text.split()[0])

    if user_id in votes[msg_key]:
        # برداشتن لایک در صورت کلیک مجدد
        votes[msg_key].remove(user_id)
        new_likes = max(0, current_likes - 1)
        await query.answer("لایک شما برداشته شد!")
    else:
        # ثبت لایک جدید
        votes[msg_key].add(user_id)
        new_likes = current_likes + 1
        await query.answer("❤️ لایک شما ثبت شد!")

    keyboard = [[InlineKeyboardButton(f"{new_likes} ❤️", callback_data="like")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

async def add_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی ادمین ندارید.")
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
        await update.message.reply_text(f"✅ لایک پست {msg_id} در کانال {chat_id} به {count} تغییر یافت!")
    except Exception as e:
        await update.message.reply_text("فرمت صحیح:\n`/addlike آیدی_کانال شناسه_پست تعداد`\nمثال:\n`/addlike @EDI_MSNjs 105 50`", parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addlike", add_likes))
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))
    
    app.run_polling()
    
