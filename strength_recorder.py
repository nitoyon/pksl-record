"""
Pokemon Sleep Strength Recorder for Google Sheets
"""

import sys
import io
from datetime import date, timedelta

# Windows (cp932) で絵文字の出力エラーを回避する
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class PokemonSleepRecorder:
    """Handles Pokemon Sleep data recording to Google Sheets"""

    def __init__(self, service_account_file='conf/google-credentials.json',
                 spreadsheet_id='11HR57XGS5ST-a5iF9dq-qND5EXFriFs-bnSPqZTEtgw',
                 sheet_name='記録'):
        """
        Initialize the recorder

        Args:
            service_account_file: Path to Google service account credentials JSON
            spreadsheet_id: Google Spreadsheet ID
            sheet_name: Sheet name to write to
        """
        self.service_account_file = service_account_file
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.sheets_service = None

    def init_sheets(self):
        """Initialize Google Sheets API"""
        if self.sheets_service is not None:
            return  # Already initialized

        try:
            print("📊 Initializing Google Sheets API...")
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(
                self.service_account_file, scopes=scopes
            )
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            print("✓ Google Sheets API initialized successfully")
        except Exception as e:
            print(f"✗ Error initializing Google Sheets API: {e}")
            raise

    def calculate_row_number(self, target_date):
        """
        Calculate spreadsheet row number from date

        Args:
            target_date: date object

        Returns:
            int or None
        """
        # Base: 2026/2/1 (Sun) = H1152
        base_date = date(2026, 2, 1)
        base_row = 1152

        if target_date < base_date:
            print(f"❌ {target_date} is before the base date")
            return None

        # Calculate row by iterating through dates
        current_date = base_date
        current_row = base_row

        while current_date < target_date:
            next_date = current_date + timedelta(days=1)

            # Sunday to Monday: +3, otherwise: +1
            if current_date.weekday() == 6 and next_date.weekday() == 0:
                current_row += 3
            else:
                current_row += 1

            current_date = next_date

        print(f"📍 Date {target_date} corresponds to row {current_row}")
        return current_row

    def update_spreadsheet(self, target_date, energy):
        """
        Update Google Sheets with energy data

        Args:
            target_date: date object
            energy: int value

        Returns:
            dict: Result with success status and update details
        """
        # Ensure Sheets API is initialized
        if self.sheets_service is None:
            self.init_sheets()

        row_number = self.calculate_row_number(target_date)
        if not row_number:
            return {
                'success': False,
                'error': 'Failed to calculate row number'
            }

        # Write to column H
        range_name = f"'{self.sheet_name}'!H{row_number}"

        body = {
            'values': [[energy]]
        }

        try:
            print(f"📝 Updating spreadsheet: {range_name} = {energy:,}")

            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()

            updated_cells = result.get('updatedCells', 0)
            print(f"✅ Update successful: {updated_cells} cell(s) updated")

            return {
                'success': True,
                'range': range_name,
                'row': row_number,
                'column': 'H',
                'value': energy,
                'updated_cells': updated_cells
            }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Spreadsheet update error: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def process_ocr_text(self, ocr_text):
        """
        Process OCR text: extract date and energy, then update spreadsheet

        Args:
            ocr_text: Text extracted from OCR

        Returns:
            dict: Result with status, date, energy, and message
        """
        # Extract date
        extracted_date = self.extract_date_from_text(ocr_text)
        if not extracted_date:
            return {
                'success': False,
                'message': "❌ Failed to extract date from image",
                'date': None,
                'energy': None
            }

        # Extract energy
        strength = self.extract_strength_from_text(ocr_text)
        if not strength:
            return {
                'success': False,
                'message': "❌ Failed to extract energy value from image",
                'date': extracted_date,
                'energy': None
            }

        # Update spreadsheet
        update_result = self.update_spreadsheet(extracted_date, strength)

        if update_result['success']:
            # Create detailed success message
            message = (
                f"🎉 Processing complete!\n"
                f"📅{extracted_date}\n"
                f"🔥{strength:,}\n"
                f"📊Updated {update_result['range']}"
            )
            return {
                'success': True,
                'message': message,
                'date': extracted_date,
                'strength': strength,
                'spreadsheet_update': update_result
            }
        else:
            error_detail = update_result.get('error', 'Unknown error')
            message = f"❌ Failed to update spreadsheet: {error_detail}"
            return {
                'success': False,
                'message': message,
                'date': extracted_date,
                'energy': strength,
                'error': error_detail
            }


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} YYYY-MM-DD strength")
        print(f"Example: {sys.argv[0]} 2026-02-01 1999819")
        sys.exit(1)

    target_date = date.fromisoformat(sys.argv[1])
    strength = int(sys.argv[2])

    recorder = PokemonSleepRecorder()
    result = recorder.update_spreadsheet(target_date, strength)
    if 'message' in result:
        print(result['message'])
    sys.exit(0 if result['success'] else 1)
