# 🚀 Deployment Guide

Deploy your Job Deadline Tracker Bot to run 24/7 on free hosting platforms.

## Table of Contents

1. [Railway.app (Recommended)](#railwayapp-recommended)
2. [Render.com](#rendercom)
3. [PythonAnywhere](#pythonanywhere)
4. [Local Machine / Raspberry Pi](#local-machine--raspberry-pi)
5. [Comparison Table](#comparison-table)

---

## Railway.app (Recommended)

**Best for:** Beginners, fastest setup, most reliable

### Prerequisites
- GitHub account
- Railway account (sign up with GitHub)

### Setup Steps

**1. Prepare Your Repository**

Make sure your code is pushed to GitHub:
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

**2. Sign Up for Railway**

- Go to [Railway.app](https://railway.app/)
- Click "Login" and sign in with GitHub
- Authorize Railway to access your repositories

**3. Create New Project**

- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose `job-deadline-tracker-bot` repository
- Railway will detect Python automatically

**4. Add Environment Variables**

- Click on your deployment
- Go to "Variables" tab
- Click "Raw Editor"
- Paste your environment variables:

```env
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_USER_ID=your_user_id
GEMINI_API_KEY=your_key
GOOGLE_SHEET_ID=your_sheet_id
USER_TIMEZONE=Asia/Dhaka
```

**5. Add Google Credentials**

For `credentials.json`, you need to convert it to a single line:

```bash
# On your local machine
cat credentials.json | jq -c . | base64
```

Then add to Railway variables:
```env
GOOGLE_SHEETS_CREDENTIALS_BASE64=<base64_encoded_content>
```

And modify your code to decode it (add to bot.py):
```python
import os
import base64
import json

# At the start of bot.py
if os.getenv('GOOGLE_SHEETS_CREDENTIALS_BASE64'):
    creds_json = base64.b64decode(os.getenv('GOOGLE_SHEETS_CREDENTIALS_BASE64'))
    with open('credentials.json', 'wb') as f:
        f.write(creds_json)
```

**6. Deploy**

- Click "Deploy"
- Railway will automatically:
  - Install dependencies from `requirements.txt`
  - Run `python bot.py`
- Check logs to verify bot is running

**7. Verify**

- Send `/start` to your bot on Telegram
- Bot should respond immediately

### Free Tier Limits

- **500 hours per month** (enough for 24/7 operation with $5 free credit)
- **100 GB outbound bandwidth**
- **512 MB RAM**

### Cost After Free Tier

- ~$5-10/month after free credit expires
- Can pause when not needed

---

## Render.com

**Best for:** Those who want zero cost forever (with limitations)

### Setup Steps

**1. Prepare Repository**

Push your code to GitHub.

**2. Create Render Account**

- Go to [Render.com](https://render.com/)
- Sign up with GitHub

**3. Create Web Service**

- Click "New +" > "Web Service"
- Connect to your GitHub repository
- Choose `job-deadline-tracker-bot`

**4. Configure Service**

- **Name:** job-tracker-bot
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python bot.py`
- **Instance Type:** Free

**5. Add Environment Variables**

In "Environment" section, add:
```env
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_USER_ID=your_user_id
GEMINI_API_KEY=your_key
GOOGLE_SHEET_ID=your_sheet_id
USER_TIMEZONE=Asia/Dhaka
PYTHON_VERSION=3.9.0
```

**6. Add Google Credentials as Secret File**

- In Render dashboard, go to "Secret Files"
- Add file path: `credentials.json`
- Paste the contents of your `credentials.json`

**7. Deploy**

- Click "Create Web Service"
- Wait for deployment (5-10 minutes)
- Check logs for success

### Free Tier Limits

- **750 hours per month** (enough for 24/7)
- **512 MB RAM**
- **Spins down after 15 minutes of inactivity**
- **Slow start-up after inactivity** (~30 seconds)

### Important Note

Render free tier **spins down** your service after inactivity. This means:
- Bot might not respond immediately after being idle
- Scheduled reminders might not work reliably
- Consider upgrading to paid tier ($7/month) for always-on

---

## PythonAnywhere

**Best for:** Python-specific hosting, reliable free tier

### Setup Steps

**1. Create Account**

- Go to [PythonAnywhere.com](https://www.pythonanywhere.com/)
- Sign up for free "Beginner" account

**2. Upload Code**

Option A - Git Clone:
```bash
# In PythonAnywhere Bash console
git clone https://github.com/your-username/job-deadline-tracker-bot.git
cd job-deadline-tracker-bot
```

Option B - Manual Upload:
- Use "Files" tab to upload your code

**3. Install Dependencies**

In PythonAnywhere Bash console:
```bash
cd job-deadline-tracker-bot
pip3.9 install --user -r requirements.txt
```

**4. Upload Credentials**

- Go to "Files" tab
- Navigate to `job-deadline-tracker-bot` folder
- Upload `credentials.json`

**5. Create .env File**

In "Files" tab, create `.env`:
```env
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_USER_ID=your_user_id
GEMINI_API_KEY=your_key
GOOGLE_SHEET_ID=your_sheet_id
USER_TIMEZONE=Asia/Dhaka
```

**6. Create Always-On Task**

PythonAnywhere free tier doesn't support always-on tasks, so we'll use a scheduled task workaround:

- Go to "Tasks" tab
- Add a new scheduled task
- Command: `python3.9 /home/yourusername/job-deadline-tracker-bot/bot.py`
- Schedule: Daily at specific time

**Note:** Free tier only allows scheduled tasks, not continuously running processes.

### Free Tier Limits

- **One web app**
- **Daily scheduled tasks only** (not always-on)
- **512 MB disk space**
- **Limited CPU time**

### Limitation

The free tier doesn't support always-on bots. Consider:
- Upgrading to "Hacker" plan ($5/month) for always-on
- Or use Railway/Render for always-on free tier

---

## Local Machine / Raspberry Pi

**Best for:** Complete control, testing, running on home server

### Requirements

- Computer that stays on 24/7
- Python 3.9+ installed
- Stable internet connection

### Setup Steps

**1. Install Dependencies**

```bash
cd job-deadline-tracker-bot
pip install -r requirements.txt
```

**2. Configure Environment**

Copy and edit `.env`:
```bash
cp .env.example .env
nano .env  # or use any text editor
```

**3. Run Bot**

```bash
python bot.py
```

### Run in Background (Linux/Mac)

**Using screen:**
```bash
screen -S jobbot
python bot.py
# Press Ctrl+A then D to detach
# To reattach: screen -r jobbot
```

**Using nohup:**
```bash
nohup python bot.py > bot.log 2>&1 &
```

**Using systemd (Linux):**

Create `/etc/systemd/system/jobbot.service`:
```ini
[Unit]
Description=Job Deadline Tracker Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/job-deadline-tracker-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable jobbot
sudo systemctl start jobbot
sudo systemctl status jobbot
```

### Run on Startup (Windows)

1. Create a `.bat` file:
```batch
@echo off
cd C:\path\to\job-deadline-tracker-bot
python bot.py
```

2. Add to Windows Startup folder:
   - Press Win+R
   - Type `shell:startup`
   - Copy your `.bat` file there

---

## Comparison Table

| Feature | Railway | Render | PythonAnywhere | Local |
|---------|---------|--------|----------------|-------|
| **Cost** | $0 (500hrs/mo) | $0 (free tier) | $0 (limited) | $0 |
| **Always-On** | ✅ Yes | ⚠️ Spins down | ❌ No (free) | ✅ Yes |
| **Setup Time** | 5 min | 10 min | 15 min | 2 min |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Reminders** | ✅ Reliable | ⚠️ May delay | ❌ Limited | ✅ Reliable |
| **Best For** | Beginners | Budget-conscious | Python devs | Advanced users |

### Recommendations

- **For most users:** Railway.app (easiest setup, most reliable)
- **For zero cost:** Render.com (with spin-down limitation)
- **For home use:** Local machine with systemd
- **For learning:** Start local, then deploy to Railway

---

## Post-Deployment Checklist

After deploying, verify:

- [ ] Bot responds to `/start` command
- [ ] Can send a job URL and get response
- [ ] Job is saved to Google Sheet
- [ ] Sheet formatting is applied
- [ ] Check logs for any errors
- [ ] Test `/list` command
- [ ] Test `/applied 1` command

## Monitoring

### Check Bot Status

**Railway:**
- Dashboard > Deployments > View Logs

**Render:**
- Dashboard > Logs

**Local:**
```bash
# If using systemd
sudo journalctl -u jobbot -f

# If using screen
screen -r jobbot

# If using nohup
tail -f bot.log
```

### Common Deployment Issues

**"Bot not responding"**
- Check logs for errors
- Verify environment variables are set
- Ensure bot token is correct

**"Can't connect to Google Sheets"**
- Verify credentials.json is uploaded
- Check service account has access to sheet
- Ensure Sheet ID is correct

**"Memory errors on free tier"**
- Reduce logging verbosity
- Consider upgrading to paid tier
- Optimize code if possible

---

## Updating Your Deployed Bot

### Railway/Render (Git-based)

```bash
# Make changes locally
git add .
git commit -m "Update bot features"
git push origin main

# Railway/Render will auto-deploy
```

### PythonAnywhere

```bash
# In PythonAnywhere console
cd job-deadline-tracker-bot
git pull origin main
# Restart scheduled task
```

### Local

```bash
git pull origin main
# If using systemd:
sudo systemctl restart jobbot
```

---

## 🆘 Need Help?

- Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review logs for specific errors
- Open [GitHub Issue](https://github.com/farzana-bhuiyan-meem/job-deadline-tracker-bot/issues)

---

**Next Steps:** After deployment, test your bot thoroughly and check the [Troubleshooting Guide](TROUBLESHOOTING.md) if you encounter any issues.
