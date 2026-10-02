import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = "8696587166:AAEqiiMPkfV71cEH12mzyfjHWNvy44SFpqs"
ADMIN_ID = 7281188442
CHANNEL_USERNAME = "@EDI_MSNjs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! اسم شرکت‌کننده یا متن بنر رو بفرست تا بنر چالش ساخته و به کانال ارسال بشه.")

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    text = f"🏆 **چالش لایکی**\n\n👤 شرکت‌کننده: **{name}**\n\n❤️ برای حمایت لایک کنید!"
    
    keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = await context.bot.send_message(
        chat_id=CHANNEL_USERNAME, 
        text=text, 
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(f"✅ بنر {name} با موفقیت در کانال ساخته شد!\nشناسه پست: `{msg.message_id}`", parse_mode="Markdown")

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    current_text = query.message.reply_markup.inline_keyboard[0][0].text
    likes = int(current_text.split()[0]) + 1
        
    await query.answer("لایک شما ثبت شد!")
    
    keyboard = [[InlineKeyboardButton(f"{likes} ❤️", callback_data="like")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

async def add_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی ادمین برای افزایش دستی لایک را ندارید.")
        return

    try:
        msg_id = int(context.args[0])
        count_to_add = int(context.args[1])

        msg = await context.bot.get_message(chat_id=CHANNEL_USERNAME, message_id=msg_id)
        current_text = msg.reply_markup.inline_keyboard[0][0].text
        current_likes = int(current_text.split()[0])
        new_likes = current_likes + count_to_add

        keyboard = [[InlineKeyboardButton(f"{new_likes} ❤️", callback_data="like")]]
        await context.bot.edit_message_reply_markup(
            chat_id=CHANNEL_USERNAME,
            message_id=msg_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(f"✅ تعداد {count_to_add} لایک اضافه شد! مجموع لایک‌ها: {new_likes}")
    except Exception as e:
        await update.message.reply_text("راهنما استفاده ادمین:\n`/addlike شناسه_پست تعداد`\nمثال:\n`/addlike 105 50`", parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addlike", add_likes))
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))
    
    app.run_polling()
    
