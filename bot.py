import telebot
from telebot import types
import os

# ====== CONFIG ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")          # Render env variable se aayega
PRIVATE_CHANNEL_ID = int(os.environ.get("PRIVATE_CHANNEL_ID"))  # e.g. -1001234567890
JOIN_LINK = "https://t.me/+cmYU5y-227EyMzQ1"

bot = telebot.TeleBot(BOT_TOKEN)

# ====== 1. START COMMAND ======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # QR code ke saath message bhejo
    with open('pay.png', 'rb') as qr:
        bot.send_photo(
            message.chat.id,
            qr,
            caption=(
                "SOUNDBOX FAKE PAYMENT PHONE PAY 
 

PRICE - ONLY 200 RUPEES ( After making the payment, send your Telegram username along with the screenshot.)

FEATURES - Soundbox Working 
                    - Unlimited Balance 
                    - Truecaller Massage 
                    - All Banks Support \n\n"
                "💳 Payment karne ke liye upar diya gaya QR code scan karein.\n"
                "📸 Payment ke baad screenshot aur apna Telegram username bhejein."
            )
        )
    # User ko batayein ki screenshot + username bhejna hai
    bot.send_message(
        message.chat.id,
        "Ab apna payment screenshot aur Telegram username (jaise @username) ek saath bhejein."
    )

# ====== 2. SCREENSHOT + USERNAME RECEIVE ======
@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    # User ka username nikalo
    username = message.from_user.username
    if not username:
        bot.reply_to(message, "Aapke Telegram account par username set nahi hai. Pehle username set karein.")
        return

    # Screenshot ki file_id
    file_id = message.photo[-1].file_id

    # Private channel ko bhejo with Approve/Reject buttons
    markup = types.InlineKeyboardMarkup(row_width=2)
    approve_btn = types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{message.from_user.id}")
    reject_btn = types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.from_user.id}")
    markup.add(approve_btn, reject_btn)

    caption = (
        f"🆕 New Payment Request\n"
        f"👤 User: @{username}\n"
        f"🆔 User ID: {message.from_user.id}"
    )

    bot.send_photo(
        PRIVATE_CHANNEL_ID,
        file_id,
        caption=caption,
        reply_markup=markup
    )

    # User ko confirm karo
    bot.reply_to(
        message,
        "✅ Aapka payment screenshot mil gaya. Admin verify karega, thoda wait karein."
    )

# ====== 3. APPROVE / REJECT CALLBACK ======
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_approval(call):
    action, user_id_str = call.data.split('_', 1)
    user_id = int(user_id_str)

    if action == 'approve':
        bot.send_message(
            user_id,
            f"🎉 Your deal approved!\n\nJOIN: {JOIN_LINK}"
        )
        bot.answer_callback_query(call.id, "✅ Approved & link sent to user.")
        # Channel message edit karke status dikhao
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n✅ APPROVED",
            reply_markup=None
        )
    else:
        bot.send_message(
            user_id,
            "❌ Your deal rejected."
        )
        bot.answer_callback_query(call.id, "❌ Rejected & user notified.")
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n❌ REJECTED",
            reply_markup=None
        )

# ====== 4. POLLING START ======
if __name__ == "__main__":
    bot.polling(none_stop=True)
