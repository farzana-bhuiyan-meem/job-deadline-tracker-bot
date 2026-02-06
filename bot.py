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

# Constants for user input matching
# Keywords that indicate user wants to skip providing URL (exact match only for clarity)
# Note: 'n' is included as a common shorthand, but requires exact match to avoid false positives
SKIP_URL_KEYWORDS = ['no', 'skip', 'none', 'no link', 'nope', 'na', 'n/a', 'n']

# Default values for missing job data
DEFAULT_COMPANY = 'Unknown Company'
DEFAULT_POSITION = 'Unknown Position'


def _is_field_present(value, default_value):
    """
    Check if a field has a meaningful value.
    
    Args:
        value: The field value to check
        default_value: The default value for this field
        
    Returns:
        True if field has a meaningful value, False otherwise
    """
    return value not in [None, default_value, '']


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
            
            # Store URL in context so we can use it when user sends text
            context.user_data['pending_url'] = url
            context.user_data['waiting_for_job_text'] = True
            
            await processing_msg.edit_text(
                f"⚠️ {scrape_result['error']}\n\n"
                "💡 **No problem!** Please copy and paste the job description text, "
                "and I'll extract the details while keeping this URL for applying later.\n\n"
                "📋 Just send me the job posting text now."
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
        
        # If no URL was provided, ask the user for it
        if not url:
            logger.info("No URL provided with job text, asking user")
            
            # Store job data in context
            context.user_data['pending_job_data'] = job_data
            context.user_data['waiting_for_job_url'] = True
            
            await processing_msg.edit_text(
                "✅ Job details extracted!\n\n"
                "📎 Do you have the job posting URL/link?\n"
                "This will help you apply to the job later.\n\n"
                "Please send:\n"
                "• The job URL/link, OR\n"
                "• Reply 'no' or 'skip' if you don't have it"
            )
            return
        
        # URL was provided, save directly
        await save_and_confirm_job(update, context, job_data, processing_msg)
    
    except Exception as e:
        logger.error(f"Error processing job text: {str(e)}", exc_info=True)
        await processing_msg.edit_text(
            "❌ An unexpected error occurred while processing the job description.\n\n"
            "Please try again or check the text format."
        )


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
    # Only require at least ONE of company or position (not both)
    has_company = _is_field_present(job_data.get('company'), DEFAULT_COMPANY)
    has_position = _is_field_present(job_data.get('position'), DEFAULT_POSITION)
    
    # Track if we need to warn the user about missing critical fields
    warn_user_about_fields = False
    
    if not has_company and not has_position:
        # Neither company nor position found - will warn user after saving
        logger.warning("Both company and position missing in extraction")
        warn_user_about_fields = True
    elif not has_company or not has_position:
        # Only one is missing - that's okay, just log it
        logger.info(f"Missing: {'company' if not has_company else 'position'} (this is fine)")
    
    # Deadline is completely optional - don't mention it
    if not job_data.get('deadline'):
        logger.info("No deadline found (this is normal and okay)")
    
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
    
    # Add warning about missing fields if needed
    if warn_user_about_fields:
        sheet_text = "in your Google Sheet" if config.GOOGLE_SHEET_ID else "in your tracker"
        confirmation_message += f"\n\n⚠️ **Note:** Company and position were not found. Please update '{DEFAULT_COMPANY}' and '{DEFAULT_POSITION}' {sheet_text}."
    
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
    
    # NEW: Check if we're waiting for job text after a failed URL scrape
    if context.user_data.get('waiting_for_job_text'):
        pending_url = context.user_data.get('pending_url')
        message_text = update.message.text.strip()
        
        # Clear the waiting state
        context.user_data['waiting_for_job_text'] = False
        context.user_data['pending_url'] = None
        
        logger.info(f"Received job text for previously failed URL: {pending_url}")
        
        # Process the text with the saved URL
        processing_msg = await update.message.reply_text("⏳ Processing job details from your text...")
        await process_job_text(update, context, message_text, pending_url, processing_msg)
        return
    
    # NEW: Check if we're waiting for URL after text extraction
    if context.user_data.get('waiting_for_job_url'):
        pending_job_data = context.user_data.get('pending_job_data')
        message_text = update.message.text.strip()
        
        # Clear waiting state
        context.user_data['waiting_for_job_url'] = False
        context.user_data['pending_job_data'] = None
        
        # Check if user wants to skip providing URL
        # Only check for exact matches to avoid false positives
        message_lower = message_text.lower()
        wants_to_skip = message_lower in SKIP_URL_KEYWORDS
        
        if wants_to_skip:
            logger.info("User skipped providing URL")
            processing_msg = await update.message.reply_text("✅ Saving job without URL...")
            await save_and_confirm_job(update, context, pending_job_data, processing_msg)
            return
        
        # Try to extract URL from message
        provided_url = utils.extract_url(message_text)
        
        if provided_url:
            logger.info(f"User provided URL: {provided_url}")
            pending_job_data['url'] = provided_url
            processing_msg = await update.message.reply_text("✅ Saving job with URL...")
            await save_and_confirm_job(update, context, pending_job_data, processing_msg)
            return
        else:
            # Not a valid URL
            logger.warning("User provided text is not a valid URL")
            await update.message.reply_text(
                "⚠️ That doesn't look like a valid URL.\n\n"
                "Saving the job without a link..."
            )
            processing_msg = await update.message.reply_text("⏳ Saving job...")
            await save_and_confirm_job(update, context, pending_job_data, processing_msg)
            return
    
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
    
    # Note: OLLAMA_AVAILABLE is checked in extractor.py
    # Bot will fall back to regex-only extraction if Ollama is not available
    logger.info("AI extraction will use Ollama if available, otherwise regex patterns")
    
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
