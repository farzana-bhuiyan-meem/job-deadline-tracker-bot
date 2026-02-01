"""
Automated reminder system for job deadlines.
"""

import logging
from datetime import time
from typing import TYPE_CHECKING
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
import sheets
import utils

if TYPE_CHECKING:
    from telegram import Bot

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None


def check_and_send_reminders(bot: 'Bot'):
    """
    Check for upcoming deadlines and send reminders.
    Run daily at 8 AM Bangladesh time.
    
    Args:
        bot: Telegram bot instance
    """
    logger.info("Running scheduled reminder check")
    
    if not config.TELEGRAM_USER_ID:
        logger.error("TELEGRAM_USER_ID not configured, cannot send reminders")
        return
    
    try:
        # Get all jobs with deadlines in next 3 days (covers all reminder days)
        jobs = sheets.get_upcoming_deadlines(days=max(config.REMINDER_DAYS))
        
        if not jobs:
            logger.info("No upcoming deadlines found")
            return
        
        # Group jobs by days left
        for reminder_day in config.REMINDER_DAYS:
            jobs_to_remind = [j for j in jobs if j['days_left'] == reminder_day]
            
            for job in jobs_to_remind:
                try:
                    _send_reminder(bot, job, reminder_day)
                except Exception as e:
                    logger.error(f"Failed to send reminder for {job.get('position', 'Unknown')}: {str(e)}")
        
        logger.info(f"Reminder check completed, processed {len(jobs)} jobs")
    
    except Exception as e:
        logger.error(f"Error in reminder check: {str(e)}")


def _send_reminder(bot: 'Bot', job: dict, days_left: int):
    """
    Send reminder notification for a specific job.
    
    Args:
        bot: Telegram bot instance
        job: Job dictionary
        days_left: Days until deadline
    """
    logger.info(f"Sending reminder for {job.get('position', 'Unknown')} ({days_left} days left)")
    
    # Format reminder message
    message = utils.format_reminder_message(job, days_left)
    
    # Create inline keyboard
    keyboard = []
    
    # Add "View Job" button if URL exists
    if job.get('url'):
        keyboard.append([InlineKeyboardButton("🔗 View Job", url=job['url'])])
    
    # Add action buttons
    keyboard.append([
        InlineKeyboardButton("✅ Mark Applied", callback_data=f"applied_{job.get('position', 'job')}")
    ])
    keyboard.append([
        InlineKeyboardButton("📋 All Deadlines", callback_data="list_all")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        bot.send_message(
            chat_id=config.TELEGRAM_USER_ID,
            text=message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        logger.info("Reminder sent successfully")
    except Exception as e:
        logger.error(f"Failed to send reminder message: {str(e)}")


def schedule_reminders(bot: 'Bot'):
    """
    Setup APScheduler to run reminder checks.
    
    Args:
        bot: Telegram bot instance
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    logger.info("Setting up reminder scheduler")
    
    try:
        _scheduler = BackgroundScheduler(timezone=str(config.TIMEZONE))
        
        # Schedule daily reminder check at 8 AM Bangladesh time
        trigger = CronTrigger(
            hour=config.REMINDER_TIME_HOUR,
            minute=0,
            timezone=config.TIMEZONE
        )
        
        _scheduler.add_job(
            func=lambda: check_and_send_reminders(bot),
            trigger=trigger,
            id='daily_reminder_check',
            name='Daily Reminder Check',
            replace_existing=True
        )
        
        # Also schedule daily update of days left in sheet
        _scheduler.add_job(
            func=sheets.update_days_left,
            trigger=trigger,
            id='daily_sheet_update',
            name='Daily Sheet Update',
            replace_existing=True
        )
        
        _scheduler.start()
        logger.info(f"Reminder scheduler started - will run daily at {config.REMINDER_TIME_HOUR}:00 {config.TIMEZONE}")
    
    except Exception as e:
        logger.error(f"Failed to setup reminder scheduler: {str(e)}")


def stop_scheduler():
    """Stop the reminder scheduler."""
    global _scheduler
    
    if _scheduler is not None:
        logger.info("Stopping reminder scheduler")
        _scheduler.shutdown()
        _scheduler = None


def test_reminder_now(bot: 'Bot'):
    """
    Immediately run reminder check for testing.
    
    Args:
        bot: Telegram bot instance
    """
    logger.info("Running immediate reminder test")
    check_and_send_reminders(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Reminder module loaded")
