# 🧪 Test Examples and Test Cases

Example test cases and URLs for validating the Job Deadline Tracker Bot functionality.

## Table of Contents

1. [Manual Testing Checklist](#manual-testing-checklist)
2. [Test URLs by Platform](#test-urls-by-platform)
3. [Expected Outputs](#expected-outputs)
4. [Edge Cases](#edge-cases)
5. [Performance Tests](#performance-tests)

---

## Manual Testing Checklist

### Initial Setup Tests

```
✅ Prerequisites Checklist
- [ ] Python 3.9+ installed
- [ ] All dependencies installed (requirements.txt)
- [ ] .env file configured with all keys
- [ ] credentials.json in project folder
- [ ] Google Sheet created and shared

✅ Bot Startup Tests
- [ ] Bot starts without errors
- [ ] "Bot is ready and polling" message appears
- [ ] "Sheet initialized successfully" in logs
- [ ] "Reminder scheduler started" in logs
- [ ] No error messages in console
```

---

### Command Tests

#### Test 1: /start Command

**Steps:**
1. Open Telegram
2. Find your bot
3. Send: `/start`

**Expected Output:**
```
🎯 Welcome to Job Deadline Tracker Bot! 🎯

I help you track job application deadlines automatically!

📝 How to use:
1️⃣ Send me any job posting URL
...
```

**✅ Pass Criteria:**
- Welcome message appears
- Message is properly formatted
- No error messages

---

#### Test 2: /help Command

**Steps:**
1. Send: `/help`

**Expected Output:**
```
📖 Job Deadline Tracker - Help Guide

BASIC USAGE:
Simply send me a job posting URL...
```

**✅ Pass Criteria:**
- Help text appears
- All sections visible
- Proper emoji formatting

---

#### Test 3: /list Command (Empty)

**Steps:**
1. Send: `/list` (before adding any jobs)

**Expected Output:**
```
📋 No upcoming deadlines found.

Send me a job URL to get started!
```

**✅ Pass Criteria:**
- Empty state message appears
- No errors
- Button for Google Sheet appears

---

### URL Processing Tests

#### Test 4: Valid Job URL

**Test URL (Example):**
```
https://www.indeed.com/viewjob?jk=example123
```

**Steps:**
1. Copy a real job posting URL
2. Send URL to bot

**Expected Output:**
```
⏳ Processing job posting...
⏳ Fetching job details...
⏳ Extracting job information...
⏳ Saving to Google Sheet...

✓ Job Added Successfully!

🏢 Company: [Company Name]
💼 Position: [Job Title]
📅 Deadline: [Date] (X days left)
📍 Location: [Location]
💰 Salary: [Salary if available]

🔗 Link saved to your tracker
⏰ I'll remind you 3 days before deadline
```

**✅ Pass Criteria:**
- All processing steps shown
- Job details extracted
- Confirmation message appears
- Job appears in Google Sheet
- No errors

---

#### Test 5: Invalid URL

**Test Input:**
```
not a valid url
```

**Expected Output:**
```
Please send a valid job posting URL.

Example: https://www.bdjobs.com/jobs/...

Use /help for more information.
```

**✅ Pass Criteria:**
- Error message is helpful
- No crash
- Bot still responds to other commands

---

#### Test 6: URL Without Deadline

**Steps:**
1. Send URL of job without clear deadline

**Expected Output:**
```
⚠️ Could not automatically detect the application deadline.

Please check the job posting manually and add the deadline to your Google Sheet.

Company: [Company Name]
Position: [Job Title]

The job has been added to your sheet without a deadline.
```

**✅ Pass Criteria:**
- Job still saved to sheet
- Warning message shown
- User guided to add manually

---

### Google Sheets Tests

#### Test 7: Sheet Initialization

**Steps:**
1. Start bot
2. Check Google Sheet

**Expected Output:**
- Headers created: Company, Position, Deadline, Days Left, Link, Status, Salary, Location, Added On
- Header row is bold and frozen
- Sheet is ready for data

**✅ Pass Criteria:**
- All columns present
- Proper formatting
- No errors

---

#### Test 8: Job Added to Sheet

**Steps:**
1. Send valid job URL
2. Open Google Sheet

**Expected Results:**
| Company | Position | Deadline | Days Left | Link | Status | Salary | Location | Added On |
|---------|----------|----------|-----------|------|--------|--------|----------|----------|
| Tech Co | Developer | 2026-02-15 | 14 | [URL] | Open | 50k | Dhaka | 2026-02-01 08:30 |

**✅ Pass Criteria:**
- New row added
- All fields populated
- Days Left calculated correctly
- Status is "Open"

---

#### Test 9: Mark as Applied

**Steps:**
1. Add a job (appears as row 2 in sheet)
2. Send: `/applied 1`
3. Check Google Sheet

**Expected Output:**
```
✅ Job #1 marked as applied!
```

**In Sheet:**
- Status column changes to "Applied"

**✅ Pass Criteria:**
- Confirmation message appears
- Sheet status updated
- No errors

---

### Reminder Tests

#### Test 10: Manual Reminder Check

**Steps:**
1. Add job with deadline 2 days from now
2. In bot.py, add test code:
```python
from reminder import test_reminder_now
test_reminder_now(application.bot)
```
3. Restart bot

**Expected Output:**
```
🔔 DEADLINE REMINDER

⏰ 2 days left to apply!

🏢 [Company]
💼 [Position]
📅 Deadline: [Date]
```

**✅ Pass Criteria:**
- Reminder message received
- Correct days calculation
- Inline buttons work

---

## Test URLs by Platform

### BDJobs.com

**Test URL Examples:**
```
https://www.bdjobs.com/jobs/
```

**Expected Extraction:**
- Company name
- Job position
- Deadline (if present)
- Location (usually Bangladesh)

---

### LinkedIn

**Test URL Example:**
```
https://www.linkedin.com/jobs/view/1234567890
```

**Notes:**
- May require login
- Rate limiting possible
- Fallback to BeautifulSoup

---

### Indeed

**Test URL Example:**
```
https://www.indeed.com/viewjob?jk=example123
```

**Expected Extraction:**
- Company name
- Job title
- Sometimes has deadline
- Location

---

### Facebook Jobs

**Test URL Example:**
```
https://www.facebook.com/jobs/123456789
```

**Notes:**
- May require login
- Less structured data
- Extraction may be limited

---

## Expected Outputs

### Successful Job Extraction

**Complete Example:**
```
✓ Job Added Successfully!

🏢 Company: Tech Solutions Bangladesh Ltd
💼 Position: Senior Frontend Developer (React + TypeScript)
📅 Deadline: March 15, 2026 (42 days left)
📍 Location: Dhaka, Bangladesh
💰 Salary: 60,000-80,000 BDT/month

🔗 Link saved to your tracker
⏰ I'll remind you 3 days before deadline

[📊 View Google Sheet]
```

### Partial Extraction (No Deadline)

```
✓ Job Added Successfully!

🏢 Company: Creative Agency
💼 Position: UI/UX Designer
📍 Location: Dhaka, Bangladesh

🔗 Link saved to your tracker

⚠️ Deadline not found - please add manually to Google Sheet
```

---

## Edge Cases

### Edge Case 1: Very Long Company Name

**Input:** Company name with 100+ characters

**Expected Behavior:**
- Full name saved to sheet
- Truncated in Telegram message if needed
- No crash

---

### Edge Case 2: Multiple Deadlines in Text

**Example Text:**
```
Application deadline: March 15, 2026
Interview deadline: March 20, 2026
Final decision: April 1, 2026
```

**Expected Behavior:**
- First deadline (application) is extracted
- Others ignored
- No errors

---

### Edge Case 3: Past Deadline

**Input:** Job with deadline in the past

**Expected Behavior:**
- Job added to sheet
- Days Left shows negative number
- No reminder sent
- User informed

---

### Edge Case 4: Same Job Added Twice

**Steps:**
1. Add job URL
2. Add same URL again

**Expected Behavior:**
- Both entries added (duplicates allowed)
- User can delete manually from sheet
- No crash

---

### Edge Case 5: Very Short URL

**Input:** `https://bit.ly/abcd123`

**Expected Behavior:**
- Follows redirect
- Scrapes final URL
- Extracts normally

---

### Edge Case 6: Non-English Job Posting

**Input:** Job posting in Bengali

**Expected Behavior:**
- Gemini extracts details
- Bengali text supported
- Proper encoding in sheet

---

## Performance Tests

### Test 11: Response Time

**Acceptance Criteria:**
- URL processing: < 10 seconds
- Command response: < 1 second
- Sheet update: < 3 seconds

**Test Steps:**
1. Record start time
2. Send job URL
3. Record end time when confirmation appears
4. Calculate duration

**Expected:** < 10 seconds total

---

### Test 12: Multiple Jobs Rapidly

**Steps:**
1. Send 5 different job URLs quickly (one after another)
2. Check all are processed

**Expected Behavior:**
- All jobs processed
- All saved to sheet
- No errors
- No rate limit issues

---

### Test 13: Large Job Description

**Input:** Job posting with 10,000+ word description

**Expected Behavior:**
- Text truncated for Gemini (5000 chars)
- Description summary in sheet (200 chars)
- No timeout
- Extraction successful

---

## Validation Scripts

### Script 1: Check Sheet Access

```python
import sheets

try:
    sheets.initialize_sheet()
    print("✅ Sheet access OK")
except Exception as e:
    print(f"❌ Sheet access failed: {e}")
```

---

### Script 2: Test Date Extraction

```python
import extractor

test_texts = [
    "Deadline: 15/02/2026",
    "Apply by: February 15, 2026",
    "Last date: 15.02.2026",
    "শেষ তারিখ: ১৫/০২/২০২৬"
]

for text in test_texts:
    result = extractor.extract_deadline_regex(text)
    print(f"Text: {text}")
    print(f"Result: {result}\n")
```

---

### Script 3: Test Scraper

```python
import scraper

test_urls = [
    "https://www.bdjobs.com",
    "https://www.linkedin.com/jobs",
    "https://www.indeed.com"
]

for url in test_urls:
    try:
        text = scraper.fetch_job_text(url)
        print(f"✅ {url}: {len(text)} chars fetched")
    except Exception as e:
        print(f"❌ {url}: {e}")
```

---

## Regression Tests

After making changes, verify:

- [ ] All commands still work
- [ ] URL processing works
- [ ] Google Sheets integration works
- [ ] Reminders still trigger
- [ ] No new errors in logs
- [ ] Performance hasn't degraded

---

## User Acceptance Testing

### Scenario 1: Complete User Journey

**User Story:** As a job seeker, I want to track a job deadline.

**Steps:**
1. Open Telegram, send /start to bot
2. Copy job URL from browser
3. Send URL to bot
4. Receive confirmation
5. Open Google Sheet to verify
6. Wait for reminder (or trigger manually)
7. Mark as applied using /applied 1
8. Verify status updated in sheet

**Success Criteria:**
- All steps complete without errors
- User doesn't need to read documentation
- Process feels intuitive
- Takes < 2 minutes total

---

### Scenario 2: Weekly Usage Pattern

**User Story:** As a job seeker, I add 10 jobs per week.

**Steps:**
1. Day 1: Add 3 jobs
2. Day 3: Add 4 jobs  
3. Day 5: Add 3 jobs
4. Day 7: Check /list
5. Mark 2 as applied

**Success Criteria:**
- All jobs tracked correctly
- Reminders sent appropriately
- Sheet organized and readable
- Bot remains responsive

---

## Automated Testing (Future)

Consider adding:
- Unit tests for utils.py functions
- Integration tests for sheets operations
- Mocked tests for API calls
- CI/CD pipeline with pytest

---

## Bug Reporting Template

When reporting issues, include:

```markdown
**Environment:**
- OS: [e.g., Windows 10]
- Python version: [e.g., 3.9.5]
- Deployment: [Local/Railway/Render]

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Behavior:**


**Actual Behavior:**


**Screenshots/Logs:**


**Additional Context:**

```

---

## Test Results Log

Keep track of test results:

```markdown
### Test Run: 2026-02-01

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | /start command | ✅ Pass | - |
| 2 | /help command | ✅ Pass | - |
| 3 | Valid URL | ✅ Pass | Took 8s |
| 4 | Invalid URL | ✅ Pass | Error handled |
| 5 | Sheet update | ✅ Pass | - |
| ... | ... | ... | ... |
```

---

**Note:** These are manual test cases. For production use, consider implementing automated testing with pytest, unittest, or similar frameworks.
