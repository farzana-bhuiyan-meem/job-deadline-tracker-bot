# 🎯 Job Deadline Tracker Bot

> Never miss a job application deadline again! Automated deadline tracking via Telegram with AI-powered detail extraction.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🤖 **Telegram Bot Interface** - Mobile-first, zero-friction job tracking
- 🔗 **Multi-Platform Support** - Works with BDJobs, LinkedIn, Indeed, Facebook Jobs, Chakri.com & more
- 🧠 **AI-Powered Extraction** - Automatically extracts company, position, deadline, salary, location
- 📊 **Google Sheets Integration** - All jobs saved with color-coded urgency
- ⏰ **Smart Reminders** - Notifications at 3 days, 1 day, and morning of deadline
- 💰 **100% Free** - Uses only free-tier APIs (Gemini, Jina AI, Google Sheets)
- 📱 **Mobile Ready** - Works perfectly on Telegram mobile app
- 🌍 **Bangladesh Optimized** - Supports Bengali text and Bangladesh timezone

## 🎬 How It Works

1. **Send a job URL** to the Telegram bot
2. **AI extracts** all details (company, position, deadline, salary, location)
3. **Saved to Google Sheet** with color coding by urgency
4. **Get reminders** automatically before deadlines
5. **Mark as applied** when done - reminders stop automatically

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.9 or higher
- ✅ Telegram account
- ✅ Google account (for Sheets API)
- ✅ 30 minutes for initial setup
- ✅ Basic command line knowledge

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/farzana-bhuiyan-meem/job-deadline-tracker-bot.git
cd job-deadline-tracker-bot
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Setup API Keys

You'll need to get three API keys (all free):

1. **Telegram Bot Token** - See [API Setup Guide](docs/API_SETUP.md)
2. **Google Gemini API Key** - See [API Setup Guide](docs/API_SETUP.md)
3. **Google Sheets Credentials** - See [API Setup Guide](docs/API_SETUP.md)

### 4️⃣ Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_USER_ID=your_telegram_user_id
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_SHEETS_CREDENTIALS=credentials.json
GOOGLE_SHEET_ID=your_google_sheet_id
USER_TIMEZONE=Asia/Dhaka
```

### 5️⃣ Run the Bot

```bash
python bot.py
```

## 📖 Detailed Setup Guide

### Step 1: Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts to name your bot
4. Copy the **Bot Token** you receive
5. Get your **User ID** by messaging [@userinfobot](https://t.me/userinfobot)

### Step 2: Get Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the generated key
4. **Cost:** Free tier includes 60 requests per minute

### Step 3: Setup Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "Google Sheets API"
4. Create Service Account credentials
5. Download JSON credentials file as `credentials.json`
6. Create a new Google Sheet
7. Share the sheet with the service account email (found in credentials.json)
8. Copy the Sheet ID from the URL

**Detailed instructions with screenshots:** [docs/API_SETUP.md](docs/API_SETUP.md)

### Step 4: Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new blank sheet
3. Copy the Sheet ID from URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`
4. Share with service account email from `credentials.json`
5. Give **Editor** permissions

### Step 5: Configure Environment Variables

Edit `.env` file with all your API keys and credentials.

### Step 6: Test the Bot

```bash
python bot.py
```

Open Telegram, find your bot, and send `/start`

## 💬 Usage Examples

### Adding a Job

Simply send any job posting URL:

```
https://www.bdjobs.com/jobs/xyz
```

The bot will:
- ✅ Extract all details automatically
- ✅ Save to Google Sheet
- ✅ Confirm with formatted message
- ✅ Setup automatic reminders

### Commands

- `/start` - Welcome message and instructions
- `/help` - Complete usage guide
- `/list` - Show all upcoming deadlines
- `/applied 1` - Mark job #1 as applied

### Example Response

```
✓ Job Added Successfully!

🏢 Company: Tech Solutions Ltd
💼 Position: Frontend Developer (React)
📅 Deadline: February 15, 2026 (14 days left)
📍 Location: Dhaka, Bangladesh
💰 Salary: 50,000-60,000 BDT

🔗 Link saved to your tracker
⏰ I'll remind you 3 days before deadline
```

## 🌐 Supported Job Platforms

The bot works with most job posting websites, including:

- ✅ BDJobs.com
- ✅ LinkedIn
- ✅ Indeed
- ✅ Facebook Jobs
- ✅ Bdjobs24.com
- ✅ Chakri.com
- ✅ Prothom Alo Jobs
- ✅ Any website with structured job postings

## ⚙️ Configuration

Edit `config.py` to customize:

- **Reminder timings** - Default: 3 days, 1 day, 0 days before deadline
- **Reminder time** - Default: 8 AM Bangladesh time
- **Timezone** - Default: Asia/Dhaka
- **Date patterns** - Add custom regex patterns for deadline extraction

