# 🔑 API Setup Guide

Complete step-by-step guide to obtain all required API keys and credentials.

## Table of Contents

1. [Telegram Bot Token](#1-telegram-bot-token)
2. [Telegram User ID](#2-telegram-user-id)
3. [Ollama Setup (Local AI)](#3-ollama-setup-local-ai)
4. [Google Sheets API Setup](#4-google-sheets-api-setup)
5. [Jina AI API Key (Optional)](#5-jina-ai-api-key-optional)

---

## 1. Telegram Bot Token

### Step-by-Step Instructions

**1. Open Telegram**
   - Open Telegram on your phone or desktop
   - Or use [Telegram Web](https://web.telegram.org)

**2. Find BotFather**
   - Search for `@BotFather` in the search bar
   - Or click: [@BotFather](https://t.me/botfather)
   - Click "Start" to begin conversation

**3. Create New Bot**
   - Send the command: `/newbot`
   - BotFather will ask for a name for your bot
   - Enter a friendly name (e.g., "My Job Tracker")

**4. Choose Username**
   - BotFather will ask for a username
   - Must end with "bot" (e.g., "my_job_tracker_bot")
   - Username must be unique

**5. Get Your Token**
   - BotFather will send you a message with your bot token
   - It looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
   - **Copy this token** - you'll need it for `.env` file
   - **⚠️ Keep it secret!** Never share this token publicly

### Example BotFather Conversation

```
You: /newbot

BotFather: Alright, a new bot. How are we going to call it?

You: My Job Tracker

BotFather: Good. Now let's choose a username for your bot.

You: my_job_tracker_bot

BotFather: Done! Your bot is ready.
Token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### What to do with the token:

Add to `.env` file:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

---

## 2. Telegram User ID

Your User ID is needed to restrict bot access to only you.

### Method 1: Using @userinfobot (Easiest)

**1. Find the bot**
   - Search for `@userinfobot` in Telegram
   - Or click: [@userinfobot](https://t.me/userinfobot)

**2. Start the bot**
   - Click "Start" or send any message

**3. Get your ID**
   - The bot will reply with your User ID
   - It's a number like: `123456789`

### Method 2: Using @raw_data_bot

**1. Find the bot**
   - Search for `@raw_data_bot`

**2. Send a message**
   - The bot will show your full user data
   - Look for `"id":` followed by a number

### What to do with the User ID:

Add to `.env` file:
```env
TELEGRAM_USER_ID=123456789
```

---

## 3. Ollama Setup (Local AI)

Ollama runs locally on your computer - no API key needed!

### Step-by-Step Instructions

**1. Download Ollama**
   - Visit: [https://ollama.com/download](https://ollama.com/download)
   - Download the installer for your operating system:
     - Windows: Download and run the installer
     - macOS: Download and install the app
     - Linux: Run `curl -fsSL https://ollama.com/install.sh | sh`

**2. Install Ollama**
   - Run the downloaded installer
   - Follow the installation prompts
   - Ollama will start automatically after installation

**3. Pull Llama 3.2 Model**
   - Open terminal/command prompt
   - Run this command:
     ```bash
     ollama pull llama3.2
     ```
   - Wait for the model to download (~2GB, takes 2-10 minutes depending on internet speed)

**4. Verify It Works**
   - Test Ollama by running:
     ```bash
     ollama run llama3.2 "Hello"
     ```
   - If it responds with a greeting, Ollama is working!

### Benefits of Using Ollama

- ✅ **No API Key Required** - Works out of the box
- ✅ **100% Private** - All data stays on your computer
- ✅ **No Rate Limits** - Unlimited extractions
- ✅ **Completely Free** - No ongoing costs
- ✅ **Works Offline** - No internet required after model download
- ✅ **No 404 Errors** - Runs locally, no API issues

### System Requirements

- **Disk Space:** ~4GB for Llama 3.2 model
- **RAM:** 8GB minimum (16GB recommended)
- **OS:** Windows, macOS, or Linux

### Troubleshooting

**If Ollama doesn't start automatically:**
- Windows: Run "Ollama" from Start menu
- macOS: Open Ollama app from Applications
- Linux: Run `ollama serve` in terminal

**If model pull fails:**
- Check your internet connection
- Try again: `ollama pull llama3.2`
- Make sure you have enough disk space

### No Configuration Needed!

Unlike API-based services, Ollama requires no configuration in `.env` file. The bot will automatically detect and use Ollama if it's running.

---

## 4. Google Sheets API Setup

This is the most complex setup but follow carefully and you'll be fine!

### Part A: Enable Google Sheets API

**1. Go to Google Cloud Console**
   - Visit: [https://console.cloud.google.com/](https://console.cloud.google.com/)
   - Sign in with your Google account

**2. Create a New Project**
   - Click on the project dropdown (top left)
   - Click "New Project"
   - Enter name: "Job Tracker Bot"
   - Click "Create"
   - Wait for project to be created (~30 seconds)
   - **Select the new project** from dropdown

**3. Enable Google Sheets API**
   - Go to: [https://console.cloud.google.com/apis/library](https://console.cloud.google.com/apis/library)
   - Search for "Google Sheets API"
   - Click on "Google Sheets API"
   - Click "Enable"
   - Wait for it to enable (~10 seconds)

### Part B: Create Service Account

**1. Go to Credentials**
   - In Google Cloud Console, go to: APIs & Services > Credentials
   - Or visit: [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)

**2. Create Service Account**
   - Click "Create Credentials" > "Service Account"
   - Enter Service Account name: "job-tracker-bot"
   - Click "Create and Continue"
   - Skip "Grant this service account access" (click Continue)
   - Skip "Grant users access" (click Done)

**3. Create Key**
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose "JSON" format
   - Click "Create"
   - **A JSON file will download automatically**
   - Rename it to `credentials.json`
   - Move it to your project folder

**4. Note the Service Account Email**
   - In the service account details, copy the email address
   - It looks like: `job-tracker-bot@project-name.iam.gserviceaccount.com`
   - You'll need this in the next step!

### Part C: Create and Share Google Sheet

**1. Create New Sheet**
   - Go to [Google Sheets](https://sheets.google.com)
   - Click "+ Blank" to create new spreadsheet
   - Name it: "Job Deadline Tracker"

**2. Get Sheet ID**
   - Look at the URL in your browser
   - It looks like: `https://docs.google.com/spreadsheets/d/ABCDEF123456xyz/edit`
   - The Sheet ID is: `ABCDEF123456xyz` (the part between `/d/` and `/edit`)
   - **Copy this Sheet ID**

**3. Share with Service Account**
   - Click the "Share" button (top right)
   - Paste the service account email you copied earlier
   - **Important:** Give "Editor" permission (not "Viewer")
   - Uncheck "Notify people" (it's a service account, not a real person)
   - Click "Share"

### What to add to `.env` file:

```env
GOOGLE_SHEETS_CREDENTIALS=credentials.json
GOOGLE_SHEET_ID=ABCDEF123456xyz
```

### Troubleshooting

**"Permission denied" error?**
- Make sure you shared the sheet with the service account email
- Check that you gave "Editor" permission (not just "Viewer")

**"Credentials file not found"?**
- Ensure `credentials.json` is in the same folder as `bot.py`
- Check the file name is exactly `credentials.json`

**"API not enabled"?**
- Go back to Google Cloud Console
- Verify "Google Sheets API" is enabled
- Wait a few minutes and try again

---

## 5. Jina AI API Key (Optional)

Jina AI Reader is used for web scraping. It has a generous free tier that works without an API key!

### Without API Key (Recommended for Beginners)

Simply leave this empty or omit from `.env`:
```env
# JINA_API_KEY=  # Leave empty for free tier
```

The bot will work fine without it!

### With API Key (For Higher Limits)

**1. Visit Jina AI**
   - Go to: [https://jina.ai/](https://jina.ai/)
   - Sign up for a free account

**2. Get API Key**
   - Go to your dashboard
   - Navigate to API Keys section
   - Create a new API key
   - Copy the key

**3. Add to `.env`**
```env
JINA_API_KEY=your_jina_api_key_here
```

### Free Tier Limits

**Without API Key:**
- 1,000 requests per day
- Sufficient for 30-50 jobs per day

**With API Key:**
- 10,000 requests per day (free tier)

---

## ✅ Verification Checklist

Before running the bot, verify you have:

- [ ] Telegram Bot Token from @BotFather
- [ ] Your Telegram User ID
- [ ] Ollama installed with Llama 3.2 model
- [ ] Google Sheets API enabled
- [ ] Service Account created and JSON key downloaded
- [ ] `credentials.json` file in project folder
- [ ] Google Sheet created and shared with service account
- [ ] Google Sheet ID copied
- [ ] All values added to `.env` file

## 📝 Complete .env Example

Here's what your final `.env` file should look like:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_USER_ID=123456789

# Ollama runs locally - no API key needed!
# Just make sure Ollama is installed and running

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS=credentials.json
GOOGLE_SHEET_ID=ABCDEF123456xyz

# Optional: Jina AI (leave empty for free tier)
JINA_API_KEY=

# Timezone (default: Asia/Dhaka)
USER_TIMEZONE=Asia/Dhaka

# Logging (default: INFO)
LOG_LEVEL=INFO
```

## 🆘 Need Help?

If you're stuck on any step:

1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review the [README](../README.md)
3. Open an [issue on GitHub](https://github.com/farzana-bhuiyan-meem/job-deadline-tracker-bot/issues)

## ⏱️ Time Required

- Telegram Bot Token: **2 minutes**
- Telegram User ID: **1 minute**
- Ollama Setup: **5-10 minutes** (one-time download)
- Google Sheets API: **10-15 minutes** (first time)
- **Total: ~20-30 minutes**

Once you've done it once, you'll never need to do it again!

---

**Next Step:** After completing this setup, go back to the [README](../README.md) and run the bot!
