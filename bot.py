"""
Main Telegram bot for Job Deadline Tracker.
"""

import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
import config
import utils
import scraper
import extractor
import sheets
import reminder

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL),
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    logger.info(f"User {update.effective_user.id} started the bot")
    
    # Security check
    if config.TELEGRAM_USER_ID and str(update.effective_user.id) != config.TELEGRAM_USER_ID:
        await update.message.reply_text("Sorry, this bot is private.")
        return
    
    welcome_message = """
🎯 Welcome to Job Deadline Tracker Bot! 🎯

I help you track job application deadlines automatically!

📝 **How to use:**

**Method 1: Send Job URL** 🔗
Just send me any job posting link from BDJobs, LinkedIn, Indeed, Facebook Jobs, or any job portal.

**Method 2: Paste Job Description** 📋
Copy the entire job posting text and send it to me.
I'll extract all the details automatically!

**What I extract:**
• Company name
• Job position
• Application deadline
• Salary range
• Location
• And more!

📊 **Features:**
✅ Automatic save to Google Sheets
✅ Smart reminders (3 days, 1 day, deadline day)
✅ Color-coded urgency tracking
✅ Mark jobs as applied

📋 **Commands:**
/help - Show detailed guide
/list - View upcoming deadlines
/applied [number] - Mark job as applied

Just send me a job URL or paste the job description to get started! 🚀
"""
    
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    logger.info(f"User {update.effective_user.id} requested help")
    
    help_message = """
📚 **How to Use Job Deadline Tracker Bot**

**Method 1: Send Job URL** 🔗
Just send me any job posting link from:
• BDJobs, LinkedIn, Indeed
• Company websites
• Facebook Jobs (if accessible)
• Any job portal

**Method 2: Paste Job Description** 📝
Copy the entire job posting text and send it to me.
I'll extract all the details automatically!

**Method 3: Mixed** 🔗📝
Send the URL followed by the job description text
(useful when the URL is hard to scrape)

**COMMANDS:**

/start - Welcome message
/help - Show this help guide
/list - Show all upcoming deadlines
/applied [number] - Mark a job as applied
  Example: /applied 1

**FEATURES:**

🔍 **Automatic Extraction:**
I automatically extract:
• Company name
• Job position
• Application deadline
• Salary range (if available)
• Location
• Job description

📊 **Google Sheets:**
All jobs are saved to your Google Sheet with:
• Color coding (red/yellow/green by urgency)
• Days left calculation
• Status tracking

⏰ **Smart Reminders:**
I'll remind you:
• 3 days before deadline
• 1 day before deadline  
• Morning of deadline day (8 AM)

**TIPS:**
• If a URL is hard to scrape (like Facebook), just paste the job text directly
• Works with Bengali text too
• Reminders stop after deadline or when marked as applied
• All data is saved in your private Google Sheet

Just send me a job link or paste the job description! 💼
"""
    
    await update.message.reply_text(help_message)


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command."""
    logger.info(f"User {update.effective_user.id} requested deadline list")
    
    # Security check
    if config.TELEGRAM_USER_ID and str(update.effective_user.id) != config.TELEGRAM_USER_ID:
        await update.message.reply_text("Sorry, this bot is private.")
        return
    
    try:
        # Get upcoming deadlines (next 30 days)
        jobs = sheets.get_upcoming_deadlines(days=30)
        
        message = utils.format_deadline_list(jobs)
        
        # Add button to view Google Sheet
        keyboard = []
        if config.GOOGLE_SHEET_ID:
            sheet_url = f"https://docs.google.com/spreadsheets/d/{config.GOOGLE_SHEET_ID}"
            keyboard.append([InlineKeyboardButton("📊 View Google Sheet", url=sheet_url)])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        await update.message.reply_text(message, reply_markup=reply_markup)
    
    except Exception as e:
        logger.error(f"Error in list command: {str(e)}")
        await update.message.reply_text("❌ Failed to retrieve deadline list. Please try again.")


async def applied_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /applied command."""
    logger.info(f"User {update.effective_user.id} used applied command")
    
    # Security check
    if config.TELEGRAM_USER_ID and str(update.effective_user.id) != config.TELEGRAM_USER_ID:
        await update.message.reply_text("Sorry, this bot is private.")
        return
    
    # Parse job number from command
    if not context.args:
        await update.message.reply_text("Please specify a job number. Example: /applied 1")
        return
    
    job_number = utils.parse_job_number(context.args[0])
    
    if not job_number:
        await update.message.reply_text("Invalid job number. Please use a valid number.")
        return
    
    try:
        success = sheets.mark_as_applied(job_number)
        
        if success:
            await update.message.reply_text(f"✅ Job #{job_number} marked as applied!")
        else:
            await update.message.reply_text(f"❌ Failed to mark job #{job_number} as applied. Please check the number.")
    
    except Exception as e:
        logger.error(f"Error in applied command: {str(e)}")
        await update.message.reply_text("❌ An error occurred. Please try again.")


