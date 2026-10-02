import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, InlineQueryHandler, filters

# خواندن توکن از متغیرهای محیطی Railway
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7281188442

votes = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide_text = (
        "👋 **به ربات چالش و لایک خوش آمدید!**\n\n"
        "📖 **راهنمای استفاده از ربات:**\n\n"
        "1️⃣ **ارسال مستقیم اسم شرکت‌کننده:**\n"
        "کافیست در همین چت، اسم شرکت‌کننده را بفرستید تا بنر لایک‌‌دار برای شما ساخته شود.\n\n"
        "2️⃣ **استفاده در گروه و کانال (Inline Mode):**\n"
        "در هر چت، گروه یا کانالی عبارت زیر را تایپ کنید:\n"
        "`@Chahchahvarz_bot اسم_شرکت‌کننده`\n"
        "سپس کادر بازشده را لمس کنید تا چالش ارسال شود.\n"
        "*(نکته: فقط مدیران گروه/کانال امکان ایجاد چالش اینلاین را دارند.)*\n\n"
        "3️⃣ **افزایش لایک توسط ادمین:**\n"
        "ادمین ربات می‌تواند با دستور زیر تعداد لایک‌ها را تغییر دهد:\n"
        "`/addlike آیدی_کانال شناسه_پست تعداد`"
    )
    await update.message.reply_text(guide_text, parse_mode="Markdown")

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
    await update.message.reply_text(name, reply_markup=InlineKeyboardMarkup(keyboard))

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return

    user_id = update.inline_query.from_user.id
    chat_type = update.inline_query.chat_type

    if chat_type in ["group", "supergroup"]:
        try:
            chat_id = update.inline_query.chat.id if update.inline_query.chat else None
            if chat_id:
                member = await context.bot.get_chat_member(chat_id, user_id)
                if member.status not in ["administrator", "creator"]:
                    return
        except Exception:
            pass

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
    user_id = query.from_user.id
    
    inline_id = query.inline_message_id
    msg_key = inline_id if inline_id else f"{query.message.chat_id}_{query.message.message_id}"

    if msg_key not in votes:
        votes[msg_key] = set()

    try:
        button_text = query.message.reply_markup.inline_keyboard[0][0].text if query.message else "0 ❤️"
        current_likes = int(button_text.split()[0])
    except Exception:
        current_likes = 0

    if user_id in votes[msg_key]:
        votes[msg_key].remove(user_id)
        new_likes = max(0, current_likes - 1)
        await query.answer("لایک شما برداشته شد!")
    else:
        votes[msg_key].add(user_id)
        new_likes = current_likes + 1
        await query.answer("❤️ لایک شما ثبت شد!")

    keyboard = [[InlineKeyboardButton(f"{new_likes} ❤️", callback_data="like")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if inline_id:
            await context.bot.edit_message_reply_markup(
                inline_message_id=inline_id,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_reply_markup(reply_markup=reply_markup)
    except Exception as e:
        print(f"Error updating like: {e}")

async def add_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی ادمین ندارید.")
        return

    try:
        chat_id = context.args[0]
        msg_id = int(context.args[1])
        count = int(context.args[2])

        keyboard = [[InlineKeyboardButton(f"{count} ❤️️", callback_data="like")]]
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(f"✅ لایک پست به {count} تغییر یافت!")
    except Exception:
        await update.message.reply_text("فرمت ادمین:\n`/addlike آیدی_کانال شناسه_پست تعداد`", parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addlike", add_likes))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))
    
    app.run_polling()
            
