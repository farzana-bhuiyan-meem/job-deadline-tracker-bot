"""
Job detail extraction using regex patterns and Ollama (local LLM).
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

# Import Ollama for local LLM extraction
logger = logging.getLogger(__name__)

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama not installed. Run: pip install ollama")


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
    Fallback when Ollama extraction fails.
    
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
    Fallback when Ollama extraction fails.
    
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
    Fallback when Ollama extraction fails.
    
    Args:
        text: Job posting text
        
    Returns:
        Location string or None
    """
    logger.info("Attempting to extract location using regex patterns")
    
    # Bangladesh cities for consistent pattern matching
    BANGLADESH_CITIES = ['Dhaka', 'Chittagong', 'Sylhet', 'Khulna', 'Rajshahi', 'Rangpur', 'Barisal', 'Mymensingh', 'Gazipur', 'Narayanganj']
    cities_pattern = '|'.join(BANGLADESH_CITIES)
    
    # First try labeled locations (captures full address)
    labeled_patterns = [
        # "Location: Police Park, House #05, Road #10, Block D, Bandaree, Khilgaon, Dhaka 1219"
        # Captures everything until double newline, or newline followed by capital letter, or end of text
        # Using greedy matching (no ?) to capture the full line
        r'(?:Location|Job Location|Workplace|Office|Work Location):\s*([^\n]+)(?:\n\n|\n[A-Z]|$)',
        
        # Try simpler version if above doesn't work - captures until end of line
        r'(?:Location|Job Location|Workplace|Office|Work Location):\s*(.+?)(?:\n|$)',
    ]
    
    for pattern in labeled_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            location = match.group(1).strip()
            # Clean up
            location = re.sub(r'\s+', ' ', location)  # Normalize whitespace
            # Remove pipe-separated trailing content
            location = re.sub(r'\s*\|.*$', '', location)
            # Only remove keywords if they look like metadata (followed by colon or are standalone at end)
            # This prevents removing legitimate place names like "Employment Plaza"
            location = re.sub(r'\s*\b(Job|Employment|Salary|Deadline)\s*:.*$', '', location, flags=re.IGNORECASE)
            
            # Sanity check - must contain at least some text
            if 3 < len(location) < 200:
                logger.info(f"Regex extracted location (labeled): {location}")
                return location
    
    # If labeled pattern fails, try to find city + surrounding context (limited to 100 chars before city)
    # Look for "Dhaka" with surrounding text (address components before and after)
    context_pattern = f'([A-Za-z\\s,#\\-()0-9]{{0,100}}(?:{cities_pattern})[A-Za-z\\s,#\\-()0-9]*)'
    match = re.search(context_pattern, text, re.IGNORECASE)
    if match:
        location = match.group(1).strip()
        # Clean up extra whitespace and normalize
        location = re.sub(r'\s+', ' ', location)
        # Remove common prefixes like "at", "in", "from"
        location = re.sub(r'^(?:at|in|from)\s+', '', location, flags=re.IGNORECASE)
        
        if 3 < len(location) < 200:
            logger.info(f"Regex extracted location (with context): {location}")
            return location
    
    # Fallback: Try to find just Bangladesh cities
    city_pattern = f'((?:{cities_pattern})(?:\\s*\\d+)?)'
    match = re.search(city_pattern, text, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
        logger.info(f"Regex extracted location (city only): {city}")
        return city
    
    # Try to find Dhaka areas
    area_pattern = r'((?:Gulshan|Banani|Dhanmondi|Niketon|Motijheel|Kawran Bazar|Mohakhali|Uttara|Mirpur|Badda|Rampura|Tejgaon|Farmgate|Khilgaon|Bandaree)(?:\s*\d+)?(?:,\s*Dhaka)?)'
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
    Fallback when Ollama extraction fails.
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


def _extract_company(text: str) -> str:
    """Extract company name using Ollama."""
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
        response = ollama.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt,
            options={
                'temperature': 0.1,  # Low temperature for factual extraction
                'num_predict': 50,   # Limit response length
            }
        )
        result = response['response'].strip()
        
        # Clean up response
        if result.lower() == 'null' or not result or len(result) > 100:
            logger.info("Company extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted company: {result}")
        return result
    except Exception as e:
        logger.error(f"Company extraction failed: {e}")
        return None


