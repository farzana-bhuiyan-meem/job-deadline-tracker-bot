"""
Job detail extraction using regex patterns and Google Gemini API.
"""

import logging
import re
import json
import traceback
from datetime import datetime
from typing import Optional, Dict
import dateparser
import config

# Default values for missing job data
DEFAULT_COMPANY = 'Unknown Company'
DEFAULT_POSITION = 'Unknown Position'

# Import Gemini API with warning suppression
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None

logger = logging.getLogger(__name__)

# Configure Gemini API
if genai and config.GEMINI_API_KEY:
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Failed to configure Gemini API: {e}")


def extract_deadline_regex(text: str) -> Optional[datetime]:
    """
    Extract deadline using regex patterns and dateparser.
    Handles multiple date formats.
    
    Args:
        text: Job posting text
        
    Returns:
        Datetime object or None if not found
    """
    logger.info("Attempting to extract deadline using regex patterns")
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Try each pattern
    for pattern in config.DATE_PATTERNS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        
        if matches:
            logger.info(f"Found potential date match: {matches[0]}")
            
            # Parse the date using dateparser
            try:
                deadline = dateparser.parse(
                    matches[0],
                    settings={
                        'TIMEZONE': str(config.TIMEZONE),
                        'RETURN_AS_TIMEZONE_AWARE': True,
                        'PREFER_DATES_FROM': 'future'
                    }
                )
                
                if deadline:
                    logger.info(f"Successfully parsed deadline: {deadline}")
                    return deadline
            except Exception as e:
                logger.warning(f"Failed to parse date '{matches[0]}': {str(e)}")
                continue
    
    # Additional attempt: look for standalone dates
    logger.info("Trying to find standalone dates in text")
    date_only_patterns = [
        r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b',
        r'\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})\b',
        r'\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b',
    ]
    
    for pattern in date_only_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        
        if matches:
            for match in matches:
                try:
                    deadline = dateparser.parse(
                        match,
                        settings={
                            'TIMEZONE': str(config.TIMEZONE),
                            'RETURN_AS_TIMEZONE_AWARE': True,
                            'PREFER_DATES_FROM': 'future'
                        }
                    )
                    
                    if deadline:
                        # Only accept if date is in the future
                        now = datetime.now(config.TIMEZONE)
                        if deadline > now:
                            logger.info(f"Found future date: {deadline}")
                            return deadline
                except Exception as e:
                    logger.warning(f"Failed to parse standalone date '{match}': {str(e)}")
                    continue
    
    logger.info("No deadline found using regex patterns")
    return None


def _extract_company(model, text: str) -> str:
    """Extract company name using focused prompt."""
    prompt = f"""
Look at this job posting and extract ONLY the company name.

Job Posting:
{text}

Instructions:
- Look for company name at the top, in headers, or near "Company:", "Organization:", "Join", "About us:"
- Check email addresses (e.g., hr@companyname.com means company is "CompanyName")
- Look in footer or signature
- Return ONLY the company name, nothing else
- If you cannot find it, return the word "null"

Examples:
- "Acme Corporation is hiring" → Acme Corporation
- "Email: jobs@techcorp.com" → TechCorp
- "About XYZ Limited" → XYZ Limited

Company name:"""
    
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Clean up response
        if result.lower() == 'null' or not result or len(result) > 100:
            logger.info("Company extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted company: {result}")
        return result
    except Exception as e:
        logger.error(f"Company extraction failed: {e}")
        return None


def _extract_position(model, text: str) -> str:
    """Extract job position using focused prompt."""
    prompt = f"""
Look at this job posting and extract ONLY the job title/position.

Job Posting:
{text}

Instructions:
- Look for "Job Title:", "Position:", "Role:", "Vacancy:", "Hiring for:", "We are looking for"
- Usually appears at the very top or in the first few lines
- Return ONLY the job title, nothing else
- If you cannot find it, return the word "null"

Examples:
- "Software Engineer - Full Stack" → Software Engineer - Full Stack
- "We are hiring: Marketing Manager" → Marketing Manager
- "Position: Data Analyst Intern" → Data Analyst Intern

Job title:"""
    
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Clean up response
        if result.lower() == 'null' or not result or len(result) > 150:
            logger.info("Position extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted position: {result}")
        return result
    except Exception as e:
        logger.error(f"Position extraction failed: {e}")
        return None


