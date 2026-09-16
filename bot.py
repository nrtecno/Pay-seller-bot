import os
import json
import telebot
from telebot import types

# ====== CONFIG ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PRIVATE_CHANNEL_ID = int(os.environ.get("PRIVATE_CHANNEL_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID"))          # 👈 apna telegram user id
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

# Broadcast mode state (sirf admin ke liye)
broadcast_mode = {}


# ====== 1. START COMMAND ======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # User ko save karo
    if message.chat.id not in users:
        users.add(message.chat.id)
        save_users()

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


# ====== 2. /bc COMMAND (only admin) ======
@bot.message_handler(commands=['bc'])
def bc_command(message):
    if message.from_user.id != ADMIN_ID:
        return  # sirf admin hi use kar sakta hai

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🟢 ON", callback_data="bc_on"),
        types.InlineKeyboardButton("🔴 OFF", callback_data="bc_off")
    )
    bot.send_message(
        message.chat.id,
        "📢 Broadcast Control\n\n"
        "🟢 ON → jo message bhejoge sab users ko jayega\n"
        "🔴 OFF → bot normal mode me",
        reply_markup=markup
    )


# ====== 3. BC ON/OFF CALLBACK ======
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
            "🟢 Broadcast mode ON.\nAb jo bhi message (text/photo/video) bhejoge, "
            "wo sabhi users ko chala jayega.\n\n"
            "Band karne ke liye /bc → 🔴 OFF dabayein."
        )
    else:
        broadcast_mode[ADMIN_ID] = False
        bot.answer_callback_query(call.id, "🔴 Broadcast OFF")
        bot.send_message(
            ADMIN_ID,
            "🔴 Broadcast mode OFF. Bot ab normal chalega."
        )


# ====== 4. BROADCAST HANDLER (admin ke messages ko sabko bhejna) ======
# Ye handler photo handler se PEHLE hona chahiye
@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID and broadcast_mode.get(ADMIN_ID, False),
    content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker']
)
def broadcast_message(message):
    success = 0
    failed = 0
    removed = []

    for uid in list(users):
        try:
            bot.copy_message(
                chat_id=uid,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            success += 1
        except Exception as e:
            failed += 1
            removed.append(uid)
            print(f"Broadcast fail for {uid}:", e)

    # Jo users blocked hain unhe hata do
    for uid in removed:
        users.discard(uid)
    if removed:
        save_users()

    bot.reply_to(
        message,
        f"✅ Broadcast complete!\n\n"
        f"✔️ Sent: {success}\n"
        f"❌ Failed: {failed}\n"
        f"👥 Total users: {len(users)}"
    )


# ====== 5. SCREENSHOT RECEIVE ======
@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    try:
        # User ko save karo
        if message.chat.id not in users:
            users.add(message.chat.id)
            save_users()

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


# ====== 6. APPROVE / REJECT CALLBACK ======
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def handle_approval(call):
    try:
        action, user_id_str = call.data.split('_', 1)
        user_id = int(user_id_str)

        if action == 'approve':
            try:
                bot.send_message(
                    user_id,
                    f"🎉 Your deal approved!\n\nJOIN: {JOIN_LINK}"
                )
            except Exception as e:
                print("User notify error (approve):", e)

            bot.answer_callback_query(call.id, "✅ Approved & link sent.")

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


# ====== 7. POLLING START ======
if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
