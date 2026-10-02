import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = "8696587166:AAEqiiMPkfV71cEH12mzyfjHWNvy44SFpqs"
ADMIN_ID = 7281188442
CHANNEL_USERNAME = "@EDI_MSNjs"

contestants = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! اسم شرکت‌کننده رو بفرست تا بنر چالش ساخته و به کانال ارسال بشه.")

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی به ساخت چالش ندارید.")
        return

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
    
    contestants[msg.message_id] = {"name": name, "likes": 0}
    await update.message.reply_text(f"✅ بنر {name} با موفقیت در کانال ساخته شد!\nشناسه پست: `{msg.message_id}`", parse_mode="Markdown")

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    msg_id = query.message.message_id
    
    if msg_id not in contestants:
        current_text = query.message.reply_markup.inline_keyboard[0][0].text
        likes = int(current_text.split()[0]) + 1
        name = "شرکت‌کننده"
    else:
        contestants[msg_id]["likes"] += 1
        likes = contestants[msg_id]["likes"]
        name = contestants[msg_id]["name"]
        
    await query.answer("لایک شما ثبت شد!")
    
    keyboard = [[InlineKeyboardButton(f"{likes} ❤️", callback_data="like")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

async def add_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        msg_id = int(context.args[0])
        count_to_add = int(context.args[1])

        if msg_id in contestants:
            contestants[msg_id]["likes"] += count_to_add
            new_likes = contestants[msg_id]["likes"]
        else:
            new_likes = count_to_add

        keyboard = [[InlineKeyboardButton(f"{new_likes} ❤️", callback_data="like")]]
        await context.bot.edit_message_reply_markup(
            chat_id=CHANNEL_USERNAME,
            message_id=msg_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(f"✅ تعداد {count_to_add} لایک به پست اضافه شد! مجموع لایک‌ها: {new_likes}")
    except Exception as e:
        await update.message.reply_text("راهنما: دستور را به این شکل بفرستید:\n`/addlike شناسه_پست تعداد`\nمثال:\n`/addlike 105 50`", parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addlike", add_likes))
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))
    
    app.run_polling()
        
