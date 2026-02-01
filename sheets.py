"""
Google Sheets integration for job tracking.
"""

import logging
import os
from datetime import datetime
from typing import Optional, List, Dict
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config
import utils

logger = logging.getLogger(__name__)

# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Global service instance
_sheets_service = None


def _get_sheets_service():
    """
    Get or create Google Sheets API service instance.
    
    Returns:
        Google Sheets API service
    """
    global _sheets_service
    
    if _sheets_service is None:
        try:
            if not os.path.exists(config.GOOGLE_SHEETS_CREDENTIALS):
                logger.error(f"Credentials file not found: {config.GOOGLE_SHEETS_CREDENTIALS}")
                raise FileNotFoundError("Google Sheets credentials file not found")
            
            creds = Credentials.from_service_account_file(
                config.GOOGLE_SHEETS_CREDENTIALS,
                scopes=SCOPES
            )
            
            _sheets_service = build('sheets', 'v4', credentials=creds)
            logger.info("Google Sheets service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {str(e)}")
            raise
    
    return _sheets_service


def initialize_sheet() -> bool:
    """
    Create sheet with headers and formatting if doesn't exist.
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Initializing Google Sheet")
    
    try:
        service = _get_sheets_service()
        sheet_id = config.GOOGLE_SHEET_ID
        
        # Check if sheet exists and has headers
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='A1:I1'
            ).execute()
            
            values = result.get('values', [])
            if values and values[0] == config.SHEET_HEADERS:
                logger.info("Sheet already initialized")
                return True
        except HttpError:
            pass
        
        # Create/update headers
        header_body = {
            'values': [config.SHEET_HEADERS]
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='A1:I1',
            valueInputOption='RAW',
            body=header_body
        ).execute()
        
        # Format header row (bold, frozen)
        requests = [
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {'bold': True},
                            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            },
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': 0,
                        'gridProperties': {'frozenRowCount': 1}
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            }
        ]
        
        body = {'requests': requests}
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()
        
        logger.info("Sheet initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Failed to initialize sheet: {str(e)}")
        return False


def add_job(job_data: Dict) -> bool:
    """
    Append job to sheet.
    
    Args:
        job_data: Dictionary with job information
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Adding job to sheet: {job_data.get('position', 'Unknown')}")
    
    try:
        service = _get_sheets_service()
        sheet_id = config.GOOGLE_SHEET_ID
        
        # Format deadline
        deadline_str = ""
        days_left = ""
        if job_data.get('deadline'):
            if isinstance(job_data['deadline'], datetime):
                deadline_str = job_data['deadline'].strftime('%Y-%m-%d')
                days_left = str(utils.calculate_days_left(job_data['deadline']))
            else:
                deadline_str = str(job_data['deadline'])
        
        # Format added_on timestamp
        added_on_str = ""
        if job_data.get('added_on'):
            if isinstance(job_data['added_on'], datetime):
                added_on_str = job_data['added_on'].strftime('%Y-%m-%d %H:%M')
            else:
                added_on_str = str(job_data['added_on'])
        else:
            added_on_str = utils.get_current_time().strftime('%Y-%m-%d %H:%M')
        
        # Prepare row data
        row = [
            job_data.get('company', 'Unknown'),
            job_data.get('position', 'Unknown'),
            deadline_str,
            days_left,
            job_data.get('url', ''),
            'Open',  # Status
            job_data.get('salary', ''),
            job_data.get('location', ''),
            added_on_str
        ]
        
        # Append row
        body = {'values': [row]}
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range='A:I',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        logger.info(f"Job added successfully: {result.get('updates', {}).get('updatedRows', 0)} row(s) added")
        
        # Apply conditional formatting to days left
        _apply_conditional_formatting()
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to add job to sheet: {str(e)}")
        return False


