import nest_asyncio
nest_asyncio.apply()

import logging
import random
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

ADMIN_ID = 8259873270

API_ID = 6
API_HASH = "eb066357cf21a11da7348b2d8e28056a"
BOT_TOKEN = "8762543964:AAHATawlvvXSSe_AmVYmdhSn4m5OKo9GO3A"

user_balances = {}
user_self_sessions = {}
user_states = {}
last_wheel_spin = {}

FONTS_HOUR = {
    '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
    '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
}

def to_fa_num(num_str):
    return "".join(FONTS_HOUR.get(c, c) for c in num_str)

def get_balance(user_id: int) -> int:
    if user_id not in user_balances:
        if user_id == ADMIN_ID:
            user_balances[user_id] = 1000000
        else:
            user_balances[user_id] = 100
    return user_balances[user_id]

app = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ پنل سلف‌بات", callback_data="panel_self")],
        [InlineKeyboardButton("💳 شارژ حساب", callback_data="buy_diamond"), InlineKeyboardButton("🎒 موجودی", callback_data="check_balance")],
        [InlineKeyboardButton("🎡 چرخ شانس", callback_data="lucky_wheel")],
        [InlineKeyboardButton("👥 زیرمجموعه‌گیری", callback_data="referral"), InlineKeyboardButton("👤 حساب کاربری", callback_data="user_account")],
        [InlineKeyboardButton("📣 چنل", url="https://t.me/EDI_MSNjs"), InlineKeyboardButton("🆘 پشتیبانی", callback_data="support")]
    ])

def self_menu_keyboard(is_active: bool):
    btn_text = "🔴 خاموش کردن سلف" if is_active else "🟢 روشن کردن سلف (۶۰ الماس/ساعت)"
    btn_data = "turn_off_self" if is_active else "turn_on_self"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_text, callback_data=btn_data)],
        [InlineKeyboardButton("📱 ورود / اتصال اکانت جدید", callback_data="login_self")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ])

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    balance = get_balance(user_id)
    text = (
        f"🔥 به ام اس ان سلف خوش آمدی، {message.from_user.first_name}!\n"
        f"──────────────────\n"
        f"💎 موجودی شما: {balance} الماس\n\n"
        f"برای مدیریت سلف‌بات و خدمات از منوی زیر استفاده کنید 👇"
    )
    await message.reply_text(text, reply_markup=main_menu_keyboard())

@app.on_callback_query()
async def callback_handler(client, query):
    user_id = query.from_user.id
    data = query.data

    if data == "main_menu":
        await query.answer()
        await query.edit_message_text("یک گزینه را انتخاب کنید:", reply_markup=main_menu_keyboard())

    elif data == "panel_self":
        await query.answer()
        is_active = user_self_sessions.get(user_id, {}).get("status", False)
        status_text = "🟢 روشن" if is_active else "🔴 خاموش"
        text = (
            f"⚡ **پنل مدیریت سلف‌بات**\n\n"
            f"📊 وضعیت سلف: {status_text}\n"
            f"💰 هزینه: ۶۰ الماس به ازای هر ۱ ساعت\n\n"
            f"📌 قابلیت‌ها:\n"
            f"▫️ ساعت تپچی روی اسم\n"
            f"▫️ منشی خودکار هنگام آفلاین بودن\n"
            f"▫️ قفل جوین اجباری برای گفتگو در پیوی\n"
            f"▫️ کنترل کامل با ارسال کلمه **«پنل»** در پیوی خودتان"
        )
        await query.edit_message_text(text, reply_markup=self_menu_keyboard(is_active))

    elif data == "login_self":
        await query.answer()
        user_states[user_id] = "WAITING_PHONE"
        await app.send_message(
            user_id,
            "📱 لطفاً شماره تلفن اکانتی که می‌خواهید روی آن سلف وصل شود را ارسال کنید:\nمثال: `+989123456789`"
        )

    elif data == "check_balance":
        await query.answer(f"💎 موجودی شما: {get_balance(user_id)} الماس", show_alert=True)

    elif data == "lucky_wheel":
        now = time.time()
        last_spin = last_wheel_spin.get(user_id, 0)
        if now - last_spin < 86400:
            await query.answer("⏳ هر ۲۴ ساعت یکبار می‌توانید چرخ شانس را بزنید!", show_alert=True)
            return
        last_wheel_spin[user_id] = now
        win = random.choice([0, 10, 20, 50, 100])
        user_balances[user_id] = get_balance(user_id) + win
        await query.answer(f"🎡 شما {win} الماس برنده شدید!", show_alert=True)

if __name__ == "__main__":
    print("Bot is running...")
    app.run()
      
