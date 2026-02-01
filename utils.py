"""
Helper utility functions for the Job Deadline Tracker Bot.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict
from urllib.parse import urlparse
import config


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def calculate_days_left(deadline: datetime) -> int:
    """
    Calculate days until deadline.
    
    Args:
        deadline: Deadline datetime object
        
    Returns:
        Number of days until deadline (negative if passed)
    """
    now = datetime.now(config.TIMEZONE)
    if deadline.tzinfo is None:
        deadline = config.TIMEZONE.localize(deadline)
    
    delta = deadline - now
    return delta.days


def format_job_message(job_data: Dict) -> str:
    """
    Format job data into pretty Telegram message.
    
    Args:
        job_data: Dictionary containing job information
        
    Returns:
        Formatted message string
    """
    company = job_data.get('company', 'Unknown Company')
    position = job_data.get('position', 'Unknown Position')
    deadline = job_data.get('deadline')
    salary = job_data.get('salary')
    location = job_data.get('location')
    url = job_data.get('url')
    
    # Build message
    message = "✅ **Job Added Successfully!**\n\n"
    
    message += f"🏢 **Company:** {company}\n"
    message += f"💼 **Position:** {position}\n"
    
    if deadline:
        deadline_str = deadline.strftime('%B %d, %Y') if hasattr(deadline, 'strftime') else str(deadline)
        days_left = calculate_days_left(deadline) if hasattr(deadline, 'strftime') else None
        message += f"📅 **Deadline:** {deadline_str}"
        if days_left is not None:
            message += f" ({days_left} days left)"
        message += "\n"
    else:
        message += "📅 **Deadline:** Not specified\n"
    
    if salary:
        message += f"💰 **Salary:** {salary}\n"
    
    if location:
        message += f"📍 **Location:** {location}\n"
    
    if url:
        message += f"🔗 **Apply:** {url}\n"
    else:
        message += "⚠️ **Note:** No application link available\n"
    
    message += "\n✨ Saved to your Google Sheet!"
    
    return message


def format_reminder_message(job_data: Dict, days_left: int) -> str:
    """
    Format reminder notification message.
    
    Args:
        job_data: Dictionary containing job information
        days_left: Days until deadline
        
    Returns:
        Formatted reminder message
    """
    if days_left == 0:
        header = "🔔 DEADLINE TODAY!"
        time_msg = "⏰ Apply today!"
    elif days_left == 1:
        header = "🔔 DEADLINE REMINDER"
        time_msg = "⏰ 1 day left to apply!"
    else:
        header = "🔔 DEADLINE REMINDER"
        time_msg = f"⏰ {days_left} days left to apply!"
    
    message_parts = [header, "", time_msg, ""]
    
    if job_data.get('company'):
        message_parts.append(f"🏢 {job_data['company']}")
    
    if job_data.get('position'):
        message_parts.append(f"💼 {job_data['position']}")
    
    if job_data.get('deadline'):
        deadline_str = job_data['deadline']
        if isinstance(job_data['deadline'], datetime):
            deadline_str = job_data['deadline'].strftime('%B %d, %Y')
        message_parts.append(f"📅 Deadline: {deadline_str}")
    
    return "\n".join(message_parts)


def format_deadline_list(jobs: list) -> str:
    """
    Format list of jobs with deadlines.
    
    Args:
        jobs: List of job dictionaries
        
    Returns:
        Formatted list message
    """
    if not jobs:
        return "📋 No upcoming deadlines found.\n\nSend me a job URL to get started!"
    
    message_parts = ["📋 Your Upcoming Deadlines\n"]
    
    for idx, job in enumerate(jobs, 1):
        company = job.get('company', 'Unknown Company')
        position = job.get('position', 'Unknown Position')
        deadline = job.get('deadline', 'No deadline')
        status = job.get('status', 'Open')
        days_left = job.get('days_left', 0)
        
        status_icon = "✓" if status == "Applied" else ""
        
        if isinstance(deadline, datetime):
            deadline_str = deadline.strftime('%b %d, %Y')
            message_parts.append(
                f"{idx}️⃣ {position} @ {company}\n"
                f"   📅 {deadline_str} ({days_left} days) - {status} {status_icon}\n"
            )
        else:
            message_parts.append(
                f"{idx}️⃣ {position} @ {company}\n"
                f"   📅 {deadline} - {status} {status_icon}\n"
            )
    
    return "\n".join(message_parts)


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text by removing extra whitespace and limiting length.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length (optional)
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text


def parse_job_number(text: str) -> Optional[int]:
    """
    Parse job number from user input.
    
    Args:
        text: User input text
        
    Returns:
        Job number or None if invalid
    """
    try:
        # Extract number from text
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
    except Exception:
        pass
    return None


def get_current_time() -> datetime:
    """
    Get current time in configured timezone.
    
    Returns:
        Current datetime with timezone
    """
    return datetime.now(config.TIMEZONE)


def extract_url(text: str) -> Optional[str]:
    """
    Extract URL from text if present.
    
    Args:
        text: Text that may contain a URL
        
    Returns:
        URL string or None if not found
    """
    # URL detection pattern that avoids trailing punctuation
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(url_pattern, text)
    if match:
        url = match.group(0)
        # Remove common trailing punctuation if present
        url = url.rstrip('.,;:!?)')
        return url
    return None


def detect_job_description(text: str) -> bool:
    """
    Detect if text looks like a job description.
    
    Args:
        text: Text to analyze
        
    Returns:
        True if text appears to be a job description, False otherwise
    """
    # Job-related keywords that indicate a job description
    job_keywords = [
        'job title', 'position', 'company', 'responsibilities', 
        'requirements', 'qualifications', 'salary', 'apply',
        'deadline', 'hiring', 'vacancy', 'career', 'role',
        'work experience', 'education', 'skills required',
        'employment', 'job description', 'compensation',
        'benefits', 'workplace', 'office', 'intern', 'internship'
    ]
    
    text_lower = text.lower()
    keyword_count = sum(1 for keyword in job_keywords if keyword in text_lower)
    
    # If text is >100 chars and has 3+ job keywords, likely a job description
    return len(text) > 100 and keyword_count >= 3
