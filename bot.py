import os
import json
import threading
import telebot
from telebot import types
from flask import Flask

# ====== CONFIG ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PRIVATE_CHANNEL_ID = int(os.environ.get("PRIVATE_CHANNEL_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
JOIN_LINK = "https://t.me/+cmYU5y-227EyMzQ1"

bot = telebot.TeleBot(BOT_TOKEN)

# ====== USER STORAGE ======
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_users():
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)
    except Exception as e:
        print("Save users error:", e)

users = load_users()
broadcast_mode = {}


# ====== 1. START ======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id not in users:
        users.add(message.chat.id)
        save_users()

    try:
        with open('pay.png', 'rb') as qr:
            bot.send_photo(
                message.chat.id,
                qr,
                caption=(
                    "SOUNDBOX FAKE PAYMENT PAYTM 👿\n\n"
                    "PRICE - ONLY 50 RUPEES ( After making the payment, send your "
                    "Telegram username along with the screenshot.)\n\n"
                    "FEATURES - Soundbox Working\n"
                    "                    - Unlimited Balance\n"
                    "                    - Truecaller Massage\n"
                    "                    - All Banks Support"
                )
            )
    except FileNotFoundError:
        bot.send_message(message.chat.id, "⚠️ pay.png file nahi mili.")
    except Exception as e:
        print("Start error:", e)


# ====== 2. /bc ======
@bot.message_handler(commands=['bc'])
def bc_command(message):
    if message.from_user.id != ADMIN_ID:
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🟢 ON", callback_data="bc_on"),
        types.InlineKeyboardButton("🔴 OFF", callback_data="bc_off")
    )
    bot.send_message(
        message.chat.id,
        "📢 Broadcast Control\n\n"
        "🟢 ON → message sab users ko jayega\n"
        "🔴 OFF → bot normal mode me",
        reply_markup=markup
    )


# ====== 3. BC TOGGLE ======
@bot.callback_query_handler(func=lambda call: call.data in ['bc_on', 'bc_off'])
def bc_toggle(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Not allowed")
        return

    if call.data == 'bc_on':
        broadcast_mode[ADMIN_ID] = True
        bot.answer_callback_query(call.id, "✅ Broadcast ON")
        bot.send_message(
            ADMIN_ID,
            "🟢 Broadcast ON. Ab jo bhejoge sab users ko jayega.\n"
            "Band karne ke liye /bc → OFF."
        )
    else:
        broadcast_mode[ADMIN_ID] = False
        bot.answer_callback_query(call.id, "🔴 Broadcast OFF")
        bot.send_message(ADMIN_ID, "🔴 Broadcast OFF. Bot normal.")


# ====== 4. BROADCAST ======
@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID and broadcast_mode.get(ADMIN_ID, False),
    content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker']
)
def broadcast_message(message):
    success, failed, removed = 0, 0, []

    for uid in list(users):
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
        except Exception as e:
            failed += 1
            removed.append(uid)
            print(f"Broadcast fail {uid}:", e)

    for uid in removed:
        users.discard(uid)
    if removed:
        save_users()

    bot.reply_to(
        message,
        f"✅ Broadcast done!\n✔️ Sent: {success}\n❌ Failed: {failed}\n"
        f"👥 Total: {len(users)}"
    )


# ====== 5. SCREENSHOT ======
@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    try:
        if message.chat.id not in users:
            users.add(message.chat.id)
            save_users()

        username = message.from_user.username
        if not username:
            bot.reply_to(
                message,
                "⚠️ Aapke Telegram account par username set nahi hai. "
                "Pehle username set karein, phir screenshot bhejein."
            )
            return

        file_id = message.photo[-1].file_id

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{message.from_user.id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.from_user.id}")
        )

        caption = (
            f"🆕 New Payment Request\n"
            f"👤 User: @{username}\n"
            f"🆔 User ID: {message.from_user.id}"
        )

        bot.send_photo(PRIVATE_CHANNEL_ID, file_id, caption=caption, reply_markup=markup)
        bot.reply_to(message, "✅ Screenshot mil gaya. Admin verify karega.")

    except Exception as e:
        print("Screenshot error:", e)
        bot.reply_to(message, "⚠️ Error aayi, dobara try karein.")


# ====== 6. APPROVE / REJECT ======
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_approval(call):
    try:
        action, user_id_str = call.data.split('_', 1)
        user_id = int(user_id_str)

        if action == 'approve':
            try:
                bot.send_message(user_id, f"🎉 Your deal approved!\n\nJOIN: {JOIN_LINK}")
            except Exception as e:
                print("Notify error:", e)
            bot.answer_callback_query(call.id, "✅ Approved")
            new_caption = (call.message.caption or "") + "\n\n✅ APPROVED"
        else:
            try:
                bot.send_message(user_id, "❌ Your deal rejected.")
            except Exception as e:
                print("Notify error:", e)
            bot.answer_callback_query(call.id, "❌ Rejected")
            new_caption = (call.message.caption or "") + "\n\n❌ REJECTED"

        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=new_caption,
                reply_markup=None
            )
        except Exception as e:
            print("Edit caption error:", e)

    except Exception as e:
        print("Callback error:", e)


# ====== 7. DUMMY HTTP SERVER ======
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!", 200

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)


# ====== 8. START ======
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot polling started...")
    bot.infinity_polling()