async def process_job_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, processing_msg):
    """
    Process a job URL by scraping and extracting details.
    
    Args:
        update: Telegram update object
        context: Telegram context object
        url: Job posting URL
        processing_msg: Processing message to update
    """
    try:
        # Step 1: Scrape the URL
        logger.info(f"Scraping URL: {url}")
        await processing_msg.edit_text("⏳ Fetching job details from URL...")
        
        scrape_result = scraper.fetch_job_text(url)
        
        # Check if scraping failed
        if not scrape_result['success']:
            logger.warning(f"Scraping failed for URL: {url}")
            await processing_msg.edit_text(
                f"⚠️ {scrape_result['error']}\n\n"
                "💡 **Alternative:** Copy and paste the job description text, "
                "and I'll extract the details for you!"
            )
            return
        
        job_text = scrape_result['text']
        
        # Step 2: Extract job details
        logger.info("Extracting job details from scraped text")
        await processing_msg.edit_text("⏳ Extracting job information...")
        
        job_data = extractor.extract_job_details(job_text, url)
        
        # Step 3: Save and confirm
        await save_and_confirm_job(update, context, job_data, processing_msg)
    
    except Exception as e:
        logger.error(f"Error processing job URL: {str(e)}", exc_info=True)
        await processing_msg.edit_text(
            "❌ An unexpected error occurred while processing the URL.\n\n"
            "Please try again or paste the job description text directly."
        )


async def process_job_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, url: str, processing_msg):
    """
    Process job description text directly (without URL scraping).
    
    Args:
        update: Telegram update object
        context: Telegram context object
        text: Job description text
        url: Job posting URL (optional, may be None)
        processing_msg: Processing message to update
    """
    try:
        # Extract job details from text
        logger.info("Extracting job details from pasted text")
        await processing_msg.edit_text("⏳ Extracting job information from text...")
        
        job_data = extractor.extract_job_details(text, url)
        
        # Save and confirm
        await save_and_confirm_job(update, context, job_data, processing_msg)
    
    except Exception as e:
        logger.error(f"Error processing job text: {str(e)}", exc_info=True)
        await processing_msg.edit_text(
            "❌ An unexpected error occurred while processing the job description.\n\n"
            "Please try again or check the text format."
        )


async def handle_missing_fields(update: Update, context: ContextTypes.DEFAULT_TYPE, extracted_data: dict, url: str = None, job_text: str = None):
    """
    Handle missing fields by asking user for input.
    
    Args:
        update: Telegram update
        context: Bot context
        extracted_data: Partially extracted job data
        url: Job URL (optional)
        job_text: Job description text (optional)
    """
    missing_fields = []
    
    # Check critical fields
    if not extracted_data.get('company'):
        missing_fields.append('company')
    if not extracted_data.get('position'):
        missing_fields.append('position')
    if not extracted_data.get('deadline'):
        missing_fields.append('deadline')
    
    if not missing_fields:
        # All critical fields present, save the job
        await save_job_to_sheet(update, context, extracted_data, url)
        return
    
    # Store data in context for later
    context.user_data['pending_job'] = {
        'extracted_data': extracted_data,
        'url': url,
        'job_text': job_text,
        'missing_fields': missing_fields,
        'current_field': 0
    }
    
    # Ask for first missing field
    field_name = missing_fields[0]
    field_prompts = {
        'company': "What is the **company name**?",
        'position': "What is the **job position/title**?",
        'deadline': "What is the **application deadline**? (e.g., Feb 15, 2026)"
    }
    
    await update.message.reply_text(
        f"⚠️ I couldn't extract the {field_name} from the job posting.\n\n"
        f"{field_prompts[field_name]}\n\n"
        f"Please reply with the {field_name}."
    )


