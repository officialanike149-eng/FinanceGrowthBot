import os
import logging
from html import escape

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEB_APP_URL = os.getenv("WEB_APP_URL", "").strip()

WELCOME = (
    "👋 <b>Welcome to Forex Trading Hub!</b>\n\n"
    "Your Forex companion for learning, market information, "
    "trading calculations, and easy access to our Mini App.\n\n"
    "📚 Learn Forex step by step.\n"
    "📊 Explore market analysis resources.\n"
    "🧮 Calculate basic trading values.\n"
    "📱 Open the Forex Mini App below.\n\n"
    "<i>Trading involves risk. Educational information is not "
    "financial advice or a guarantee of profit.</i>\n\n"
    "👇 <b>Choose an option to get started:</b>"
)


def main_menu():
    rows = [
        [InlineKeyboardButton("📱 Open Forex Mini App",
                              web_app=WebAppInfo(url=WEB_APP_URL))]
        if WEB_APP_URL.startswith("https://") else
        [InlineKeyboardButton("📱 Open Forex Mini App",
                              url=WEB_APP_URL or "https://telegram.org")],
        [
            InlineKeyboardButton("📚 Forex Education", callback_data="education"),
            InlineKeyboardButton("📊 Market Analysis", callback_data="analysis"),
        ],
        [
            InlineKeyboardButton("🧮 Trading Calculator", callback_data="calculator"),
            InlineKeyboardButton("📈 Trading Signals", callback_data="signals"),
        ],
        [
            InlineKeyboardButton("⚠️ Risk Management", callback_data="risk"),
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Main Menu", callback_data="home")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = escape(update.effective_user.first_name or "Trader")
    await update.effective_message.reply_text(
        f"Hello, {user}!\n\n" + WELCOME,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pages = {
        "home": (
            "🏠 <b>Main Menu</b>\n\nChoose a service below.",
            main_menu(),
        ),
        "education": (
            "📚 <b>Forex Education</b>\n\n"
            "Forex is the market where currencies are exchanged.\n\n"
            "• <b>Currency pair:</b> Two currencies, such as EUR/USD.\n"
            "• <b>Spread:</b> Difference between the buy and sell price.\n"
            "• <b>pip:</b> A standard unit of price movement for many pairs.\n"
            "• <b>Lot:</b> A unit used to measure trade size.\n"
            "• <b>Leverage:</b> Exposure larger than your deposited margin; "
            "it can magnify losses as well as gains.\n\n"
            "Start by learning demo trading and basic risk management.",
            back_menu(),
        ),
        "analysis": (
            "📊 <b>Market Analysis</b>\n\n"
            "Review economic calendars, central-bank announcements, "
            "and reliable financial news before making decisions.\n\n"
            "This bot does not currently receive live prices or verify "
            "real-time market signals. Connect a trusted data source "
            "to enable live market information.",
            back_menu(),
        ),
        "calculator": (
            "🧮 <b>Trading Calculator</b>\n\n"
            "Send a message in this format:\n"
            "<code>/risk 1000 1 20</code>\n\n"
            "Example: account balance 1000, risk 1%, stop-loss "
            "distance 20 pips.\n\n"
            "The bot estimates the money at risk and does not "
            "calculate lot size without the pair and pip value.",
            back_menu(),
        ),
        "signals": (
            "📈 <b>Trading Signals</b>\n\n"
            "No live signals are configured yet. This section can "
            "display signals after you connect and validate a legitimate "
            "signal source.\n\n"
            "Never treat an unverified signal as guaranteed profit.",
            back_menu(),
        ),
        "risk": (
            "⚠️ <b>Risk Management</b>\n\n"
            "• Risk only what you can afford to lose.\n"
            "• Consider a stop-loss before entering a trade.\n"
            "• Avoid excessive leverage.\n"
            "• Test strategies on a demo account.\n"
            "• Remember that stop-loss orders may not always fill "
            "at the requested price during volatile markets.",
            back_menu(),
        ),
        "help": (
            "❓ <b>Help Center</b>\n\n"
            "/start — Open the main menu\n"
            "/risk BALANCE PERCENT PIPS — Estimate risk amount\n"
            "/help — Show this help message\n\n"
            "Use the buttons to navigate the bot.",
            back_menu(),
        ),
    }

    text, keyboard = pages.get(
        query.data,
        ("Please choose an option from the main menu.", main_menu()),
    )
    await query.edit_message_text(
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 3:
            raise ValueError

        balance, percent, pips = map(float, context.args)

        if balance <= 0 or not 0 < percent <= 100 or pips <= 0:
            raise ValueError

        amount = balance * percent / 100
        await update.effective_message.reply_text(
            "🧮 Risk Estimate\n\n"
            f"Account balance: {balance:,.2f}\n"
            f"Risk percentage: {percent:g}%\n"
            f"Stop-loss distance: {pips:g} pips\n"
            f"Estimated money at risk: {amount:,.2f}\n\n"
            "This is a risk-budget estimate, not a lot-size calculation. "
            "Actual loss depends on trade size, pip value, fees, slippage, "
            "and account currency."
        )
    except (ValueError, TypeError):
        await update.effective_message.reply_text(
            "Usage: /risk BALANCE PERCENT PIPS\n"
            "Example: /risk 1000 1 20"
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return

    text = message.text.lower().strip()

    if any(word in text for word in ["hello", "hi", "hey"]):
        reply = "👋 Hello, trader! Choose an option from the menu to begin."
    elif "pip" in text:
        reply = "📚 A pip is a standard measure of price movement in many currency pairs."
    elif "spread" in text:
        reply = "📚 The spread is the difference between a market's bid and ask prices."
    elif "lot" in text:
        reply = "📚 A lot measures trade size. The money at risk also depends on pip value and stop-loss distance."
    elif "signal" in text:
        reply = "📈 Live signals are not configured yet. Please use the Trading Signals menu for details."
    elif "price" in text or "market" in text:
        reply = "📊 Live prices are not connected yet. Check a trusted market data source."
    else:
        reply = (
            "I'm your Forex information assistant. 📚\n\n"
            "Choose Forex Education, Market Analysis, Trading Calculator, "
            "Risk Management, or Help from the menu."
        )

    await message.reply_text(reply, reply_markup=main_menu())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Use /start for the main menu.\n"
        "Use /risk 1000 1 20 to estimate risk.\n"
        "Choose a button to explore the available features.",
        reply_markup=main_menu(),
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Add it in Railway Variables."
        )

    if not WEB_APP_URL.startswith("https://"):
        raise RuntimeError(
            "WEB_APP_URL is missing or invalid. Add your HTTPS Mini App URL "
            "in Railway Variables."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("risk", risk_command))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    print("Forex Telegram Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
