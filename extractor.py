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

# Maximum length for extracted salary text
MAX_SALARY_TEXT_LENGTH = 150

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


def extract_company_regex(text: str) -> Optional[str]:
    """
    Extract company name using regex patterns.
    Fallback when Gemini extraction fails.
    
    Args:
        text: Job posting text
        
    Returns:
        Company name string or None
    """
    logger.info("Attempting to extract company using regex patterns")
    
    patterns = [
        # "Company: Acme Corporation"
        r'Company:\s*([A-Z][A-Za-z\s&.,()]+?)(?:\n|is|hiring|looking|Job|$)',
        
        # "Organization: Tech Solutions"
        r'Organization:\s*([A-Z][A-Za-z\s&.,()]+?)(?:\n|is|Job|$)',
        
        # "About XYZ Limited" or "About Cityscape International Ltd"
        r'About\s+(?:Us\s+)?([A-Z][A-Za-z\s&.,()]+?(?:Ltd|Limited|Inc|Corporation|Group|International|Bangladesh))(?:\n|is|Job|$)',
        
        # "Cityscape International Ltd is hiring"
        r'([A-Z][A-Za-z\s&.,()]+?(?:Ltd|Limited|Inc|Corporation|Group|International))\s+is\s+(?:hiring|looking|seeking)',
        
        # "Join Helium Bangladesh"
        r'Join\s+(?:our team at\s+)?([A-Z][A-Za-z\s&.,()]+?(?:Ltd|Limited|Inc|Corporation|Group|International|Bangladesh))(?:\n|!|\.|$)',
        
        # Look for company names ending with common suffixes
        r'([A-Z][A-Za-z\s&.,()]+?(?:Limited|Ltd|Inc|Corporation|Group|International|Bangladesh))\s*(?:\n|is|hiring|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            company = match.group(1).strip()
            # Clean up
            company = re.sub(r'\s+', ' ', company)  # Normalize whitespace
            # Sanity check: reasonable length
            if 3 < len(company) < 100 and company.lower() not in ['job', 'position', 'role']:
                logger.info(f"Regex extracted company: {company}")
                return company
    
    logger.info("No company found using regex patterns")
    return None


def extract_position_regex(text: str) -> Optional[str]:
    """
    Extract job position/title using regex patterns.
    Fallback when Gemini extraction fails.
    
    Args:
        text: Job posting text
        
    Returns:
        Position string or None
    """
    logger.info("Attempting to extract position using regex patterns")
    
    patterns = [
        # "Position: Software Engineer"
        r'Position:\s*([A-Z][A-Za-z\s\-–&/(),]+?)(?:\n|Job|Employment|Work|$)',
        
        # "Job Title: Marketing Manager"
        r'Job Title:\s*([A-Z][A-Za-z\s\-–&/(),]+?)(?:\n|Job|Employment|Work|$)',
        
        # "Role: Data Analyst"
        r'Role:\s*([A-Z][A-Za-z\s\-–&/(),]+?)(?:\n|Job|Employment|Work|$)',
        
        # "Hiring for: HR Intern"
        r'Hiring for:\s*([A-Z][A-Za-z\s\-–&/(),]+?)(?:\n|Job|to|$)',
        
        # "Vacancy: Senior Developer"
        r'Vacancy:\s*([A-Z][A-Za-z\s\-–&/(),]+?)(?:\n|Job|Employment|$)',
        
        # "is looking for IT & Odoo Software Intern" (from your example) - prioritize this
        r'is looking for\s+([A-Z][A-Za-z\s\-–&/(),]+?)(?:\n|Job|to|$)',
        
        # "We are looking for a Software Engineer" - check this last
        r'looking for\s+(?:a|an)\s+([A-Z][A-Za-z\s\-–&/(),]+?)(?:\n|to|with|who|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            position = match.group(1).strip()
            # Clean up
            position = re.sub(r'\s+', ' ', position)
            # Sanity check
            if 3 < len(position) < 150:
                logger.info(f"Regex extracted position: {position}")
                return position
    
    logger.info("No position found using regex patterns")
    return None


def extract_location_regex(text: str) -> Optional[str]:
    """
    Extract job location using regex patterns.
    Fallback when Gemini extraction fails.
    
    Args:
        text: Job posting text
        
    Returns:
        Location string or None
    """
    logger.info("Attempting to extract location using regex patterns")
    
    # First try labeled locations
    labeled_patterns = [
        r'(?:Location|Job Location|Workplace|Office|Work Location):\s*([A-Za-z\s,\-()0-9]+?)(?:\n|\||Job|Employment|Salary|$)',
    ]
    
    for pattern in labeled_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            location = match.group(1).strip()
            # Clean up
            location = re.sub(r'\s+', ' ', location)
            if 3 < len(location) < 100:
                logger.info(f"Regex extracted location (labeled): {location}")
                return location
    
    # Try to find Bangladesh cities
    city_pattern = r'((?:Dhaka|Chittagong|Sylhet|Khulna|Rajshahi|Rangpur|Barisal|Mymensingh|Gazipur|Narayanganj)(?:\s*\([A-Za-z\s0-9]+\))?)'
    match = re.search(city_pattern, text, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
        logger.info(f"Regex extracted location (city): {city}")
        return city
    
    # Try to find Dhaka areas
    area_pattern = r'((?:Gulshan|Banani|Dhanmondi|Niketon|Motijheel|Kawran Bazar|Mohakhali|Uttara|Mirpur|Badda|Rampura|Tejgaon|Farmgate)(?:\s*\d+)?)'
    match = re.search(area_pattern, text, re.IGNORECASE)
    if match:
        area = match.group(1).strip()
        logger.info(f"Regex extracted location (area): {area}")
        return area
    
    # Check for remote work
    if re.search(r'\b(remote|work from home|wfh)\b', text, re.IGNORECASE):
        logger.info("Regex extracted location: Remote")
        return "Remote"
    
    logger.info("No location found using regex patterns")
    return None


def extract_salary_regex(text: str) -> Optional[str]:
    """
    Extract salary information using regex patterns.
    Fallback when Gemini extraction fails.
    Handles multiple Bangladesh salary formats.
    
    Args:
        text: Job posting text
        
    Returns:
        Salary string or None
    """
    logger.info("Attempting to extract salary using regex patterns")
    
    # Pattern 1: Labeled salary with full details
    # "Salary: Tk. 22,000 - 30,000 (Monthly)"
    # "Monthly Salary: BDT 25,000 - 35,000 (Negotiable)"
    labeled_patterns = [
        r'(?:Salary|Compensation|Monthly Salary|Package|Pay):\s*([^\n]+?)(?:\n\n|\n[A-Z]|$)',
    ]
    
    for pattern in labeled_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            salary = match.group(1).strip()
            # Clean up
            salary = re.sub(r'\s+', ' ', salary)
            # Basic validation: contains number or "Negotiable"
            if re.search(r'\d|negotiable', salary, re.IGNORECASE) and len(salary) < MAX_SALARY_TEXT_LENGTH:
                logger.info(f"Regex extracted salary (labeled): {salary}")
                return salary
    
    # Pattern 2: Currency symbol at start with range and suffix
    # "Tk. 22,000 - 30,000 per month"
    # "৳ 25,000 - 32,000"
    # "BDT 50,000-60,000 (Monthly)"
    # "$800-1000/month"
    currency_first_patterns = [
        # Range: Currency + number + (k)? + separator + number + (k)? + optional suffix
        # Examples: "Tk. 22,000 - 30,000 per month", "৳25k-35k"
        r'((?:Tk\.?|৳|BDT|USD|\$)\s*[\d,]+(?:k|K)?\s*(?:[-–to]+)\s*[\d,]+(?:k|K)?(?:\s*(?:BDT|Tk|৳|USD|\$))?(?:\s*(?:per month|monthly|/month|\(Monthly\)|\(Negotiable\)))?)',
        
        # Single amount: Currency + number + (k)? + (+)? + optional suffix
        # Examples: "Tk 50000+", "BDT 50k per month"
        r'((?:Tk\.?|৳|BDT|USD|\$)\s*[\d,]+(?:k|K)?(?:\+)?(?:\s*(?:per month|monthly|/month|\(Monthly\)|\(Negotiable\)))?)',
    ]
    
    for pattern in currency_first_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            salary = match.group(1).strip()
            # Clean up whitespace
            salary = re.sub(r'\s+', ' ', salary)
            # Validate: reasonable length and contains digits
            if re.search(r'\d', salary) and 3 < len(salary) < MAX_SALARY_TEXT_LENGTH:
                logger.info(f"Regex extracted salary (currency first): {salary}")
                return salary
    
    # Pattern 3: Amount first, then currency
    # "22,000 - 30,000 BDT"
    # "25000-35000 Tk"
    # "30k-40k BDT/month"
    amount_first_patterns = [
        # Range: number + (k)? + separator + number + (k)? + currency + optional suffix
        # Examples: "22,000 - 30,000 BDT", "30k-40k BDT/month"
        r'([\d,]+(?:k|K)?\s*(?:[-–to]+)\s*[\d,]+(?:k|K)?\s*(?:BDT|Tk\.?|৳|USD|\$)(?:\s*(?:per month|monthly|/month|\(Monthly\)|\(Negotiable\)))?)',
        
        # Single amount: number + (k)? + (+)? + currency + optional suffix
        # Examples: "50000+ BDT", "50k Tk per month"
        r'([\d,]+(?:k|K)?(?:\+)?\s*(?:BDT|Tk\.?|৳|USD|\$)(?:\s*(?:per month|monthly|/month|\(Monthly\)|\(Negotiable\)))?)',
    ]
    
    for pattern in amount_first_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            salary = match.group(1).strip()
            salary = re.sub(r'\s+', ' ', salary)
            # Additional validation: must have reasonable digits
            if re.search(r'\d{2,}', salary) and 3 < len(salary) < MAX_SALARY_TEXT_LENGTH:
                logger.info(f"Regex extracted salary (amount first): {salary}")
                return salary
    
    # Pattern 4: Just numbers in salary context (no currency symbol)
    # "22,000 - 30,000 (Monthly)"
    # "30000-40000"
    # Only match if near "Salary" keyword to avoid false positives
    contextual_pattern = r'(?:Salary|Compensation|Pay)(?:[:\s]+).*?([\d,]+\s*(?:[-–to]+)\s*[\d,]+(?:\s*\((?:Monthly|Negotiable|Per Month)\))?)'
    match = re.search(contextual_pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        # Make sure we don't capture too much text
        potential_salary = match.group(1).strip()
        # Check if captured text is reasonably sized
        if len(potential_salary) < 100:
            salary = potential_salary
            salary = re.sub(r'\s+', ' ', salary)
            logger.info(f"Regex extracted salary (contextual): {salary}")
            return salary
    
    # Pattern 5: "Negotiable" or "As per company policy"
    negotiable_match = re.search(r'(?:Salary|Compensation)[:\s]+(Negotiable|As per company policy|Competitive)', text, re.IGNORECASE)
    if negotiable_match:
        logger.info(f"Regex extracted salary (negotiable): {negotiable_match.group(1)}")
        return negotiable_match.group(1)
    
    # Pattern 6: Standalone amount ranges (last resort, be conservative)
    # Only match clear salary-like numbers (4-6 digits with separator or k suffix)
    standalone_pattern = r'\b((?:\d{2,3}[,]\d{3}|\d{2,3}k)\s*[-–to]+\s*(?:\d{2,3}[,]\d{3}|\d{2,3}k))\b'
    match = re.search(standalone_pattern, text, re.IGNORECASE)
    if match:
        salary = match.group(1).strip()
        # Only accept if it looks like a salary (20k-50k range or 20,000-50,000)
        salary = re.sub(r'\s+', ' ', salary)
        logger.info(f"Regex extracted salary (standalone): {salary}")
        return salary
    
    logger.info("No salary found using regex patterns")
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
    Falls back to regex patterns if Gemini extraction fails.
    
    Args:
        text: Job posting text
        url: Job posting URL (optional)
        
    Returns:
        Dictionary with extracted fields
    """
    logger.info("Using Gemini API to extract job details")
    
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
    
    if not config.GEMINI_API_KEY or not genai:
        logger.warning("Gemini API not configured or not available, using regex-only extraction")
        # Try regex extraction for all fields
        job_data['company'] = extract_company_regex(text_sample)
        job_data['position'] = extract_position_regex(text_sample)
        job_data['location'] = extract_location_regex(text_sample)
        job_data['salary'] = extract_salary_regex(text_sample)
        # Deadline will be handled by extract_job_details() function
        # Description has no regex fallback
        return job_data
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        logger.info(f"Initializing Gemini model: {config.GEMINI_MODEL}")
        
        # PASS 1: Extract company name
        job_data['company'] = _extract_company(model, text_sample)
        # Fallback to regex if Gemini failed
        if not job_data['company']:
            job_data['company'] = extract_company_regex(text_sample)
        
        # PASS 2: Extract position
        job_data['position'] = _extract_position(model, text_sample)
        # Fallback to regex if Gemini failed
        if not job_data['position']:
            job_data['position'] = extract_position_regex(text_sample)
        
        # PASS 3: Extract location
        job_data['location'] = _extract_location(model, text_sample)
        # Fallback to regex if Gemini failed
        if not job_data['location']:
            job_data['location'] = extract_location_regex(text_sample)
        
        # PASS 4: Extract salary
        job_data['salary'] = _extract_salary(model, text_sample)
        # Fallback to regex if Gemini failed
        if not job_data['salary']:
            job_data['salary'] = extract_salary_regex(text_sample)
        
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
        
        # PASS 6: Extract description (Gemini only, no regex fallback makes sense here)
        job_data['description'] = _extract_description(model, text_sample)
        
        logger.info(f"Extraction complete: {job_data}")
        return job_data
        
    except Exception as e:
        logger.error(f"Gemini API extraction failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Fall back to regex-only extraction
        logger.info("Falling back to regex-only extraction due to Gemini failure")
        job_data['company'] = extract_company_regex(text_sample)
        job_data['position'] = extract_position_regex(text_sample)
        job_data['location'] = extract_location_regex(text_sample)
        job_data['salary'] = extract_salary_regex(text_sample)
        return job_data


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
