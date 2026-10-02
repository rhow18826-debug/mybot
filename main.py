from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8696587166:AAEqiiMPkfV71cEH12mzyfjHWNvy44SFpqs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "لایک کن اگه برنده شدم 500 مگ میدم"
    keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like_count")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    current_text = query.message.reply_markup.inline_keyboard[0][0].text
    current_likes = int(current_text.split()[0])
    new_likes = current_likes + 1
    
    new_keyboard = [[InlineKeyboardButton(f"{new_likes} ❤️", callback_data="like_count")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()
    
