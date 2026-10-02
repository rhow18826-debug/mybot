import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7281188442

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 به ربات چالش خوش آمدید!\n\n"
        "اسم شرکت‌کننده رو ارسال کنید تا بنر ساخته بشه."
    )

# وقتی کاربر توی پیوی اسم می‌فرسته
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
    await update.message.reply_text(
        f"🏆 چالش: {name}\n\n"
        f"💡 برای ارسال این بنر به کانال، دستور زیر را به ربات بفرستید:\n"
        f"`/send @my_channel {name}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ارسال مستقیم بنر به کانال توسط هر کاربر یا ادمین
async def send_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        channel_id = context.args[0]
        name = " ".join(context.args[1:])
        
        keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
        sent_msg = await context.bot.send_message(
            chat_id=channel_id,
            text=f"🏆 چالش: {name}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(
            f"✅ بنر با موفقیت در کانال قرار گرفت!\n"
            f"🆔 آیدی پیام: `{sent_msg.message_id}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text("❌ خطا! فرمت درست:\n`/send @channel_id اسم_شرکت‌کننده`\n\n(مطمئن شوید ربات ادمین کانال است)", parse_mode="Markdown")

# کلیک روی دکمه لایک
async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.message and query.message.reply_markup:
        # خواندن مستقیم عدد از روی متن دکمه
        current_text = query.message.reply_markup.inline_keyboard[0][0].text
        numbers = re.findall(r'\d+', current_text)
        current_likes = int(numbers[0]) if numbers else 0
        
        new_likes = current_likes + 1
        keyboard = [[InlineKeyboardButton(f"{new_likes} ❤️", callback_data="like")]]
        
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer("❤️ لایک ثبت شد!")
    else:
        await query.answer("⚠️ این پیام اینلاین است و پشتیبانی نمی‌شود. پیام باید مستقیم از ربات پست شده باشد.", show_alert=True)

# تغییر تعداد لایک توسط ادمین اصلی
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
        await update.message.reply_text(f"✅ لایک پیام {msg_id} به {count} تغییر یافت!")
    except Exception:
        await update.message.reply_text("فرمت صحیح دستور:\n`/addlike @channel_id msg_id 150`", parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_post))
    app.add_handler(CommandHandler("addlike", add_likes))
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_name))
    
    app.run_polling()
        
