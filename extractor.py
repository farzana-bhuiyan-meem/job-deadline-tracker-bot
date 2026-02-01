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
    Extract job details using Gemini 1.5 Flash API.
    
    Args:
        text: Job posting text to extract from
        url: Optional URL of job posting
        
    Returns:
        dict with extracted fields: company, position, deadline, salary, location, description
    """
    logger.info("Using Gemini API to extract job details")
    
    if not config.GEMINI_API_KEY or not genai:
        logger.error("Gemini API not configured or not available")
        return _get_empty_job_data()
    
    try:
        # Use Gemini 1.5 Flash model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Limit text length to avoid token limits
        text_sample = text[:5000] if len(text) > 5000 else text
        
        # Enhanced extraction prompt
        prompt = f"""
You are an expert at extracting job posting information. Analyze this job posting text very carefully.

JOB POSTING TEXT:
{text_sample}

{f"URL: {url}" if url else ""}

Extract the following information with HIGH ACCURACY. Look at the ENTIRE text carefully:

1. **Company Name**: Look for phrases like "Company:", "About Us:", "Join", organization name, or check email domains (e.g., "contact@helium.com" means company is likely "Helium").

2. **Job Title/Position**: Look for "Job Title:", "Position:", "Role:", "Hiring for:", "Vacancy:", or prominent text at the beginning.

3. **Application Deadline**: Look for "Deadline:", "Apply by:", "Last date:", "Applications close:", any date with deadline context. Format as YYYY-MM-DD.

4. **Salary/Compensation**: Look for "Salary:", "Monthly Salary:", "Compensation:", "BDT", "USD", "৳", numbers with currency symbols.

5. **Location**: Look for "Location:", "Office:", "Workplace:", city names like "Dhaka", "Chittagong", area names like "Gulshan", "Banani", "Niketon", etc.

6. **Description**: Summarize the key responsibilities in 1-2 sentences (max 200 characters).

CRITICAL INSTRUCTIONS:
- Read the ENTIRE text carefully before extracting
- Look for information even if it's not labeled
- Company names are often at the top or in email addresses
- Return actual values found in the text, NOT placeholder text like "Not specified"
- Only return null if information is genuinely not present

Return ONLY valid JSON with NO additional text:

{{
  "company": "exact company name or null",
  "position": "exact job title or null",
  "deadline": "YYYY-MM-DD or null",
  "salary": "full salary details or null",
  "location": "location or null",
  "description": "brief summary or null"
}}
"""

        # Generate response
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Log raw response for debugging
        logger.info(f"Gemini raw response: {response_text[:500]}")
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        # Parse JSON
        extracted_data = json.loads(response_text)
        
        logger.info(f"Gemini extraction successful: {extracted_data}")
        
        # Parse deadline if present
        if extracted_data.get('deadline') and extracted_data['deadline'] != 'null':
            try:
                deadline_str = extracted_data['deadline']
                deadline = dateparser.parse(
                    deadline_str,
                    settings={
                        'TIMEZONE': str(config.TIMEZONE),
                        'RETURN_AS_TIMEZONE_AWARE': True
                    }
                )
                extracted_data['deadline'] = deadline
            except Exception as e:
                logger.warning(f"Failed to parse Gemini deadline: {str(e)}")
                extracted_data['deadline'] = None
        else:
            extracted_data['deadline'] = None
        
        # Add URL to job data if provided
        if url:
            extracted_data['url'] = url
        
        # Validate and clean data - replace null strings with None
        return {
            'company': extracted_data.get('company') or None,
            'position': extracted_data.get('position') or None,
            'deadline': extracted_data.get('deadline') or None,
            'salary': extracted_data.get('salary') or None,
            'location': extracted_data.get('location') or None,
            'description': extracted_data.get('description') or None,
            'url': extracted_data.get('url')
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {e}")
        logger.error(f"Response text was: {response_text[:500]}")
        return _get_empty_job_data()
        
    except Exception as e:
        logger.error(f"Gemini API extraction failed: {e}")
        return _get_empty_job_data()


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


def _get_empty_job_data() -> Dict:
    """
    Return empty job data dict with None values.
    
    Returns:
        Dictionary with None values for all fields
    """
    return {
        'company': None,
        'position': None,
        'deadline': None,
        'salary': None,
        'location': None,
        'description': None
    }


def _get_default_job_data(url: str) -> Dict:
    """
    Return default job data structure when extraction fails.
    
    Args:
        url: Job posting URL
        
    Returns:
        Dictionary with default values
    """
    return {
        'company': None,
        'position': None,
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