def _extract_position(text: str) -> str:
    """Extract job position using Ollama."""
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
        response = ollama.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt,
            options={
                'temperature': 0.1,
                'num_predict': 50,
            }
        )
        result = response['response'].strip()
        
        if result.lower() == 'null' or not result or len(result) > 150:
            logger.info("Position extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted position: {result}")
        return result
    except Exception as e:
        logger.error(f"Position extraction failed: {e}")
        return None


def _extract_location(text: str) -> str:
    """Extract location using Ollama."""
    prompt = f"""
Look at this job posting and extract ONLY the work location.

Job Posting:
{text}

Instructions:
- Look for "Location:", "Office:", "Workplace:", "Job Location:", "Work from"
- Look for city names like Dhaka, Chittagong, Sylhet, Khulna, etc.
- Look for area names like Gulshan, Banani, Dhanmondi, Niketon, etc.
- Include full address if provided (House #, Road #, Block, postal code)
- Include "Remote" or "Work from home" if mentioned
- Return ONLY the location, nothing else
- If you cannot find it, return the word "null"

Examples:
- "Location: Dhaka, Bangladesh" → Dhaka, Bangladesh
- "Office: Gulshan 2, Dhaka" → Gulshan 2, Dhaka
- "Remote work" → Remote
- "Location: Police Park, House #05, Road #10, Block D, Dhaka 1219" → Police Park, House #05, Road #10, Block D, Dhaka 1219

Location:"""
    
    try:
        response = ollama.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt,
            options={
                'temperature': 0.1,
                'num_predict': 100,
            }
        )
        result = response['response'].strip()
        
        if result.lower() == 'null' or not result or len(result) > 200:
            logger.info("Location extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted location: {result}")
        return result
    except Exception as e:
        logger.error(f"Location extraction failed: {e}")
        return None


def _extract_salary(text: str) -> str:
    """Extract salary using Ollama."""
    prompt = f"""
Look at this job posting and extract ONLY the salary information.

Job Posting:
{text}

Instructions:
- Look for "Salary:", "Compensation:", "Pay:", "Monthly Salary:", "Package:"
- Look for currency symbols: BDT, USD, $, ৳, Tk, Tk.
- Look for numbers followed by these keywords
- Include the full salary range if given
- Include suffixes like (Monthly), (Negotiable), per month, etc.
- Return ONLY the salary info, nothing else
- If you cannot find it, return the word "null"

Examples:
- "Salary: 50,000 BDT per month" → 50,000 BDT per month
- "Monthly: ৳40,000 - ৳60,000" → ৳40,000 - ৳60,000
- "Compensation: $800/month" → $800/month
- "Tk. 22,000 - 30,000 (Monthly)" → Tk. 22,000 - 30,000 (Monthly)
- "Salary: Negotiable" → Negotiable

Salary:"""
    
    try:
        response = ollama.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt,
            options={
                'temperature': 0.1,
                'num_predict': 50,
            }
        )
        result = response['response'].strip()
        
        if result.lower() == 'null' or not result or len(result) > 100:
            logger.info("Salary extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted salary: {result}")
        return result
    except Exception as e:
        logger.error(f"Salary extraction failed: {e}")
        return None


def _extract_deadline(text: str) -> str:
    """Extract deadline using Ollama."""
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
        response = ollama.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt,
            options={
                'temperature': 0.1,
                'num_predict': 30,
            }
        )
        result = response['response'].strip()
        
        if result.lower() == 'null' or not result or len(result) > 50:
            logger.info("Deadline extraction returned null or invalid")
            return None
        
        logger.info(f"Extracted deadline: {result}")
        return result
    except Exception as e:
        logger.error(f"Deadline extraction failed: {e}")
        return None


