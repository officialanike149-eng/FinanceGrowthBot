import logging
import os
import io
import requests
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables & Configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = "@financemasters1"
CHANNEL_URL = "https://t.me/financemasters1"

WELCOME_MESSAGE = (
    "**FinanceGrowthBot** helps you learn personal finance, "
    "improve money habits, and grow long-term wealth with simple, practical tips."
)


async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the user has joined the channel (Gatekeeper check)."""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except TelegramError as e:
        logger.warning(f"Membership check warning: {e}")
        return True  # Fallback if bot is not admin yet


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command for any user."""
    user = update.effective_user
    if not update.message:
        return

    if await is_user_member(user.id, context):
        # User is verified, show main Forex & Finance menu
        keyboard = [
            [
                InlineKeyboardButton("📊 Forex Quick Tips", callback_data="forex_tips"),
                InlineKeyboardButton("💱 Major Pairs", callback_data="forex_pairs")
            ],
            [
                InlineKeyboardButton("🎨 Generate AI Image", callback_data="menu_gen_info"),
                InlineKeyboardButton("📢 Official Channel", url=CHANNEL_URL)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        full_text = (
            f"Hello {user.first_name}! 👋\n\n"
            f"{WELCOME_MESSAGE}\n\n"
            "Choose an option below or type any question to chat with your AI assistant!"
        )
        await update.message.reply_text(text=full_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        # Force join gatekeeper prompt
        force_join = (
            f"⚠️ **Channel Access Required!**\n\n"
            f"Hello {user.first_name}, please join our official channel to unlock the bot."
        )
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
            [InlineKeyboardButton("🔄 Verify Membership", callback_data="check_subscription")]
        ]
        await update.message.reply_text(text=force_join, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles inline button clicks for Forex options and verification."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "check_subscription":
        if await is_user_member(query.from_user.id, context):
            keyboard = [
                [InlineKeyboardButton("📊 Forex Quick Tips", callback_data="forex_tips")],
                [InlineKeyboardButton("💱 Major Pairs", callback_data="forex_pairs")]
            ]
            await query.edit_message_text(
                "✅ **Verification Successful!**\n\n"
                f"{WELCOME_MESSAGE}\n\nSelect an option below:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ You haven't joined @financemasters1 yet!", show_alert=True)

    elif data == "forex_tips":
        tips_text = (
            "💡 **Top Forex Trading & Risk Habits:**\n\n"
            "1️⃣ **Never risk more than 1-2%** of your capital on a single trade.\n"
            "2️⃣ **Always use Stop-Loss orders** to protect your account from sudden market spikes.\n"
            "3️⃣ **Trade with the trend**—don't fight major market momentum.\n"
            "4️⃣ **Keep a trading journal** to review your wins and mistakes."
        )
        await query.message.reply_text(tips_text, parse_mode="Markdown")

    elif data == "forex_pairs":
        pairs_text = (
            "💱 **Major Forex Currency Pairs:**\n\n"
            "• **EUR/USD** (Euro / US Dollar) - Most liquid pair.\n"
            "• **GBP/USD** (British Pound / US Dollar) - Known as 'Cable'.\n"
            "• **USD/JPY** (US Dollar / Japanese Yen) - Highly sensitive to Asian sessions.\n"
            "• **USD/CHF** (US Dollar / Swiss Franc) - Safe-haven currency pair."
        )
        await query.message.reply_text(pairs_text, parse_mode="Markdown")

    elif data == "menu_gen_info":
        await query.message.reply_text(
            "🎨 **AI Image Generation:**\nType `/gen <description>` to create professional charts, trading setups, or custom artwork instantly!"
        )


async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answers user questions on finance and forex using keyless AI."""
    user = update.effective_user
    if not update.message or not update.message.text:
        return

    if not await is_user_member(user.id, context):
        await update.message.reply_text("❌ Please join @financemasters1 first!")
        return

    if update.message.text.startswith(("/gen", "/generate")):
        return

    status_msg = await update.message.reply_text("Thinking... 🤔")

    try:
        response = requests.post(
            "https://text.pollinations.ai/",
            json={
                "messages": [
                    {"role": "system", "content": "You are a professional forex trading mentor and personal finance advisor."},
                    {"role": "user", "content": update.message.text}
                ]
            },
            timeout=25
        )
        if response.status_code == 200:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
                text=response.text
            )
        else:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
                text="⚠️ Chat service busy. Please try again."
            )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text="⚠️ Could not process your request right now."
        )


async def handle_image_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generates images via text prompt."""
    user = update.effective_user
    if not update.message or not update.message.text:
        return

    if not await is_user_member(user.id, context):
        await update.message.reply_text("❌ Please join @financemasters1 first!")
        return

    text = update.message.text
    prompt = text[4:].strip() if text.startswith("/gen") else text[9:].strip()

    if not prompt:
        await update.message.reply_text("⚠️ Usage: `/gen <describe the image/chart you want>`", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("🎨 Creating image...")

    try:
        image_url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1024&height=1024&nologo=true"
        img_resp = requests.get(image_url, timeout=30)

        if img_resp.status_code == 200:
            stream = io.BytesIO(img_resp.content)
            stream.name = "generated.png"
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=stream,
                caption=f"🎨 Generated image for: *{prompt}*",
                parse_mode="Markdown"
            )
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        else:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
                text="⚠️ Image generation timed out."
            )
    except Exception as e:
        logger.error(f"Image gen error: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text="⚠️ Could not generate image."
        )


async def handle_incoming_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Applies a professional design mark watermark to user images."""
    user = update.effective_user
    if not update.message or not update.message.photo:
        return

    if not await is_user_member(user.id, context):
        await update.message.reply_text("❌ Please join @financemasters1 first!")
        return

    status_msg = await update.message.reply_text("🖼️ Applying professional design mark...")

    try:
        photo = await context.bot.get_file(update.message.photo[-1].file_id)
        image_data = await photo.download_as_bytearray()
        img = Image.open(io.BytesIO(image_data)).convert("RGBA")

        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = img.size

        badge_text = "★ FINANCE MASTERS DESIGN ★"
        font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), badge_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        pad = 10
        x2, y2 = w - 20, h - 20
        x1, y1 = x2 - tw - (pad * 2), y2 - th - (pad * 2)

        draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, 180), outline=(255, 215, 0, 255), width=2)
        draw.text((x1 + pad, y1 + pad), badge_text, fill=(255, 215, 0, 255), font=font)

        out_img = Image.alpha_composite(img, overlay).convert("RGB")
        out_stream = io.BytesIO()
        out_img.save(out_stream, format="JPEG", quality=95)
        out_stream.seek(0)
        out_stream.name = "designed.jpg"

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=out_stream,
            caption="✅ Professional design mark successfully applied!"
        )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)

    except Exception as e:
        logger.error(f"Image design error: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text="⚠️ Failed to design image."
        )


def main() -> None:
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is missing!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, handle_image_generation))
    app.add_handler(MessageHandler(filters.PHOTO, handle_incoming_image))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ai_chat))

    logger.info("FinanceGrowthBot worker starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
