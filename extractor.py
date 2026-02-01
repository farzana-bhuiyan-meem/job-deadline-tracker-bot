"""
Job detail extraction using regex patterns and Google Gemini API.
"""

import logging
import re
import json
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


def extract_job_details_gemini(text: str, url: str = None) -> Dict:
    """
    Use Gemini API to extract job details including:
    - company_name
    - position
    - deadline (if not found by regex)
    - salary
    - location
    - description_summary
    
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
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        
        # Limit text length to avoid token limits
        text_sample = text[:5000] if len(text) > 5000 else text
        
        # Improved extraction prompt with better instructions
        url_line = f"\nJob URL: {url}" if url else ""
        
        prompt = f"""
You are an expert at extracting job posting information. Analyze the following job posting text carefully and extract ALL available information.

Job Posting Text:
{text_sample}{url_line}

Extract the following information with HIGH ACCURACY:

1. **Company Name**: Look for company name, organization name, employer name. Check near phrases like "Company:", "About us:", "Join our team at", email domains (@company.com), footer text, etc.

2. **Job Title/Position**: Look for "Job Title:", "Position:", "Role:", "Hiring for:", "Vacancy:", or similar. This is usually prominent at the top.

3. **Application Deadline**: Look for "Deadline:", "Apply by:", "Last date:", "Applications close:", "Valid till:", or any date mentioned with deadline context. Return in YYYY-MM-DD format.

4. **Salary/Compensation**: Look for "Salary:", "Compensation:", "Pay:", "BDT", "USD", "$", "৳", "Tk", monthly/yearly amounts, salary ranges. Include currency and full details found.

5. **Location**: Look for "Location:", "Office:", "Workplace:", city names like "Dhaka", "Remote", "Work from home", area names like "Gulshan", "Banani", "Niketon", etc.

6. **Brief Description**: Summarize the key responsibilities or job description in 1-2 sentences (max 200 characters).

IMPORTANT INSTRUCTIONS:
- Be thorough and check the ENTIRE text carefully
- Even if a field isn't clearly labeled, try to infer it from context
- For company name: check email addresses (e.g., "contact@helium.com" → likely "Helium" or "Helium Bangladesh")
- Return actual values found in the text, not generic placeholders
- Only return null if the information is genuinely not present anywhere in the text
- Be smart about context - if you see "HR Intern at Helium Bangladesh", extract both position and company

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "company": "exact company name found or null",
  "position": "exact job title found or null",
  "deadline": "YYYY-MM-DD or null",
  "salary": "full salary details with currency or null",
  "location": "location details or null",
  "description": "brief summary or null"
}}

Do not include any text outside the JSON block.
"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean response text (remove markdown code blocks if present)
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)
        
        # Parse JSON response
        try:
            job_data = json.loads(response_text)
            logger.info("Successfully extracted job details with Gemini API")
            logger.info(f"Extracted data: {job_data}")
            
            # Parse deadline if present
            if job_data.get('deadline') and job_data['deadline'] != 'null':
                try:
                    deadline_str = job_data['deadline']
                    deadline = dateparser.parse(
                        deadline_str,
                        settings={
                            'TIMEZONE': str(config.TIMEZONE),
                            'RETURN_AS_TIMEZONE_AWARE': True
                        }
                    )
                    job_data['deadline'] = deadline
                except Exception as e:
                    logger.warning(f"Failed to parse Gemini deadline: {str(e)}")
                    job_data['deadline'] = None
            else:
                job_data['deadline'] = None
            
            # Add URL to job data if provided
            if url:
                job_data['url'] = url
            
            return job_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            return _get_default_job_data(url)
    
    except Exception as e:
        logger.error(f"Gemini API extraction failed: {str(e)}")
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