def _extract_location(model, text: str) -> str:
    """Extract location using focused prompt."""
    prompt = f"""
Look at this job posting and extract ONLY the work location.

Job Posting:
{text}

Instructions:
- Look for "Location:", "Office:", "Workplace:", "Job Location:", "Work from"
- Look for city names like Dhaka, Chittagong, Sylhet, Khulna, etc.
- Look for area names like Gulshan, Banani, Dhanmondi, Niketon, etc.
- Include "Remote" or "Work from home" if mentioned
- Return ONLY the location, nothing else
- If you cannot find it, return the word "null"

Examples:
- "Location: Dhaka, Bangladesh" → Dhaka, Bangladesh
- "Office: Gulshan 2, Dhaka" → Gulshan 2, Dhaka
- "Remote work" → Remote

Location:"""
    
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Clean up response
        if result.lower() == 'null' or not result or len(result) > 100:
            logger.info("Location extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted location: {result}")
        return result
    except Exception as e:
        logger.error(f"Location extraction failed: {e}")
        return None


def _extract_salary(model, text: str) -> str:
    """Extract salary using focused prompt."""
    prompt = f"""
Look at this job posting and extract ONLY the salary information.

Job Posting:
{text}

Instructions:
- Look for "Salary:", "Compensation:", "Pay:", "Monthly Salary:", "Package:"
- Look for currency symbols: BDT, USD, $, ৳, Tk
- Look for numbers followed by these keywords
- Include the full salary range if given
- Return ONLY the salary info, nothing else
- If you cannot find it, return the word "null"

Examples:
- "Salary: 50,000 BDT per month" → 50,000 BDT per month
- "Monthly: ৳40,000 - ৳60,000" → ৳40,000 - ৳60,000
- "Compensation: $800/month" → $800/month

Salary:"""
    
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Clean up response
        if result.lower() == 'null' or not result or len(result) > 100:
            logger.info("Salary extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted salary: {result}")
        return result
    except Exception as e:
        logger.error(f"Salary extraction failed: {e}")
        return None


def _extract_deadline(model, text: str) -> str:
    """Extract deadline using focused prompt."""
    prompt = f"""
Look at this job posting and extract ONLY the application deadline date.

Job Posting:
{text}

Instructions:
- Look for "Deadline:", "Apply by:", "Last date:", "Applications close:", "Valid till:"
- Return the date in YYYY-MM-DD format if possible
- If you cannot find a deadline, return the word "null"

Examples:
- "Deadline: February 15, 2026" → 2026-02-15
- "Apply by 10th March 2026" → 2026-03-10
- "Last date: 05/02/2026" → 2026-02-05

Deadline (YYYY-MM-DD):"""
    
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Clean up response
        if result.lower() == 'null' or not result or len(result) > 50:
            logger.info("Deadline extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted deadline: {result}")
        return result
    except Exception as e:
        logger.error(f"Deadline extraction failed: {e}")
        return None


def _extract_description(model, text: str) -> str:
    """Extract brief job description."""
    prompt = f"""
Look at this job posting and write a ONE sentence summary (max 200 characters).

Job Posting:
{text}

Instructions:
- Summarize what the job is about in 1 sentence
- Focus on key responsibilities or role
- Keep it under 200 characters
- If you cannot summarize, return the word "null"

Summary:"""
    
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Clean up response
        if result.lower() == 'null' or not result or len(result) > 250:
            logger.info("Description extraction returned null or invalid")
            return None
        
        # Truncate if too long
        if len(result) > 200:
            result = result[:197] + "..."
        
        logger.info(f"Extracted description: {result}")
        return result
    except Exception as e:
        logger.error(f"Description extraction failed: {e}")
        return None


