import os
import telebot
from telebot import types
from flask import Flask, request

# ============ CONFIG (Render ENV se aayega) ============
BOT_TOKEN   = os.environ.get("BOT_TOKEN")      # Render ENV
CHANNEL_ID  = os.environ.get("CHANNEL_ID")     # Render ENV
RENDER_URL  = os.environ.get("RENDER_URL")     # Render ENV

# ============ FIXED VALUES ============
QR_FILE     = "pay.png"                        # GitHub repo me pay.png
JOIN_LINK   = "https://t.me/+cmYU5y-227EyMzQ1"
BRAND_TEXT  = "I AM NRHACKZ"

# =================================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)


# ---------- Flask routes ----------
@app.route("/", methods=["GET"])
def home():
    return "Bot is running ✅"


@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    bot.remove_webhook()
    ok = bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    return f"Webhook set: {ok}"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "", 403


# ---------- /start ----------
@bot.message_handler(commands=["start"])
def start(message):
    caption = (
        f"<b>{BRAND_TEXT}</b>\n\n"
        "💳 Neeche diya gaya QR code scan karke payment karein.\n\n"
        "📸 Payment ke baad <b>screenshot</b> bhejein aur "
        "caption me apna <b>Telegram username</b> likhein.\n\n"
        "Example caption: <code>@your_username</code>"
    )
    try:
        with open(QR_FILE, "rb") as qr:
            bot.send_photo(message.chat.id, qr, caption=caption)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            caption + f"\n\n⚠️ QR file load nahi hui: {e}"
        )


# ---------- Photo (screenshot) handler ----------
@bot.message_handler(content_types=["photo"])
def handle_screenshot(message):
    user = message.from_user
    provided_username = (message.caption or "").strip() or "Not provided"
    photo_file_id = message.photo[-1].file_id  # highest resolution

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve|{user.id}"),
        types.InlineKeyboardButton("❌ Reject",  callback_data=f"reject|{user.id}"),
    )

    channel_caption = (
        "🆕 <b>New Payment Submitted</b>\n\n"
        f"👤 Name: {user.first_name or '-'}\n"
        f"🔗 TG Username: @{user.username if user.username else 'None'}\n"
        f"📝 Caption Username: {provided_username}\n"
        f"🆔 User ID: <code>{user.id}</code>"
    )

    try:
        bot.send_photo(
            CHANNEL_ID,
            photo_file_id,
            caption=channel_caption,
            reply_markup=kb,
        )
        bot.reply_to(
            message,
            "✅ Aapka payment screenshot admin ko bhej diya gaya hai.\n"
            "Please wait for approval.",
        )
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}\nAdmin se contact karein.")


# ---------- Approve / Reject handler ----------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        action, user_id_str = call.data.split("|")
        user_id = int(user_id_str)
    except Exception:
        bot.answer_callback_query(call.id, "Invalid data")
        return

    original_caption = call.message.caption or ""

    if action == "approve":
        try:
            bot.send_message(user_id, f"JOIN: {JOIN_LINK}")
        except Exception as e:
            bot.answer_callback_query(call.id, f"User ko msg nahi gaya: {e}")
            return
        bot.answer_callback_query(call.id, "Approved ✅")
        new_caption = original_caption + "\n\n✅ <b>APPROVED</b>"

    elif action == "reject":
        try:
            bot.send_message(user_id, "your deal rejected")
        except Exception as e:
            bot.answer_callback_query(call.id, f"User ko msg nahi gaya: {e}")
            return
        bot.answer_callback_query(call.id, "Rejected ❌")
        new_caption = original_caption + "\n\n❌ <b>REJECTED</b>"

    else:
        bot.answer_callback_query(call.id, "Unknown action")
        return

    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=new_caption,
        )
    except Exception:
        pass


# ---------- Local run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
