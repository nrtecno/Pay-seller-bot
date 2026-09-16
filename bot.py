import os
import telebot
from telebot import types

# ====== CONFIG ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PRIVATE_CHANNEL_ID = int(os.environ.get("PRIVATE_CHANNEL_ID"))
JOIN_LINK = "https://t.me/+cmYU5y-227EyMzQ1"

bot = telebot.TeleBot(BOT_TOKEN)


# ====== 1. START COMMAND ======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        with open('pay.png', 'rb') as qr:
            bot.send_photo(
                message.chat.id,
                qr,
                caption=(
                    "SOUNDBOX FAKE PAYMENT PHONE PAY 👿\n\n"
                    "PRICE - ONLY 200 RUPEES ( After making the payment, send your "
                    "Telegram username along with the screenshot.)\n\n"
                    "FEATURES - Soundbox Working\n"
                    "                    - Unlimited Balance\n"
                    "                    - Truecaller Massage\n"
                    "                    - All Banks Support"
                )
            )
    except FileNotFoundError:
        bot.send_message(
            message.chat.id,
            "⚠️ pay.png file nahi mili. Admin se contact karein."
        )
    except Exception as e:
        print("Start error:", e)


# ====== 2. SCREENSHOT RECEIVE ======
@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    try:
        username = message.from_user.username

        if not username:
            bot.reply_to(
                message,
                "⚠️ Aapke Telegram account par username set nahi hai.\n"
                "Pehle Telegram Settings me jaakar username set karein, "
                "phir screenshot ke saath dobara bhejein."
            )
            return

        file_id = message.photo[-1].file_id

        markup = types.InlineKeyboardMarkup(row_width=2)
        approve_btn = types.InlineKeyboardButton(
            "✅ Approve",
            callback_data=f"approve_{message.from_user.id}"
        )
        reject_btn = types.InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject_{message.from_user.id}"
        )
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

        bot.reply_to(
            message,
            "✅ Aapka payment screenshot mil gaya.\n"
            "Admin verify karega, thoda wait karein."
        )

    except Exception as e:
        print("Screenshot handler error:", e)
        bot.reply_to(message, "⚠️ Kuch error aayi. Dobara try karein.")


# ====== 3. APPROVE / REJECT CALLBACK ======
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_approval(call):
    try:
        action, user_id_str = call.data.split('_', 1)
        user_id = int(user_id_str)

        if action == 'approve':
            # User ko JOIN link bhejo
            try:
                bot.send_message(
                    user_id,
                    f"🎉 Your deal approved!\n\nJOIN: {JOIN_LINK}"
                )
            except Exception as e:
                print("User notify error (approve):", e)

            bot.answer_callback_query(call.id, "✅ Approved & link sent.")

            # Channel message update karo
            try:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=(call.message.caption or "") + "\n\n✅ APPROVED",
                    reply_markup=None
                )
            except Exception as e:
                print("Edit caption error (approve):", e)

        else:
            # User ko reject message bhejo
            try:
                bot.send_message(user_id, "❌ Your deal rejected.")
            except Exception as e:
                print("User notify error (reject):", e)

            bot.answer_callback_query(call.id, "❌ Rejected & user notified.")

            try:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=(call.message.caption or "") + "\n\n❌ REJECTED",
                    reply_markup=None
                )
            except Exception as e:
                print("Edit caption error (reject):", e)

    except Exception as e:
        print("Callback handler error:", e)


# ====== 4. POLLING START ======
if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
