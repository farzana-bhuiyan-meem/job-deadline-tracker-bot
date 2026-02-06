"""
Configuration constants and settings for the Job Deadline Tracker Bot.
"""

import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_USER_ID = os.getenv('TELEGRAM_USER_ID')

# Ollama Configuration (Local LLM)
OLLAMA_MODEL = 'llama3.2'  # Model to use for extraction
OLLAMA_HOST = 'http://localhost:11434'  # Default Ollama server

# Jina AI Reader
JINA_API_KEY = os.getenv('JINA_API_KEY', '')
JINA_READER_URL = 'https://r.jina.ai/'

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS', 'credentials.json')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')

# Timezone Configuration
USER_TIMEZONE_STR = os.getenv('USER_TIMEZONE', 'Asia/Dhaka')
TIMEZONE = pytz.timezone(USER_TIMEZONE_STR)

# Reminder Configuration
REMINDER_DAYS = [3, 1, 0]  # Days before deadline to send reminders
REMINDER_TIME_HOUR = 8  # 8 AM Bangladesh time

# Date Regex Patterns for deadline extraction
DATE_PATTERNS = [
    r'deadline[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    r'apply\s+by[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
    r'apply\s+by[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
    r'last\s+date[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    r'application\s+deadline[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    r'applications\s+close\s+on[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
    r'close\s+date[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    r'শেষ\s+তারিখ[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',  # Bengali for "last date"
    r'due\s+date[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    r'expires[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    r'valid\s+till[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
]

# Google Sheets Column Headers
SHEET_HEADERS = [
    'Company',
    'Position',
    'Deadline',
    'Days Left',
    'Link',
    'Status',
    'Salary',
    'Location',
    'Added On'
]

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# Maximum job description length in sheet
MAX_DESCRIPTION_LENGTH = 200
