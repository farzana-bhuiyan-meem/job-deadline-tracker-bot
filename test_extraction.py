#!/usr/bin/env python3
"""
Test script for multi-pass Gemini extraction.
"""

import logging
import sys
from extractor import extract_job_details

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test case 1: Cityscape Job
test_cityscape = """
IT & Odoo Software Intern

Company: Cityscape International Ltd (or Cityscape Lifestyle Limited)
Location: Dhaka (GULSHAN 1)

We are looking for an IT intern to work on Odoo ERP system.

Contact: hr@cityscapebd.com
"""

# Test case 2: Complete job posting
test_complete = """
Helium Bangladesh is hiring!

Position: Intern – Human Resources (HR)
Location: Niketon, Dhaka
Monthly Salary: BDT 6,000
Deadline: February 15, 2026

About the role:
We are seeking a passionate HR intern to join our team and assist with recruitment, onboarding, and employee engagement activities.

Contact: careers@heliumbd.com
"""

# Test case 3: Minimal job posting
test_minimal = """
Software Engineer position at TechCorp Bangladesh.
Apply to: jobs@techcorp.com.bd
"""

def test_extraction(test_name, test_text):
    """Test extraction and print results."""
    print("\n" + "="*60)
    print(f"Testing: {test_name}")
    print("="*60)
    
    result = extract_job_details(test_text, url="https://example.com/job")
    
    print("\n📊 Extraction Results:")
    print(f"  🏢 Company:     {result.get('company', 'None')}")
    print(f"  💼 Position:    {result.get('position', 'None')}")
    print(f"  📍 Location:    {result.get('location', 'None')}")
    print(f"  💰 Salary:      {result.get('salary', 'None')}")
    print(f"  📅 Deadline:    {result.get('deadline', 'None')}")
    print(f"  📝 Description: {result.get('description', 'None')}")
    
    # Check if extraction improved (not all null except deadline)
    non_null_fields = sum([
        1 for key in ['company', 'position', 'location', 'salary', 'description']
        if result.get(key) is not None
    ])
    
    print(f"\n✓ Non-null fields: {non_null_fields}/5")
    
    if non_null_fields >= 2:
        print("✅ PASS - Multiple fields extracted successfully!")
    else:
        print("⚠️  PARTIAL - Only few fields extracted")
    
    return result

if __name__ == "__main__":
    print("🧪 Multi-Pass Gemini Extraction Test Suite")
    print("="*60)
    
    # Run tests
    test_extraction("Cityscape Job", test_cityscape)
    test_extraction("Complete Job Posting (Helium)", test_complete)
    test_extraction("Minimal Job Posting", test_minimal)
    
    print("\n" + "="*60)
    print("🏁 Test suite completed!")
    print("="*60)
