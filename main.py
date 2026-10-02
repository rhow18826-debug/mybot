async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # شناسه پیام اینلاین یا پیام معمولی
    inline_id = query.inline_message_id
    msg_key = inline_id if inline_id else f"{query.message.chat_id}_{query.message.message_id}"

    if msg_key not in votes:
        votes[msg_key] = set()

    current_text = query.message.reply_markup.inline_keyboard[0][0].text if query.message else query.data
    # دریافت تعداد لایک‌های فعلی از دکمه
    try:
        button_text = query.message.reply_markup.inline_keyboard[0][0].text
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

    # ویرایش دکمه لایک هم برای اینلاین و هم پیام معمولی
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
                