def get_upcoming_deadlines(days: int = 7) -> List[Dict]:
    """
    Get jobs with deadlines in next N days.
    
    Args:
        days: Number of days to look ahead
        
    Returns:
        List of job dictionaries
    """
    logger.info(f"Getting upcoming deadlines (next {days} days)")
    
    try:
        service = _get_sheets_service()
        sheet_id = config.GOOGLE_SHEET_ID
        
        # Get all rows
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range='A2:I'  # Skip header
        ).execute()
        
        values = result.get('values', [])
        jobs = []
        
        now = utils.get_current_time()
        
        for row in values:
            if len(row) < 6:  # Ensure minimum columns
                continue
            
            # Parse deadline
            try:
                deadline_str = row[2] if len(row) > 2 else ''
                if not deadline_str:
                    continue
                
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                deadline = config.TIMEZONE.localize(deadline)
                
                days_until = utils.calculate_days_left(deadline)
                
                # Check if within range and not applied
                status = row[5] if len(row) > 5 else 'Open'
                if 0 <= days_until <= days and status != 'Applied':
                    job = {
                        'company': row[0] if len(row) > 0 else '',
                        'position': row[1] if len(row) > 1 else '',
                        'deadline': deadline,
                        'days_left': days_until,
                        'url': row[4] if len(row) > 4 else '',
                        'status': status,
                        'salary': row[6] if len(row) > 6 else '',
                        'location': row[7] if len(row) > 7 else ''
                    }
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"Failed to parse job row: {str(e)}")
                continue
        
        # Sort by deadline (nearest first)
        jobs.sort(key=lambda x: x['deadline'])
        
        logger.info(f"Found {len(jobs)} upcoming deadlines")
        return jobs
    
    except Exception as e:
        logger.error(f"Failed to get upcoming deadlines: {str(e)}")
        return []


def mark_as_applied(row_number: int) -> bool:
    """
    Update status to 'Applied' for a specific row.
    
    Args:
        row_number: Row number (1-based, excluding header)
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Marking row {row_number} as applied")
    
    try:
        service = _get_sheets_service()
        sheet_id = config.GOOGLE_SHEET_ID
        
        # Row number + 1 for header
        actual_row = row_number + 1
        
        # Update status column (F)
        body = {'values': [['Applied']]}
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f'F{actual_row}',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        logger.info(f"Row {row_number} marked as applied")
        return True
    
    except Exception as e:
        logger.error(f"Failed to mark job as applied: {str(e)}")
        return False


def update_days_left() -> bool:
    """
    Recalculate days left for all jobs.
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Updating days left for all jobs")
    
    try:
        service = _get_sheets_service()
        sheet_id = config.GOOGLE_SHEET_ID
        
        # Get all rows
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range='A2:I'
        ).execute()
        
        values = result.get('values', [])
        updates = []
        
        for idx, row in enumerate(values, start=2):
            if len(row) < 3:
                continue
            
            deadline_str = row[2] if len(row) > 2 else ''
            if not deadline_str:
                continue
            
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                deadline = config.TIMEZONE.localize(deadline)
                days_left = utils.calculate_days_left(deadline)
                
                updates.append({
                    'range': f'D{idx}',
                    'values': [[str(days_left)]]
                })
            except Exception as e:
                logger.warning(f"Failed to update row {idx}: {str(e)}")
                continue
        
        if updates:
            body = {
                'valueInputOption': 'RAW',
                'data': updates
            }
            
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body=body
            ).execute()
            
            logger.info(f"Updated {len(updates)} rows")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to update days left: {str(e)}")
        return False


def _apply_conditional_formatting():
    """Apply conditional formatting to days left column."""
    try:
        service = _get_sheets_service()
        sheet_id = config.GOOGLE_SHEET_ID
        
        requests = [
            # Red: < 3 days
            {
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{'sheetId': 0, 'startColumnIndex': 3, 'endColumnIndex': 4}],
                        'booleanRule': {
                            'condition': {
                                'type': 'NUMBER_LESS',
                                'values': [{'userEnteredValue': '3'}]
                            },
                            'format': {
                                'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
                            }
                        }
                    },
                    'index': 0
                }
            },
            # Yellow: < 7 days
            {
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{'sheetId': 0, 'startColumnIndex': 3, 'endColumnIndex': 4}],
                        'booleanRule': {
                            'condition': {
                                'type': 'NUMBER_LESS',
                                'values': [{'userEnteredValue': '7'}]
                            },
                            'format': {
                                'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.8}
                            }
                        }
                    },
                    'index': 1
                }
            }
        ]
        
        body = {'requests': requests}
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()
    except Exception as e:
        logger.warning(f"Failed to apply conditional formatting: {str(e)}")


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    initialize_sheet()
