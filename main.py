import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8696587166:AAEqiiMPkfV71cEH12mzyfjHWNvy44SFpqs"
ADMIN_ID = 7281188442
CHANNEL_USERNAME = "@EDI_MSNjs"
GROUP_USERNAME = "@hhdhdhksj"

user_likes = {}
user_voted = set()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("💬 عضویت در گروه", url=f"https://t.me/{GROUP_USERNAME[1:]}")],
        [InlineKeyboardButton("✅ بررسی عضویت و ورود", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 به ربات چالش لایک خوش آمدید!\nلطفا ابتدا در کانال و گروه ما عضو شوید:", reply_markup=reply_markup)

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        group_member = await context.bot.get_chat_member(chat_id=GROUP_USERNAME, user_id=user_id)
        
        if chat_member.status in ['member', 'administrator', 'creator'] and group_member.status in ['member', 'administrator', 'creator']:
            keyboard = [
                [InlineKeyboardButton("❤️ ثبت/مشاهده لایک من", callback_data="my_likes")],
                [InlineKeyboardButton("👍 لایک دادن به شرکت‌کننده", callback_data="give_like")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("✅ عضویت شما تایید شد! از منوی زیر استفاده کنید:", reply_markup=reply_markup)
        else:
            await query.answer("❌ هنوز در کانال یا گروه عضو نشده‌اید!", show_alert=True)
    except Exception:
        await query.answer("❌ خطا در بررسی عضویت. مطمئن شوید ربات در کانال/گروه ادمین است.", show_alert=True)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "my_likes":
        likes = user_likes.get(user_id, 0)
        await query.answer(f"تعداد لایک‌های شما: {likes}", show_alert=True)
    elif data == "give_like":
        if user_id in user_voted:
            await query.answer("شما قبلاً رای داده‌اید!", show_alert=True)
        else:
            user_likes[user_id] = user_likes.get(user_id, 0) + 1
            user_voted.add(user_id)
            await query.answer("❤️ رای شما با موفقیت ثبت شد!", show_alert=True)

async def add_fake_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        user_likes[target_id] = user_likes.get(target_id, 0) + amount
        await update.message.reply_text(f"✅ تعداد {amount} لایک به کاربر {target_id} اضافه شد.")
    except Exception:
        await update.message.reply_text("دستور اشتباه است.\nفرمت صحیح:\n/addlike USER_ID AMOUNT")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addlike", add_fake_like))
    app.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
  
