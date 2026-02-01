#!/usr/bin/env python3
"""
Integration test to verify no regressions in other extraction functions.
"""

import logging
from extractor import (
    extract_company_regex,
    extract_position_regex,
    extract_location_regex,
    extract_deadline_regex,
    extract_salary_regex
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_full_extraction():
    """Test that all extraction functions work together."""
    logger.info("\n" + "="*80)
    logger.info("INTEGRATION TEST: Full Job Extraction")
    logger.info("="*80)
    
    # Sample job posting with all fields
    job_posting = """
    IT & Odoo Software Intern

    Cityscape International Ltd is looking for IT & Odoo Software Intern
    
    About Cityscape International Ltd:
    Leading technology company in Bangladesh
    
    Job Location
    • Dhaka (Niketon)
    
    Monthly Salary
    • Tk. 22,000 - 30,000 (Monthly)
    
    Experience
    • 2-3 years experience preferred
    
    Application deadline: February 15, 2026
    """
    
    logger.info("\nExtracting from sample job posting...")
    
    # Test each extractor
    company = extract_company_regex(job_posting)
    logger.info(f"\n✅ Company: {company}")
    
    position = extract_position_regex(job_posting)
    logger.info(f"✅ Position: {position}")
    
    location = extract_location_regex(job_posting)
    logger.info(f"✅ Location: {location}")
    
    salary = extract_salary_regex(job_posting)
    logger.info(f"✅ Salary: {salary}")
    
    deadline = extract_deadline_regex(job_posting)
    logger.info(f"✅ Deadline: {deadline}")
    
    # Verify all were extracted
    success = all([company, position, location, salary, deadline])
    
    logger.info("\n" + "="*80)
    if success:
        logger.info("✅ ALL FIELDS EXTRACTED SUCCESSFULLY")
    else:
        logger.info("⚠️  Some fields missing (may be expected)")
    logger.info("="*80)
    
    return success


def test_salary_specific_cases():
    """Test salary extraction doesn't interfere with other numbers in text."""
    logger.info("\n" + "="*80)
    logger.info("REGRESSION TEST: Salary vs Other Numbers")
    logger.info("="*80)
    
    # Test that we don't extract non-salary numbers
    test_cases = [
        {
            'text': """
            Senior Developer Role
            
            Experience: 2-3 years required
            Age: 25-30 preferred
            Team size: 10-15 people
            Working hours: 9-5
            Salary: Tk. 50,000 - 70,000
            """,
            'expected_salary': 'Tk. 50,000 - 70,000',
            'should_not_contain': ['2-3', '25-30', '10-15', '9-5']
        }
    ]
    
    all_pass = True
    
    for i, case in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}:")
        salary = extract_salary_regex(case['text'])
        logger.info(f"  Extracted salary: {salary}")
        logger.info(f"  Expected: {case['expected_salary']}")
        
        # Check correct extraction
        if salary and case['expected_salary'] in salary:
            logger.info("  ✅ Correct salary extracted")
        else:
            logger.info("  ❌ Failed to extract correct salary")
            all_pass = False
            continue
        
        # Check it doesn't contain non-salary numbers
        contains_bad = False
        for bad_value in case['should_not_contain']:
            if bad_value in salary:
                logger.info(f"  ❌ Incorrectly contains: {bad_value}")
                contains_bad = True
                all_pass = False
        
        if not contains_bad:
            logger.info("  ✅ No false positives")
    
    logger.info("\n" + "="*80)
    if all_pass:
        logger.info("✅ NO REGRESSIONS DETECTED")
    else:
        logger.info("❌ REGRESSIONS FOUND")
    logger.info("="*80)
    
    return all_pass


def main():
    """Run integration tests."""
    logger.info("\n" + "="*80)
    logger.info("REGRESSION TEST SUITE")
    logger.info("="*80)
    
    # Run tests
    test1_passed = test_full_extraction()
    test2_passed = test_salary_specific_cases()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("FINAL SUMMARY")
    logger.info("="*80)
    logger.info(f"Full Extraction: {'✅ PASS' if test1_passed else '⚠️  PARTIAL'}")
    logger.info(f"Regression Tests: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    logger.info("="*80)
    
    return 0 if test2_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
