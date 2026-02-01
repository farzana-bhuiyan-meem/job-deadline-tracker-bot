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
1️⃣ Send me any job posting URL
2️⃣ I'll extract the details and deadline
3️⃣ I'll save it to your Google Sheet
4️⃣ I'll remind you before the deadline!

🔗 **Supported platforms:**
• BDJobs.com
• LinkedIn
• Indeed
• Facebook Jobs
• Bdjobs24.com
• Chakri.com
• And many more!

⏰ **Reminders:**
• 3 days before deadline
• 1 day before deadline
• Morning of deadline (8 AM)

📋 **Commands:**
/help - Show this guide
/list - View upcoming deadlines
/applied [number] - Mark job as applied

Just send me a job URL to get started! 🚀
"""
    
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    logger.info(f"User {update.effective_user.id} requested help")
    
    help_message = """
📖 **Job Deadline Tracker - Help Guide**

**BASIC USAGE:**
Simply send me a job posting URL and I'll do the rest!

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
• Works with most job posting websites
• Just paste the URL, no need to type anything else
• Reminders stop after deadline or when marked as applied
• All data is saved in your private Google Sheet

Need help? Just send me a job URL to see it in action! 💼
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


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URL messages."""
    logger.info(f"User {update.effective_user.id} sent a message")
    
    # Security check
    if config.TELEGRAM_USER_ID and str(update.effective_user.id) != config.TELEGRAM_USER_ID:
        await update.message.reply_text("Sorry, this bot is private.")
        return
    
    message_text = update.message.text.strip()
    
    # Check if message contains a URL
    if not utils.is_valid_url(message_text):
        await update.message.reply_text(
            "Please send a valid job posting URL.\n\n"
            "Example: https://www.bdjobs.com/jobs/...\n\n"
            "Use /help for more information."
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Processing job posting...\nThis may take a few seconds.")
    
    try:
        # Step 1: Scrape the URL
        logger.info(f"Scraping URL: {message_text}")
        await processing_msg.edit_text("⏳ Fetching job details...")
        
        try:
            job_text = scraper.fetch_job_text(message_text)
        except scraper.ScraperError as e:
            logger.error(f"Scraper error: {str(e)}")
            await processing_msg.edit_text(
                "❌ Failed to fetch job posting.\n\n"
                "Possible reasons:\n"
                "• Website blocks automated access\n"
                "• Invalid or expired URL\n"
                "• Network timeout\n\n"
                "Please try a different URL or check if the link works in your browser."
            )
            return
        
        # Step 2: Extract job details
        logger.info("Extracting job details")
        await processing_msg.edit_text("⏳ Extracting job information...")
        
        job_data = extractor.extract_job_details(message_text, job_text)
        
        # Check if deadline was found
        if not job_data.get('deadline'):
            await processing_msg.edit_text(
                "⚠️ Could not automatically detect the application deadline.\n\n"
                "Please check the job posting manually and add the deadline to your Google Sheet.\n\n"
                f"Company: {job_data.get('company', 'Unknown')}\n"
                f"Position: {job_data.get('position', 'Unknown')}\n\n"
                "The job has been added to your sheet without a deadline."
            )
        
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
    
    except Exception as e:
        logger.error(f"Unexpected error processing URL: {str(e)}", exc_info=True)
        await processing_msg.edit_text(
            "❌ An unexpected error occurred.\n\n"
            "Please try again or contact support if the problem persists."
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
    
    # Add message handler for URLs
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
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