def extract_job_details_gemini(text: str, url: str = None) -> Dict:
    """
    Use Gemini API to extract job details using multi-pass strategy.
    
    Args:
        text: Job posting text
        url: Job posting URL (optional)
        
    Returns:
        Dictionary with extracted fields
    """
    logger.info("Using Gemini API to extract job details")
    
    if not config.GEMINI_API_KEY or not genai:
        logger.error("Gemini API not configured or not available")
        return _get_default_job_data(url)
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        logger.info(f"Initializing Gemini model: {config.GEMINI_MODEL}")
        
        # Limit text length
        text_sample = text[:5000] if len(text) > 5000 else text
        
        # Initialize result dict
        job_data = {
            'company': None,
            'position': None,
            'deadline': None,
            'salary': None,
            'location': None,
            'description': None,
            'url': url
        }
        
        # PASS 1: Extract company name
        job_data['company'] = _extract_company(model, text_sample)
        
        # PASS 2: Extract position
        job_data['position'] = _extract_position(model, text_sample)
        
        # PASS 3: Extract location
        job_data['location'] = _extract_location(model, text_sample)
        
        # PASS 4: Extract salary
        job_data['salary'] = _extract_salary(model, text_sample)
        
        # PASS 5: Extract deadline (if not already found by regex)
        deadline_str = _extract_deadline(model, text_sample)
        if deadline_str:
            try:
                deadline = dateparser.parse(
                    deadline_str,
                    settings={
                        'TIMEZONE': str(config.TIMEZONE),
                        'RETURN_AS_TIMEZONE_AWARE': True,
                        'PREFER_DATES_FROM': 'future'
                    }
                )
                job_data['deadline'] = deadline
            except Exception:
                job_data['deadline'] = None
        
        # PASS 6: Extract description
        job_data['description'] = _extract_description(model, text_sample)
        
        logger.info(f"Extraction complete: {job_data}")
        return job_data
        
    except Exception as e:
        logger.error(f"Gemini API extraction failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return _get_default_job_data(url)


def extract_job_details(text: str, url: str = None) -> Dict:
    """
    Complete job extraction pipeline.
    
    1. Try regex for deadline
    2. Use Gemini for all details (including deadline if regex failed)
    
    Args:
        text: Job posting text content
        url: Job posting URL (optional)
        
    Returns:
        Dictionary with all extracted job details
    """
    logger.info("Starting job detail extraction pipeline")
    
    # Step 1: Try regex for deadline
    deadline = extract_deadline_regex(text)
    
    # Step 2: Use Gemini for other details
    job_data = extract_job_details_gemini(text, url)
    
    # Use regex deadline if found and Gemini didn't find one
    if deadline and not job_data.get('deadline'):
        job_data['deadline'] = deadline
        logger.info("Using regex-extracted deadline")
    
    # Ensure URL is in job data if provided
    if url:
        job_data['url'] = url
    
    # Add extraction timestamp
    job_data['added_on'] = datetime.now(config.TIMEZONE)
    
    return job_data


def _get_default_job_data(url: str) -> Dict:
    """
    Return default job data structure when extraction fails.
    
    Args:
        url: Job posting URL
        
    Returns:
        Dictionary with default values
    """
    return {
        'company': DEFAULT_COMPANY,
        'position': DEFAULT_POSITION,
        'deadline': None,
        'salary': None,
        'location': None,
        'description': None,
        'url': url
    }


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    
    test_text = """
    Frontend Developer Position
    
    Company: Tech Solutions Ltd
    Location: Dhaka, Bangladesh
    Salary: 50,000-60,000 BDT
    
    We are hiring a React developer.
    
    Application deadline: February 15, 2026
    """
    
    deadline = extract_deadline_regex(test_text)
    print(f"Extracted deadline: {deadline}")
