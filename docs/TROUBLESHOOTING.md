# 🔧 Troubleshooting Guide

Common issues and their solutions for the Job Deadline Tracker Bot.

## Table of Contents

1. [Bot Not Responding](#bot-not-responding)
2. [Google Sheets Errors](#google-sheets-errors)
3. [Extraction Errors](#extraction-errors)
4. [Reminder Issues](#reminder-issues)
5. [Deployment Problems](#deployment-problems)
6. [API Rate Limits](#api-rate-limits)

---

## Bot Not Responding

### Issue: Bot doesn't respond to `/start` command

**Possible Causes:**
1. Bot is not running
2. Wrong bot token
3. User ID mismatch

**Solutions:**

**Check if bot is running:**
```bash
# Local machine
ps aux | grep bot.py

# Or check your deployment platform logs
```

**Verify bot token:**
```bash
# Check .env file
cat .env | grep TELEGRAM_BOT_TOKEN

# Test token with curl
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

Expected response:
```json
{"ok":true,"result":{"id":123456789,"is_bot":true,...}}
```

**Verify User ID:**
```python
# In bot.py, temporarily add logging
logger.info(f"User ID from message: {update.effective_user.id}")
logger.info(f"Configured User ID: {config.TELEGRAM_USER_ID}")
```

Make sure they match!

**Fix:**
1. Restart the bot: `python bot.py`
2. Update TELEGRAM_BOT_TOKEN in `.env`
3. Update TELEGRAM_USER_ID in `.env`

---

### Issue: "Sorry, this bot is private" message

**Cause:** Your Telegram User ID doesn't match the configured ID.

**Solution:**
1. Get your User ID from [@userinfobot](https://t.me/userinfobot)
2. Update `.env`:
   ```env
   TELEGRAM_USER_ID=123456789
   ```
3. Restart bot

---

## Google Sheets Errors

### Issue: "Failed to initialize Google Sheets"

**Error message in logs:**
```
FileNotFoundError: credentials.json not found
```

**Solution:**
1. Ensure `credentials.json` is in the same folder as `bot.py`
2. Check file path:
   ```bash
   ls -la credentials.json
   ```
3. Verify `.env` setting:
   ```env
   GOOGLE_SHEETS_CREDENTIALS=credentials.json
   ```

---

### Issue: "Permission denied" error

**Error message:**
```
HttpError 403: The caller does not have permission
```

**Cause:** Service account doesn't have access to the sheet.

**Solution:**
1. Open your Google Sheet
2. Click "Share" (top right)
3. Add the service account email (from `credentials.json`):
   ```json
   "client_email": "job-tracker@project.iam.gserviceaccount.com"
   ```
4. Give **Editor** permission (not Viewer)
5. Click "Share"

---

### Issue: "Invalid sheet ID"

**Error message:**
```
HttpError 404: Requested entity was not found
```

**Solution:**
1. Get correct Sheet ID from URL:
   ```
   https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
   ```
2. Update `.env`:
   ```env
   GOOGLE_SHEET_ID=1ABC2DEF3GHI4JKL5MNO
   ```
3. Restart bot

---

### Issue: "API has not been enabled"

**Error message:**
```
HttpError 403: Google Sheets API has not been used in project
```

**Solution:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to "APIs & Services" > "Library"
4. Search "Google Sheets API"
5. Click "Enable"
6. Wait 2-3 minutes
7. Restart bot

---

## Extraction Errors

### Issue: "Failed to fetch job posting"

**Possible Causes:**
1. Website blocks bots
2. Invalid URL
3. Network timeout
4. Website requires login

**Solutions:**

**Test URL manually:**
```bash
curl -I https://example.com/job-url
```

**Try in browser:**
- If URL doesn't load in browser, bot can't scrape it

**Check if site blocks bots:**
```python
# Test with scraper.py
python scraper.py
```

**Workaround for blocked sites:**
1. Copy job text manually
2. Paste into a text file
3. Modify bot to accept text input (future feature)

---

### Issue: "Deadline not extracted"

**Message from bot:**
```
⚠️ Could not automatically detect the application deadline.
```

**Cause:** Deadline format not recognized by regex patterns.

**Solution:**

**Add custom date pattern:**

Edit `config.py`:
```python
DATE_PATTERNS = [
    # Existing patterns...
    r'your_custom_pattern_here',
]
```

**Example patterns:**
```python
# For "Valid until: DD/MM/YYYY"
r'valid\s+until[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'

# For Bengali dates
r'আবেদনের\s+শেষ\s+তারিখ[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
```

**Manual entry workaround:**
1. Job is added to sheet without deadline
2. Open Google Sheet
3. Manually enter deadline in "Deadline" column
4. Format: YYYY-MM-DD

---

### Issue: Gemini API extraction fails

**Error message:**
```
Gemini API extraction failed: Invalid API key
```

**Solution:**
1. Verify Gemini API key:
   ```env
   GEMINI_API_KEY=AIzaSy...
   ```
2. Check key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Ensure no extra spaces in `.env`
4. Restart bot

---

## Reminder Issues

### Issue: Not receiving reminders

**Possible Causes:**
1. Scheduler not running
2. Wrong timezone
3. No jobs with upcoming deadlines
4. Jobs already marked as applied

**Solutions:**

**Check scheduler status:**
```bash
# Check logs for:
"Reminder scheduler started"
```

**Verify timezone:**
```env
USER_TIMEZONE=Asia/Dhaka
```

**Test reminder manually:**
```python
# Add to bot.py for testing
from reminder import test_reminder_now
test_reminder_now(application.bot)
```

**Check jobs in sheet:**
1. Open Google Sheet
2. Verify "Deadline" column has dates
3. Check "Days Left" column is calculated
4. Ensure "Status" is not "Applied" for pending jobs

---

### Issue: Reminders at wrong time

**Cause:** Incorrect timezone configuration.

**Solution:**
1. Update `.env`:
   ```env
   USER_TIMEZONE=Asia/Dhaka
   ```
2. Available timezones: [List of timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
3. Restart bot

---

## Deployment Problems

### Issue: Railway deployment fails

**Error:** Build failed

**Solution:**
1. Check `requirements.txt` is present
2. Verify all packages are available on PyPI
3. Check Railway logs for specific error
4. Ensure Python version is specified:
   ```
   runtime.txt:
   python-3.9.0
   ```

---

### Issue: Render service keeps spinning down

**Cause:** Free tier limitation

**Solutions:**
1. **Accept limitation:** Bot will wake up when needed (30s delay)
2. **Upgrade to paid tier:** $7/month for always-on
3. **Switch to Railway:** Better free tier for bots
4. **Keep-alive trick:**
   - Add web endpoint
   - Use external service to ping every 10 minutes
   - Example: UptimeRobot

---

### Issue: PythonAnywhere "CPU quota exceeded"

**Cause:** Free tier CPU limits

**Solutions:**
1. Reduce logging verbosity:
   ```env
   LOG_LEVEL=WARNING
   ```
2. Optimize code to use less CPU
3. Upgrade to Hacker plan ($5/month)
4. Use Railway instead (better for bots)

---

## API Rate Limits

### Issue: "Rate limit exceeded" errors

**Gemini API:**
- **Limit:** 60 requests/minute
- **Solution:** Add delays between requests, cache results

**Google Sheets API:**
- **Limit:** 500 requests per 100 seconds
- **Solution:** Batch updates, use fewer API calls

**Jina AI Reader:**
- **Without key:** 1,000 requests/day
- **With key:** 10,000 requests/day
- **Solution:** Get API key if needed

**Telegram Bot API:**
- **Limit:** 30 messages/second
- **Solution:** Usually not an issue for single-user bots

---

## Common Error Messages

### "Connection timeout"

**Cause:** Network issues or slow server

**Solution:**
1. Check internet connection
2. Increase timeout in config.py:
   ```python
   REQUEST_TIMEOUT = 60  # Increase from 30
   ```
3. Try again

---

### "JSON decode error"

**Full error:**
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Cause:** Invalid JSON response from API

**Solution:**
1. Usually temporary - try again
2. Check API status (Gemini/Jina)
3. Verify API keys are correct

---

### "Module not found"

**Error:**
```
ModuleNotFoundError: No module named 'telegram'
```

**Solution:**
```bash
pip install -r requirements.txt
```

If still failing:
```bash
pip install python-telegram-bot --upgrade
```

---

## Logging and Debugging

### Enable Debug Logging

In `.env`:
```env
LOG_LEVEL=DEBUG
```

This will show detailed information about:
- API requests and responses
- Extraction attempts
- Sheet operations
- Reminder checks

### View Logs

**Local machine:**
```bash
python bot.py 2>&1 | tee bot.log
```

**Railway:**
- Dashboard > Deployments > Logs

**Render:**
- Dashboard > Logs tab

**PythonAnywhere:**
- Dashboard > Files > error.log

---

## Testing Checklist

When troubleshooting, test in this order:

1. **Bot Connection**
   ```
   - [ ] Can connect to Telegram API
   - [ ] Bot responds to /start
   - [ ] User ID is correct
   ```

2. **Google Sheets**
   ```
   - [ ] credentials.json exists
   - [ ] Sheet ID is correct
   - [ ] Service account has access
   - [ ] Sheet initializes successfully
   ```

3. **URL Processing**
   ```
   - [ ] URL validation works
   - [ ] Scraper can fetch content
   - [ ] Extractor finds deadline
   - [ ] Job saves to sheet
   ```

4. **Reminders**
   ```
   - [ ] Scheduler starts
   - [ ] Can read upcoming deadlines
   - [ ] Reminders are sent
   - [ ] Timezone is correct
   ```

---

## Getting Help

If you're still stuck:

### 1. Check Logs
Look for specific error messages and search for them.

### 2. Review Configuration
Double-check all environment variables and file paths.

### 3. Test Components Individually
```python
# Test scraper
python scraper.py

# Test extractor
python extractor.py

# Test sheets
python sheets.py
```

### 4. Open GitHub Issue

Include:
- Operating system
- Python version
- Error message (full traceback)
- Steps to reproduce
- What you've already tried

[Open Issue](https://github.com/farzana-bhuiyan-meem/job-deadline-tracker-bot/issues/new)

---

## Frequently Asked Questions

**Q: Can I use this bot for multiple users?**
A: Current version is single-user. Modify `bot.py` to remove User ID check for multi-user support.

**Q: What happens if I exceed API limits?**
A: Bot will receive error responses. Most operations will gracefully degrade or retry.

**Q: Can I run multiple bots with same credentials?**
A: Yes, but they'll share the same Google Sheet. Use different sheets for different bots.

**Q: Is my data secure?**
A: Yes - all credentials are local/private. Google Service Account has minimal permissions.

**Q: Can I customize reminder times?**
A: Yes! Edit `config.py`:
```python
REMINDER_DAYS = [5, 2, 0]  # 5 days, 2 days, day of deadline
REMINDER_TIME_HOUR = 9  # 9 AM instead of 8 AM
```

---

## Still Need Help?

- 📖 Review [README](../README.md)
- 🔑 Check [API Setup Guide](API_SETUP.md)
- 🚀 Review [Deployment Guide](DEPLOYMENT.md)
- 💬 Ask in [Discussions](https://github.com/farzana-bhuiyan-meem/job-deadline-tracker-bot/discussions)
- 🐛 Report [Bug](https://github.com/farzana-bhuiyan-meem/job-deadline-tracker-bot/issues)

---

**Remember:** Most issues are configuration-related. Double-check your API keys, credentials, and environment variables first!
