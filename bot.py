"""
Telegram Message Scheduler Bot
================================
A bot that allows authorized admins to schedule and broadcast messages
to a target chat at configurable intervals.

Commands:
    /start          - Show welcome message and available commands
    /setmessage     - Set the message content to be broadcast
    /schedule       - Choose a scheduling option (hourly or daily)
    /status         - Show current message and schedule settings
    /stop           - Stop the scheduled broadcast
    /help           - Show command help

Author: Generated for controlled, user-authorized message automation.
"""

import logging
import asyncio
from datetime import datetime, time as dtime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, ADMIN_IDS, TARGET_CHAT_ID
from storage import Storage

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Conversation States ──────────────────────────────────────────────────────
AWAITING_MESSAGE = 1
AWAITING_DAILY_TIME = 2

# ─── Storage Instance ─────────────────────────────────────────────────────────
storage = Storage()


# ─── Authorization Decorator ──────────────────────────────────────────────────
def admin_only(func):
    """Decorator: restricts a handler to authorized admin users only."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text(
                "⛔ *Access Denied*\n\nYou are not authorized to use this bot.",
                parse_mode="Markdown",
            )
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            return ConversationHandler.END
        return await func(update, context)
    wrapper.__name__ = func.__name__
    return wrapper


# ─── Helper: Cancel any existing broadcast job ────────────────────────────────
def cancel_existing_jobs(context: ContextTypes.DEFAULT_TYPE):
    """Remove all active broadcast jobs from the job queue."""
    current_jobs = context.job_queue.get_jobs_by_name("broadcast")
    for job in current_jobs:
        job.schedule_removal()
        logger.info("Removed existing broadcast job.")


# ─── Broadcast Callback ───────────────────────────────────────────────────────
async def broadcast_message(context: ContextTypes.DEFAULT_TYPE):
    """Job callback: sends the stored message to the target chat."""
    settings = storage.load()
    msg = settings.get("message")
    if not msg:
        logger.warning("Broadcast triggered but no message is set.")
        return

    try:
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=f"📢 *Scheduled Broadcast*\n\n{msg}",
            parse_mode="Markdown",
        )
        logger.info(f"Broadcast sent to {TARGET_CHAT_ID}")
    except Exception as e:
        logger.error(f"Failed to send broadcast: {e}")


# ─── /start ───────────────────────────────────────────────────────────────────
@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with command overview."""
    text = (
        "👋 *Welcome to the Message Scheduler Bot!*\n\n"
        "I allow authorized admins to automate message broadcasts.\n\n"
        "*Available Commands:*\n"
        "📝 /setmessage — Set the broadcast message\n"
        "🕐 /schedule — Choose a schedule interval\n"
        "📊 /status — View current settings\n"
        "🛑 /stop — Stop scheduled broadcasts\n"
        "❓ /help — Show this help message\n\n"
        "_Use /setmessage to get started!_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /help ────────────────────────────────────────────────────────────────────
@admin_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display detailed usage instructions."""
    text = (
        "📖 *Bot Usage Guide*\n\n"
        "*Step 1:* Use /setmessage to write your message.\n"
        "*Step 2:* Use /schedule to pick when it repeats.\n"
        "*Step 3:* The bot broadcasts automatically!\n"
        "*Step 4:* Use /stop anytime to cancel.\n\n"
        "*Scheduling Options:*\n"
        "• Every 1 hour\n"
        "• Every 2 hours\n"
        "• Every 3 hours\n"
        "• Daily at a specific time (e.g. 09:00)\n\n"
        "*Tips:*\n"
        "— You can update the message anytime with /setmessage.\n"
        "— Changing the schedule cancels the old one automatically.\n"
        "— Use /status to check what's currently active."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /setmessage ──────────────────────────────────────────────────────────────
@admin_only
async def cmd_setmessage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Begin conversation to collect the broadcast message."""
    await update.message.reply_text(
        "✏️ *Set Broadcast Message*\n\n"
        "Please type the message you want to broadcast.\n"
        "_Send /cancel to abort._",
        parse_mode="Markdown",
    )
    return AWAITING_MESSAGE


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the user-provided message to persistent storage."""
    new_msg = update.message.text.strip()
    settings = storage.load()
    settings["message"] = new_msg
    storage.save(settings)

    await update.message.reply_text(
        f"✅ *Message saved!*\n\n```\n{new_msg}\n```\n\n"
        "Use /schedule to set or update a schedule.",
        parse_mode="Markdown",
    )
    logger.info(f"Message updated by admin {update.effective_user.id}")
    return ConversationHandler.END


# ─── /schedule ────────────────────────────────────────────────────────────────
@admin_only
async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show inline keyboard with scheduling options."""
    settings = storage.load()
    if not settings.get("message"):
        await update.message.reply_text(
            "⚠️ No message set yet. Use /setmessage first."
        )
        return

    keyboard = [
        [InlineKeyboardButton("⏱ Every 1 Hour",  callback_data="schedule_1h")],
        [InlineKeyboardButton("⏱ Every 2 Hours", callback_data="schedule_2h")],
        [InlineKeyboardButton("⏱ Every 3 Hours", callback_data="schedule_3h")],
        [InlineKeyboardButton("📅 Daily at Specific Time", callback_data="schedule_daily")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🕐 *Choose a Schedule*\n\nHow often should the message be sent?",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def handle_schedule_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the inline keyboard schedule selection."""
    query = update.callback_query
    await query.answer()
    choice = query.data

    # Hourly options
    interval_map = {
        "schedule_1h": (3600,  "every 1 hour"),
        "schedule_2h": (7200,  "every 2 hours"),
        "schedule_3h": (10800, "every 3 hours"),
    }

    if choice in interval_map:
        interval_seconds, label = interval_map[choice]

        # Cancel old jobs and schedule new repeating job
        cancel_existing_jobs(context)
        context.job_queue.run_repeating(
            broadcast_message,
            interval=interval_seconds,
            first=10,           # First run in 10 seconds
            name="broadcast",
        )

        # Persist schedule settings
        settings = storage.load()
        settings["schedule_type"] = "interval"
        settings["interval_seconds"] = interval_seconds
        settings["schedule_label"] = label
        settings["active"] = True
        storage.save(settings)

        await query.edit_message_text(
            f"✅ *Schedule Set!*\n\nYour message will be sent *{label}*.\n"
            "Use /stop to cancel at any time.",
            parse_mode="Markdown",
        )
        logger.info(f"Schedule set: {label} by admin {query.from_user.id}")

    elif choice == "schedule_daily":
        await query.edit_message_text(
            "📅 *Daily Schedule*\n\n"
            "Enter the time in *HH:MM* format (24-hour).\n"
            "Example: `09:00` or `18:30`\n\n"
            "_Send /cancel to abort._",
            parse_mode="Markdown",
        )
        return AWAITING_DAILY_TIME

    return ConversationHandler.END


async def receive_daily_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse and set a daily schedule at the user-specified time."""
    time_str = update.message.text.strip()

    # Validate HH:MM format
    try:
        t = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Please enter time as *HH:MM* (e.g. `09:00`).",
            parse_mode="Markdown",
        )
        return AWAITING_DAILY_TIME

    # Cancel old jobs and schedule daily job
    cancel_existing_jobs(context)
    context.job_queue.run_daily(
        broadcast_message,
        time=dtime(hour=t.hour, minute=t.minute, second=0),
        name="broadcast",
    )

    # Persist
    settings = storage.load()
    settings["schedule_type"] = "daily"
    settings["daily_time"] = time_str
    settings["schedule_label"] = f"daily at {time_str}"
    settings["active"] = True
    storage.save(settings)

    await update.message.reply_text(
        f"✅ *Daily Schedule Set!*\n\nYour message will be sent every day at *{time_str}*.\n"
        "Use /stop to cancel at any time.",
        parse_mode="Markdown",
    )
    logger.info(f"Daily schedule set for {time_str} by admin {update.effective_user.id}")
    return ConversationHandler.END


# ─── /status ──────────────────────────────────────────────────────────────────
@admin_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the current bot settings and schedule status."""
    settings = storage.load()
    msg = settings.get("message", "_Not set_")
    label = settings.get("schedule_label", "_Not set_")
    active = settings.get("active", False)
    status_icon = "🟢 Active" if active else "🔴 Inactive"

    text = (
        f"📊 *Current Bot Status*\n\n"
        f"*Status:* {status_icon}\n"
        f"*Schedule:* {label}\n\n"
        f"*Message Preview:*\n```\n{msg}\n```"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /stop ────────────────────────────────────────────────────────────────────
@admin_only
async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel all active broadcast jobs."""
    cancel_existing_jobs(context)

    settings = storage.load()
    settings["active"] = False
    storage.save(settings)

    await update.message.reply_text(
        "🛑 *Broadcast Stopped*\n\n"
        "All scheduled messages have been cancelled.\n"
        "Use /schedule to restart anytime.",
        parse_mode="Markdown",
    )
    logger.info(f"Broadcast stopped by admin {update.effective_user.id}")


# ─── /cancel (conversation fallback) ─────────────────────────────────────────
async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current conversation flow."""
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END


# ─── Restore Jobs on Restart ──────────────────────────────────────────────────
async def restore_jobs(application: Application):
    """Re-register scheduled jobs from persistent storage after bot restarts."""
    settings = storage.load()
    if not settings.get("active"):
        return

    schedule_type = settings.get("schedule_type")
    logger.info(f"Restoring schedule: {settings.get('schedule_label')}")

    if schedule_type == "interval":
        interval = settings.get("interval_seconds", 3600)
        application.job_queue.run_repeating(
            broadcast_message,
            interval=interval,
            first=30,  # Give the bot 30s to fully start before first send
            name="broadcast",
        )
    elif schedule_type == "daily":
        time_str = settings.get("daily_time", "09:00")
        t = datetime.strptime(time_str, "%H:%M").time()
        application.job_queue.run_daily(
            broadcast_message,
            time=dtime(hour=t.hour, minute=t.minute),
            name="broadcast",
        )
    logger.info("Schedule restored successfully.")


# ─── Main Entry Point ─────────────────────────────────────────────────────────
def main():
    """Build and run the bot application."""
    app = Application.builder().token(BOT_TOKEN).build()

    # ── Conversation: /setmessage ──
    setmessage_conv = ConversationHandler(
        entry_points=[CommandHandler("setmessage", cmd_setmessage)],
        states={
            AWAITING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    # ── Conversation: /schedule + daily time input ──
    schedule_conv = ConversationHandler(
        entry_points=[CommandHandler("schedule", cmd_schedule)],
        states={
            AWAITING_DAILY_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_daily_time)
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(setmessage_conv)
    app.add_handler(schedule_conv)
    app.add_handler(CallbackQueryHandler(handle_schedule_choice, pattern="^schedule_"))

    # Restore persisted jobs after startup
    app.post_init = restore_jobs

    logger.info("🤖 Bot is starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
