import os
import asyncio
import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7281188442
DB_NAME = "wheels.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wheels (
            wheel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            participants TEXT,
            forced_winner TEXT DEFAULT NULL,
            photo_id TEXT DEFAULT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def create_wheel(title: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO wheels (title, participants) VALUES (?, ?)", (title, ""))
    wheel_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return wheel_id

def add_participant(wheel_id: int, name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT participants FROM wheels WHERE wheel_id = ?", (wheel_id,))
    row = cursor.fetchone()
    if row:
        current = row[0].split(",") if row[0] else []
        if name not in current:
            current.append(name)
            updated = ",".join(current)
            cursor.execute("UPDATE wheels SET participants = ? WHERE wheel_id = ?", (updated, wheel_id))
            conn.commit()
    conn.close()

def set_forced_winner(wheel_id: int, name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE wheels SET forced_winner = ? WHERE wheel_id = ?", (name, wheel_id))
    conn.commit()
    conn.close()

def set_wheel_photo(wheel_id: int, photo_id: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE wheels SET photo_id = ? WHERE wheel_id = ?", (photo_id, wheel_id))
    conn.commit()
    conn.close()

def get_wheel_data(wheel_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT title, participants, forced_winner, photo_id FROM wheels WHERE wheel_id = ?", (wheel_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        parts = row[1].split(",") if row[1] else []
        return {
            "title": row[0],
            "participants": parts,
            "forced_winner": row[2],
            "photo_id": row[3]
        }
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    guide = (
        "🎰 **راهنمای ربات گردونه:**\n\n"
        "1️⃣ `/newwheel عنوان`\n"
        "2️⃣ `/add <wheel_id> نام`\n"
        "3️⃣ `/setphoto <wheel_id>` (روی کاپشن عکس)\n"
        "4️⃣ `/setwinner <wheel_id> نام_برنده`\n"
        "5️⃣ `/sendwheel @channel_id <wheel_id>`"
    )
    await update.message.reply_text(guide, parse_mode="Markdown")

async def cmd_new_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("❌ `/newwheel عنوان`", parse_mode="Markdown")
        return
    title = " ".join(context.args)
    wheel_id = create_wheel(title)
    await update.message.reply_text(f"✅ گردونه با آیدی `{wheel_id}` ساخته شد.", parse_mode="Markdown")

async def cmd_add_participant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ `/add <wheel_id> نام`", parse_mode="Markdown")
        return
    try:
        wheel_id = int(context.args[0])
        name = " ".join(context.args[1:])
        data = get_wheel_data(wheel_id)
        if not data:
            await update.message.reply_text("❌ پیدا نشد.")
            return
        add_participant(wheel_id, name)
        await update.message.reply_text(f"✅ **{name}** اضافه شد.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ آیدی عدد باشد.")

async def cmd_set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    message = update.message
    if not message.photo or not context.args:
        await message.reply_text("❌ دستور `/setphoto <wheel_id>` را روی عکس بفرستید.", parse_mode="Markdown")
        return
    try:
        wheel_id = int(context.args[0])
        if not get_wheel_data(wheel_id):
            await message.reply_text("❌ پیدا نشد.")
            return
        photo_id = message.photo[-1].file_id
        set_wheel_photo(wheel_id, photo_id)
        await message.reply_text(f"✅ عکس گردونه `{wheel_id}` ثبت شد.", parse_mode="Markdown")
    except ValueError:
        await message.reply_text("❌ آیدی عدد باشد.")

async def cmd_set_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ `/setwinner <wheel_id> نام`", parse_mode="Markdown")
        return
    try:
        wheel_id = int(context.args[0])
        winner_name = " ".join(context.args[1:])
        data = get_wheel_data(wheel_id)
        if not data or winner_name not in data["participants"]:
            await update.message.reply_text("❌ یافت نشد یا کاربر در لیست نیست.")
            return
        set_forced_winner(wheel_id, winner_name)
        await update.message.reply_text(f"🤫 برنده به **{winner_name}** تغییر کرد.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ آیدی عدد باشد.")

async def cmd_send_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ `/sendwheel @channel_id <wheel_id>`", parse_mode="Markdown")
        return
    target_chat = context.args[0]
    try:
        wheel_id = int(context.args[1])
        data = get_wheel_data(wheel_id)
        if not data or not data["participants"]:
            await update.message.reply_text("❌ گردونه خالی است یا وجود ندارد.")
            return
        participants_str = "\n".join([f"▫️ {p}" for p in data["participants"]])
        text = f"🎰 **{data['title']}**\n\n👥 **شرکت‌کنندگان:**\n{participants_str}"
        keyboard = [[InlineKeyboardButton("🎰 چرخاندن گردونه", callback_data=f"spin_{wheel_id}")]]
        if data["photo_id"]:
            await context.bot.send_photo(chat_id=target_chat, photo=data["photo_id"], caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await context.bot.send_message(chat_id=target_chat, text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        await update.message.reply_text("✅ ارسال شد.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def handle_spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    wheel_id = int(query.data.split("_")[1])
    data = get_wheel_data(wheel_id)
    if not data or not data["participants"]:
        return
    participants = data["participants"]
    final_winner = data["forced_winner"] if (data["forced_winner"] and data["forced_winner"] in participants) else random.choice(participants)
    
    for _ in range(2):
        for name in participants:
            kb = [[InlineKeyboardButton(f"🔄 در حال چرخش... 👈 {name}", callback_data="none")]]
            try:
                if query.message.photo:
                    await query.edit_message_caption(caption=f"🎰 **{data['title']}**\n\n🔄 در حال چرخش...", reply_markup=InlineKeyboardMarkup(kb))
                else:
                    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
                await asyncio.sleep(0.4)
            except Exception:
                pass

    final_kb = [
        [InlineKeyboardButton(f"🏆 برنده: {final_winner} 🎉", callback_data="none")],
        [InlineKeyboardButton("🎰 چرخاندن مجدد", callback_data=f"spin_{wheel_id}")]
    ]
    participants_str = "\n".join([f"▫️ {p}" for p in participants])
    final_text = f"🎰 **{data['title']}**\n\n👥 **شرکت‌کنندگان:**\n{participants_str}\n\n🏆 **برنده:** **{final_winner}**"

    if query.message.photo:
        await query.edit_message_caption(caption=final_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(final_kb))
    else:
        await query.edit_message_text(text=final_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(final_kb))

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newwheel", cmd_new_wheel))
    app.add_handler(CommandHandler("add", cmd_add_participant))
    app.add_handler(CommandHandler("setwinner", cmd_set_winner))
    app.add_handler(CommandHandler("sendwheel", cmd_send_wheel))
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r"^/setphoto"), cmd_set_photo))
    app.add_handler(CallbackQueryHandler(handle_spin, pattern="^spin_"))
    app.run_polling()
        