## 📊 Google Sheets Structure

The bot automatically creates a sheet with these columns:

| Column | Description |
|--------|-------------|
| Company | Company name |
| Position | Job title |
| Deadline | Application deadline (YYYY-MM-DD) |
| Days Left | Auto-calculated days remaining |
| Link | Original job posting URL |
| Status | "Open" or "Applied" |
| Salary | Salary range if available |
| Location | Job location |
| Added On | Timestamp when added |

**Color Coding:**
- 🔴 Red: < 3 days left (urgent)
- 🟡 Yellow: < 7 days left (soon)
- 🟢 Default: > 7 days left

## 🚀 Deployment

Deploy your bot to run 24/7 on free hosting platforms:

### Option 1: Railway.app (Recommended)

- **Cost:** Free (500 hours/month)
- **Setup time:** 5 minutes
- **Always-on:** Yes

[Deployment Guide](docs/DEPLOYMENT.md#railway)

### Option 2: Render.com

- **Cost:** Free tier available
- **Setup time:** 10 minutes
- **Always-on:** Yes

[Deployment Guide](docs/DEPLOYMENT.md#render)

### Option 3: PythonAnywhere

- **Cost:** Free tier available
- **Setup time:** 15 minutes
- **Always-on:** Yes

[Deployment Guide](docs/DEPLOYMENT.md#pythonanywhere)

**Full deployment instructions:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 💰 Cost Breakdown

| Service | Free Tier Limit | Monthly Cost |
|---------|----------------|--------------|
| Google Gemini API | 60 requests/min | **$0** |
| Jina AI Reader | 1,000 requests/day | **$0** |
| Google Sheets API | 500 requests/100 seconds | **$0** |
| Telegram Bot API | Unlimited | **$0** |
| Railway.app hosting | 500 hours | **$0** |
| **TOTAL** | | **$0** |

For typical usage (50 jobs/month), you'll stay well within all free tier limits.

## 🔒 Security

- ✅ Bot restricted to your Telegram User ID only
- ✅ Credentials stored in `.env` (gitignored)
- ✅ Google Service Account with minimal permissions
- ✅ No sensitive data logged
- ✅ HTTPS for all API communications

## 🐛 Troubleshooting

### Bot not responding?

1. Check Telegram bot token is correct
2. Verify bot is running (`python bot.py`)
3. Check User ID matches in `.env`

### "Failed to fetch job posting"?

- Website may block automated access
- Try the URL in your browser first
- Check internet connection

### "Failed to save to Google Sheet"?

- Verify credentials.json is in correct location
- Ensure Sheet ID is correct
- Check service account has Editor permission

**More solutions:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 📚 Documentation

- [API Setup Guide](docs/API_SETUP.md) - Step-by-step API key acquisition
- [Deployment Guide](docs/DEPLOYMENT.md) - Deploy to cloud platforms
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and fixes
- [Test Examples](tests/test_examples.md) - Test cases and examples

## 🛠️ Technical Stack

- **Bot Framework:** python-telegram-bot 20.0+
- **AI/ML:** Google Gemini API
- **Web Scraping:** Jina AI Reader, BeautifulSoup4
- **Date Parsing:** dateparser
- **Sheets API:** google-api-python-client
- **Scheduling:** APScheduler
- **Timezone:** pytz

## 📁 Project Structure

```
job-deadline-tracker-bot/
├── bot.py                 # Main Telegram bot logic
├── scraper.py            # Web scraping (Jina AI + fallback)
├── extractor.py          # AI extraction (Regex + Gemini)
├── sheets.py             # Google Sheets integration
├── reminder.py           # Automated reminder system
├── utils.py              # Helper functions
├── config.py             # Configuration constants
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore patterns
├── docs/
│   ├── API_SETUP.md     # API key setup guide
│   ├── DEPLOYMENT.md    # Deployment instructions
│   └── TROUBLESHOOTING.md
└── tests/
    └── test_examples.md  # Test cases
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Google Gemini](https://ai.google.dev/)
- [Jina AI Reader](https://jina.ai/reader/)
- [python-telegram-bot](https://python-telegram-bot.org/)

## 📧 Support

Having issues? Need help?

1. Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
2. Search [existing issues](https://github.com/farzana-bhuiyan-meem/job-deadline-tracker-bot/issues)
3. Open a [new issue](https://github.com/farzana-bhuiyan-meem/job-deadline-tracker-bot/issues/new)

## 🌟 Star History

If this project helped you, please consider giving it a ⭐!

---

**Made with ❤️ for job seekers in Bangladesh**

*Never miss another deadline!* 🎯