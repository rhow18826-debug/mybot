import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, InlineQueryHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7281188442

# --- راه اندازی و مدیریت دیتابیس ---
DB_NAME = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # جدول ذخیره تعداد کل لایک‌های هر پیام
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_likes (
            msg_key TEXT PRIMARY KEY,
            like_count INTEGER DEFAULT 0
        )
    ''')
    # جدول ذخیره وضعیت کلیک هر کاربر برای جلوگیری از لایک تکراری
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_votes (
            click_key TEXT PRIMARY KEY,
            has_liked INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_like_count(msg_key: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT like_count FROM post_likes WHERE msg_key = ?", (msg_key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def set_like_count(msg_key: str, count: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO post_likes (msg_key, like_count) VALUES (?, ?) ON CONFLICT(msg_key) DO UPDATE SET like_count = ?", (msg_key, count, count))
    conn.commit()
    conn.close()

def get_user_vote(click_key: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT has_liked FROM user_votes WHERE click_key = ?", (click_key,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row else False

def set_user_vote(click_key: str, status: bool):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    val = 1 if status else 0
    cursor.execute("INSERT INTO user_votes (click_key, has_liked) VALUES (?, ?) ON CONFLICT(click_key) DO UPDATE SET has_liked = ?", (click_key, val, val))
    conn.commit()
    conn.close()

# --- توابع ربات ---

async def is_user_member(context: ContextTypes.DEFAULT_TYPE, chat_id, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        print(f"Error checking membership: {e}")
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide_text = (
        "👋 به ربات چالش و لایک خوش آمدید!\n\n"
        "📖 راهنمای استفاده از ربات:\n\n"
        "1️⃣ ارسال مستقیم اسم شرکت‌کننده:\n"
        "کافیست در پیوی ربات، اسم شرکت‌‌کننده را بفرستید تا بنر لایکدار برای شما ساخته شود.\n\n"
        "2️⃣ استفاده در گروه و کانال (Inline Mode):\n"
        "در هر چت عبارت زیر را تایپ کنید:\n"
        "@Chahchahvarz_bot اسم_شرکت‌کننده\n"
        "(نکته: فقط مدیران امکان ایجاد چالش اینلاین را دارند.)"
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
    
    # بررسی عضویت در کانال
    if query.message and query.message.chat:
        chat_id = query.message.chat.id
        if not await is_user_member(context, chat_id, user_id):
            await query.answer("⚠️ برای ثبت لایک باید ابتدا عضو این کانال شوید!", show_alert=True)
            return

    inline_id = query.inline_message_id
    msg_key = inline_id if inline_id else f"{query.message.chat_id}_{query.message.message_id}"

    # خواندن مقدار لایک از دیتابیس
    current_likes = get_like_count(msg_key)

    # اگر در دیتابیس ثبت نشده بود، سعی می‌کنیم از متن روی دکمه بخوانیم
    if current_likes == 0 and query.message and query.message.reply_markup:
        try:
            button_text = query.message.reply_markup.inline_keyboard[0][0].text
            current_likes = int(button_text.split()[0])
        except Exception:
            current_likes = 0

    click_key = f"{msg_key}_{user_id}"
    has_liked = get_user_vote(click_key)

    if has_liked:
        new_likes = max(0, current_likes - 1)
        set_user_vote(click_key, False)
        await query.answer("لایک شما برداشته شد!")
    else:
        new_likes = current_likes + 1
        set_user_vote(click_key, True)
        await query.answer("❤️ لایک شما ثبت شد!")

    # ذخیره لایک جدید در دیتابیس
    set_like_count(msg_key, new_likes)

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
        return

    try:
        target = context.args[0]
        
        # حالت ۱: تغییر لایک پیام اینلاین (ارسال شناسه inline)
        if len(context.args) == 2 and not target.startswith("@") and not target.startswith("-"):
            inline_id = target
            count = int(context.args[1])
            
            set_like_count(inline_id, count)
            
            keyboard = [[InlineKeyboardButton(f"{count} ❤️", callback_data="like")]]
            await context.bot.edit_message_reply_markup(
                inline_message_id=inline_id,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await update.message.reply_text(f"✅ لایک پیام اینلاین به {count} تغییر یافت!")
            return

        # حالت ۲: تغییر لایک پیام عادی کانال (/addlike @channel_id msg_id count)
        chat_id = target
        msg_id = int(context.args[1])
        count = int(context.args[2])

        msg_key = f"{chat_id}_{msg_id}"
        set_like_count(msg_key, count)

        keyboard = [[InlineKeyboardButton(f"{count} ❤️", callback_data="like")]]
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(f"✅ لایک پست به {count} تغییر یافت!")
    except Exception as e:
        await update.message.reply_text("فرمت اشتباه است. نمونه دستورها:\n\n۱. کانال:\n/addlike @channel_id 123 150\n\n۲. اینلاین:\n/addlike INLINE_ID 150")

if __name__ == '__main__':
    # ایجاد یا اتصال به دیتابیس
    init_db()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addlike", add_likes))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_name))
    
    app.run_polling()
        