async def handle_field_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user's response to missing field questions.
    
    Returns:
        True if message was a field response, False otherwise
    """
    if 'pending_job' not in context.user_data:
        return False  # Not in field collection mode
    
    pending = context.user_data['pending_job']
    missing_fields = pending['missing_fields']
    current_index = pending['current_field']
    
    if current_index >= len(missing_fields):
        return False  # Already done
    
    # Get user's response
    user_response = update.message.text.strip()
    current_field = missing_fields[current_index]
    
    # Store the field value with appropriate parsing
    if current_field == 'deadline':
        # Parse deadline input to datetime
        try:
            import dateparser
            deadline = dateparser.parse(
                user_response,
                settings={
                    'TIMEZONE': str(config.TIMEZONE),
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'PREFER_DATES_FROM': 'future'
                }
            )
            if deadline:
                pending['extracted_data'][current_field] = deadline
            else:
                # If parsing fails, store as string and let user know
                pending['extracted_data'][current_field] = user_response
                logger.warning(f"Could not parse deadline: {user_response}")
        except Exception as e:
            logger.warning(f"Error parsing deadline: {e}")
            pending['extracted_data'][current_field] = user_response
    else:
        # For other fields, store as-is
        pending['extracted_data'][current_field] = user_response
    
    # Move to next field
    current_index += 1
    pending['current_field'] = current_index
    
    if current_index < len(missing_fields):
        # Ask for next field
        next_field = missing_fields[current_index]
        field_prompts = {
            'company': "What is the **company name**?",
            'position': "What is the **job position/title**?",
            'deadline': "What is the **application deadline**? (e.g., Feb 15, 2026)"
        }
        
        await update.message.reply_text(
            f"✓ Got it!\n\n"
            f"{field_prompts[next_field]}\n\n"
            f"Please reply with the {next_field}."
        )
        return True
    else:
        # All fields collected, save the job
        await update.message.reply_text("✓ All information collected! Saving job...")
        
        extracted_data = pending['extracted_data']
        url = pending.get('url')
        
        # Clear pending data
        del context.user_data['pending_job']
        
        # Save to sheet
        await save_job_to_sheet(update, context, extracted_data, url)
        return True


async def save_job_to_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE, job_data: dict, url: str = None):
    """
    Save job to Google Sheets and send confirmation message.
    
    Args:
        update: Telegram update
        context: Bot context
        job_data: Job data dictionary
        url: Job URL (optional)
    """
    # Ensure URL is in job data
    if url and 'url' not in job_data:
        job_data['url'] = url
    
    # Add extraction timestamp if not present
    if 'added_on' not in job_data:
        from datetime import datetime
        job_data['added_on'] = datetime.now(config.TIMEZONE)
    
    # Save to Google Sheets
    logger.info("Saving to Google Sheet")
    success = sheets.add_job(job_data)
    
    if not success:
        await update.message.reply_text(
            "❌ Failed to save to Google Sheet.\n\n"
            "Please check your Google Sheets configuration."
        )
        return
    
    # Send confirmation
    logger.info("Job processed successfully")
    
    confirmation_message = utils.format_job_message(job_data)
    
    # Create inline keyboard
    keyboard = []
    if config.GOOGLE_SHEET_ID:
        sheet_url = f"https://docs.google.com/spreadsheets/d/{config.GOOGLE_SHEET_ID}"
        keyboard.append([InlineKeyboardButton("📊 View Google Sheet", url=sheet_url)])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(confirmation_message, reply_markup=reply_markup)


async def save_and_confirm_job(update: Update, context: ContextTypes.DEFAULT_TYPE, job_data: dict, processing_msg):
    """
    Save job to Google Sheets and send confirmation message.
    
    Args:
        update: Telegram update object
        context: Telegram context object
        job_data: Extracted job data dictionary
        processing_msg: Processing message to update
    """
    # Check if critical fields are missing
    has_company = job_data.get('company') not in [None, '']
    has_position = job_data.get('position') not in [None, '']
    has_deadline = job_data.get('deadline') is not None
    
    # If critical fields are missing, ask user for them
    if not has_company or not has_position:
        logger.warning("Critical fields missing in extraction")
        await processing_msg.edit_text(
            "⚠️ I had trouble extracting some information from the job posting."
        )
        # Trigger missing field handler
        await handle_missing_fields(
            update, 
            context, 
            job_data, 
            job_data.get('url'),
            None  # We don't have the original text here
        )
        return
    
    # If only deadline is missing, mention it but proceed
    if not has_deadline:
        logger.info("No deadline found in extraction")
    
    # Step 3: Save to Google Sheets
    logger.info("Saving to Google Sheet")
    await processing_msg.edit_text("⏳ Saving to Google Sheet...")
    
    success = sheets.add_job(job_data)
    
    if not success:
        await processing_msg.edit_text(
            "❌ Failed to save to Google Sheet.\n\n"
            "Please check your Google Sheets configuration."
        )
        return
    
    # Step 4: Send confirmation
    logger.info("Job processed successfully")
    
    confirmation_message = utils.format_job_message(job_data)
    
    # Create inline keyboard
    keyboard = []
    if config.GOOGLE_SHEET_ID:
        sheet_url = f"https://docs.google.com/spreadsheets/d/{config.GOOGLE_SHEET_ID}"
        keyboard.append([InlineKeyboardButton("📊 View Google Sheet", url=sheet_url)])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await processing_msg.edit_text(confirmation_message, reply_markup=reply_markup)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages - URLs or text job descriptions."""
    logger.info(f"User {update.effective_user.id} sent a message")
    
    # Security check
    if config.TELEGRAM_USER_ID and str(update.effective_user.id) != config.TELEGRAM_USER_ID:
        await update.message.reply_text("Sorry, this bot is private.")
        return
    
    # Check if we're collecting missing fields
    if await handle_field_response(update, context):
        return  # Message was a field response, handled
    
    message_text = update.message.text.strip()
    
    # Check if message contains a URL
    url = utils.extract_url(message_text)
    
    # Detect if message looks like a job description
    is_job_description = utils.detect_job_description(message_text)
    
    logger.info(f"URL detected: {url is not None}, Job description detected: {is_job_description}")
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Processing job posting...\nThis may take a few seconds.")
    
    # Determine processing mode
    if url and not is_job_description:
        # URL only - scrape it
        logger.info("Processing as URL-only")
        await process_job_url(update, context, url, processing_msg)
    elif is_job_description:
        # Text job description (with or without URL)
        # Use the text directly for extraction
        logger.info("Processing as job description text")
        await process_job_text(update, context, message_text, url, processing_msg)
    else:
        # Not a URL or job description
        await processing_msg.edit_text(
            "Please send me a job posting URL or paste the job description text.\n\n"
            "💡 **Examples:**\n"
            "• Send a URL: https://www.bdjobs.com/jobs/...\n"
            "• Paste job text: Copy the entire job posting and send it to me\n\n"
            "Use /help for more information."
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks."""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"Callback query: {query.data}")
    
    if query.data == "list_all":
        # Show deadline list
        try:
            jobs = sheets.get_upcoming_deadlines(days=30)
            message = utils.format_deadline_list(jobs)
            
            keyboard = []
            if config.GOOGLE_SHEET_ID:
                sheet_url = f"https://docs.google.com/spreadsheets/d/{config.GOOGLE_SHEET_ID}"
                keyboard.append([InlineKeyboardButton("📊 View Google Sheet", url=sheet_url)])
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            await query.message.reply_text(message, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error showing deadline list: {str(e)}")
            await query.message.reply_text("❌ Failed to retrieve deadlines.")
    
    elif query.data.startswith("applied_"):
        # Mark job as applied (simplified version)
        await query.message.reply_text(
            "To mark a job as applied, use:\n/applied [number]\n\nExample: /applied 1"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)


def main():
    """Main function to run the bot."""
    logger.info("Starting Job Deadline Tracker Bot")
    
    # Validate configuration
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        sys.exit(1)
    
    if not config.GOOGLE_SHEET_ID:
        logger.warning("GOOGLE_SHEET_ID not set - sheet integration will not work")
    
    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set - AI extraction will not work")
    
    try:
        # Initialize Google Sheets
        logger.info("Initializing Google Sheets")
        sheets.initialize_sheet()
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets: {str(e)}")
        logger.warning("Continuing without Google Sheets integration")
    
    # Create application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("applied", applied_command))
    
    # Add message handler for URLs and text job descriptions
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Setup reminder scheduler
    logger.info("Setting up reminder scheduler")
    try:
        reminder.schedule_reminders(application.bot)
    except Exception as e:
        logger.error(f"Failed to setup reminders: {str(e)}")
        logger.warning("Continuing without reminder system")
    
    # Start the bot
    logger.info("Bot is ready and polling for updates")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        reminder.stop_scheduler()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
