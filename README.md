# 📅 Telegram Message Scheduler Bot

A clean, production-ready Telegram bot for **automated message scheduling and broadcasting**. Supports hourly and daily schedules, persistent settings, and admin-only access control.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 Admin-only access | Only whitelisted Telegram user IDs can control the bot |
| 📝 Custom messages | Set any message via `/setmessage` |
| ⏱ Interval scheduling | Every 1, 2, or 3 hours |
| 📅 Daily scheduling | Broadcast at a specific time each day (e.g. `09:00`) |
| 💾 Persistent storage | Settings survive bot restarts (JSON file) |
| 🔄 Auto-restore | Active schedules are restored automatically on restart |
| 🛑 Start/Stop control | Pause and resume broadcasts anytime |

---

## 📁 Project Structure

```
telegram_scheduler_bot/
├── bot.py              # Main bot logic and command handlers
├── config.py           # Loads environment variables
├── storage.py          # JSON-based persistent settings storage
├── requirements.txt    # Python dependencies
├── .env.example        # Template for environment variables
├── .env                # Your actual secrets (DO NOT commit this)
└── data/
    └── settings.json   # Auto-created; stores message + schedule state
```

---

## 🚀 Setup Guide

### Step 1 — Prerequisites

- Python 3.10 or higher
- A Telegram account
- Internet access

### Step 2 — Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **API token** you receive (looks like `123456:ABCdef...`)

### Step 3 — Get Your Telegram User ID

1. Message **@userinfobot** on Telegram
2. It will reply with your numeric user ID (e.g. `123456789`)
3. This is your `ADMIN_IDS` value

### Step 4 — Find the Target Chat ID

The `TARGET_CHAT_ID` is where broadcasts will be sent:

- **Your private chat:** Use your own user ID from Step 3
- **A group:** Add the bot to the group, then message **@RawDataBot** in the group to get the group ID (negative number)
- **A channel:** Add the bot as admin, then the channel ID is usually `-100` + the channel's numeric ID

### Step 5 — Install Dependencies

```bash
# Clone or download the project, then:
cd telegram_scheduler_bot

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 6 — Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values
nano .env    # or open in any text editor
```

Fill in:
```env
BOT_TOKEN=123456:ABCdefGHIjklMNO...
ADMIN_IDS=123456789
TARGET_CHAT_ID=123456789
```

For multiple admins: `ADMIN_IDS=111111111,222222222`

### Step 7 — Run the Bot

```bash
python bot.py
```

You should see:
```
2024-01-01 10:00:00 | INFO | __main__ | 🤖 Bot is starting...
```

Now open Telegram and message your bot `/start`!

---

## 💬 Command Reference

| Command | Description |
|---|---|
| `/start` | Show welcome message and command overview |
| `/help` | Show detailed usage guide |
| `/setmessage` | Enter a new broadcast message interactively |
| `/schedule` | Choose a scheduling interval via inline buttons |
| `/status` | View current message, schedule, and active state |
| `/stop` | Cancel all active scheduled broadcasts |
| `/cancel` | Cancel the current input operation |

---

## 📖 Example Usage

### Setting a message and scheduling it hourly:

```
You:  /setmessage
Bot:  ✏️ Set Broadcast Message — Please type your message.

You:  🔔 Daily standup reminder: share your updates in #general!
Bot:  ✅ Message saved!

You:  /schedule
Bot:  [Shows inline buttons: Every 1 Hour / Every 2 Hours / etc.]

You:  [Tap "Every 1 Hour"]
Bot:  ✅ Schedule Set! Your message will be sent every 1 hour.
```

### Setting a daily message at 9 AM:

```
You:  /schedule
Bot:  [Inline buttons appear]

You:  [Tap "Daily at Specific Time"]
Bot:  Please enter the time in HH:MM format.

You:  09:00
Bot:  ✅ Daily Schedule Set! Your message will be sent every day at 09:00.
```

### Stopping broadcasts:

```
You:  /stop
Bot:  🛑 Broadcast Stopped. All scheduled messages have been cancelled.
```

---

## 🔁 Running as a Background Service (Linux/macOS)

### Using systemd (Linux):

Create `/etc/systemd/system/telegram-scheduler.service`:

```ini
[Unit]
Description=Telegram Scheduler Bot
After=network.target

[Service]
Type=simple
User=your_linux_username
WorkingDirectory=/path/to/telegram_scheduler_bot
ExecStart=/path/to/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-scheduler
sudo systemctl start telegram-scheduler
sudo systemctl status telegram-scheduler
```

### Using screen (quick & simple):

```bash
screen -S telegrambot
python bot.py
# Press Ctrl+A then D to detach
# Re-attach with: screen -r telegrambot
```

---

## 🔒 Security Notes

- ✅ Never share your `.env` file or commit it to Git
- ✅ Add `.env` to your `.gitignore`
- ✅ Only add trusted Telegram IDs to `ADMIN_IDS`
- ✅ For channels/groups, ensure the bot has send permissions
- ✅ This bot is designed for **authorized, opted-in recipients** only

---

## 🛠 Customization

### Swap JSON storage for SQLite:

Replace `storage.py` with an SQLite implementation using Python's built-in `sqlite3` module. The `Storage` class interface (`load()` / `save()`) stays the same.

### Add more intervals:

In `bot.py`, extend the `keyboard` list in `cmd_schedule()` and the `interval_map` dict in `handle_schedule_choice()`.

### Send to multiple chats:

Modify `broadcast_message()` to loop over a list of target chat IDs stored in settings.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `python-telegram-bot` | 21.6 | Telegram Bot API wrapper + job queue |
| `python-dotenv` | 1.0.1 | Load `.env` environment variables |

The `[job-queue]` extra installs `APScheduler` for reliable cron-style scheduling.