def _extract_description(text: str) -> str:
    """Extract brief job description using Ollama."""
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
        response = ollama.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt,
            options={
                'temperature': 0.3,
                'num_predict': 100,
            }
        )
        result = response['response'].strip()
        
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


def _extract_with_regex_only(text: str, url: str = None) -> Dict:
    """
    Extract job details using only regex patterns (fallback when Ollama unavailable).
    
    Args:
        text: Job posting text
        url: Job posting URL (optional)
        
    Returns:
        Dictionary with extracted fields
    """
    logger.info("Using regex-only extraction")
    
    text_sample = text[:5000] if len(text) > 5000 else text
    
    job_data = {
        'company': extract_company_regex(text_sample),
        'position': extract_position_regex(text_sample),
        'location': extract_location_regex(text_sample),
        'salary': extract_salary_regex(text_sample),
        'deadline': None,
        'description': None,
        'url': url
    }
    
    return job_data


def extract_job_details_ollama(text: str, url: str = None) -> Dict:
    """
    Use Ollama (Llama 3.2) to extract job details using multi-pass strategy.
    Falls back to regex patterns if Ollama extraction fails.
    
    Args:
        text: Job posting text
        url: Job posting URL (optional)
        
    Returns:
        Dictionary with extracted fields
    """
    logger.info("Using Ollama (Llama 3.2) to extract job details")
    
    if not OLLAMA_AVAILABLE:
        logger.error("Ollama not available, using regex only")
        return _extract_with_regex_only(text, url)
    
    try:
        # Test Ollama connection
        ollama.list()
        logger.info(f"Ollama connected, using model: {config.OLLAMA_MODEL}")
    except Exception as e:
        logger.error(f"Ollama not running or not accessible: {e}")
        logger.error("Make sure Ollama is running. Start it with: ollama serve")
        return _extract_with_regex_only(text, url)
    
    try:
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
        job_data['company'] = _extract_company(text_sample)
        # Fallback to regex if Ollama failed
        if not job_data['company']:
            job_data['company'] = extract_company_regex(text_sample)
        
        # PASS 2: Extract position
        job_data['position'] = _extract_position(text_sample)
        # Fallback to regex if Ollama failed
        if not job_data['position']:
            job_data['position'] = extract_position_regex(text_sample)
        
        # PASS 3: Extract location
        job_data['location'] = _extract_location(text_sample)
        # Fallback to regex if Ollama failed
        if not job_data['location']:
            job_data['location'] = extract_location_regex(text_sample)
        
        # PASS 4: Extract salary
        job_data['salary'] = _extract_salary(text_sample)
        # Fallback to regex if Ollama failed
        if not job_data['salary']:
            job_data['salary'] = extract_salary_regex(text_sample)
        
        # PASS 5: Extract deadline
        deadline_str = _extract_deadline(text_sample)
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
        job_data['description'] = _extract_description(text_sample)
        
        logger.info(f"Extraction complete: {job_data}")
        return job_data
        
    except Exception as e:
        logger.error(f"Ollama extraction failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return _extract_with_regex_only(text, url)


def extract_job_details(text: str, url: str = None) -> Dict:
    """
    Complete job extraction pipeline.
    
    1. Try regex for deadline
    2. Use Ollama for all details (including deadline if regex failed)
    3. Fall back to regex for each field if Ollama fails
    
    Args:
        text: Job posting text content
        url: Job posting URL (optional)
        
    Returns:
        Dictionary with all extracted job details
    """
    logger.info("Starting job detail extraction pipeline")
    
    # Step 1: Try regex for deadline
    deadline = extract_deadline_regex(text)
    
    # Step 2: Use Ollama for other details
    job_data = extract_job_details_ollama(text, url)
    
    # Use regex deadline if found and Ollama didn't find one
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
