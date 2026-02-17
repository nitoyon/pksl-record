"""
Pokemon Sleep Skill Recorder for Google Sheets

skill_recorder.py YYYY-MM-DD hh:mm ポケモン名 スキル回数
"""

import sys
import io
from datetime import date

# Windows (cp932) で絵文字の出力エラーを回避する
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class SkillRecorder:
    """Handles Pokemon Sleep skill data recording to Google Sheets"""

    def __init__(self, service_account_file='conf/google-credentials.json',
                 spreadsheet_id='11HR57XGS5ST-a5iF9dq-qND5EXFriFs-bnSPqZTEtgw',
                 sheet_name='スキル記録'):
        self.service_account_file = service_account_file
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.sheets_service = None

    def init_sheets(self):
        """Initialize Google Sheets API"""
        if self.sheets_service is not None:
            return

        print("📊 Initializing Google Sheets API...")
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(
            self.service_account_file, scopes=scopes
        )
        self.sheets_service = build('sheets', 'v4', credentials=creds)
        print("✓ Google Sheets API initialized successfully")

    def get_last_row(self):
        """
        Get the last row number with data in column A of the sheet.

        Returns:
            int: last row number (1-based), or 0 if the sheet is empty
        """
        range_name = f"'{self.sheet_name}'!A:A"
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
        ).execute()

        values = result.get('values', [])
        return len(values)

    def record(self, target_date, time_str, pokemon_name, count):
        """
        Record skill data to Google Sheets.

        Args:
            target_date: date object
            time_str: time string in hh:mm format
            pokemon_name: pokemon name string
            count: skill count (1 or 2)
        """
        if count not in (1, 2):
            print(f"❌ スキル回数は 1 または 2 を指定してください: {count}")
            return False

        if self.sheets_service is None:
            self.init_sheets()

        last_row = self.get_last_row()
        new_row = last_row + 1

        data = []
        for i in range(count):
            row = new_row + i
            data.extend([
                {
                    'range': f"'{self.sheet_name}'!A{row}",
                    'values': [[target_date.isoformat()]],
                },
                {
                    'range': f"'{self.sheet_name}'!B{row}",
                    'values': [[time_str]],
                },
                {
                    'range': f"'{self.sheet_name}'!C{row}",
                    'values': [[pokemon_name]],
                },
            ])

        print(f"📝 行{new_row}: {target_date} {time_str} {pokemon_name} x{count}")

        result = self.sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'valueInputOption': 'RAW', 'data': data},
        ).execute()

        updated = result.get('totalUpdatedCells', 0)
        print(f"✅ {updated} cell(s) updated")
        return True


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} YYYY-MM-DD hh:mm ポケモン名 スキル回数")
        print(f"Example: {sys.argv[0]} 2026-02-16 12:30 ピカチュウ 1")
        sys.exit(1)

    target_date = date.fromisoformat(sys.argv[1])
    time_str = sys.argv[2]
    pokemon_name = sys.argv[3]
    count = int(sys.argv[4])

    recorder = SkillRecorder()
    ok = recorder.record(target_date, time_str, pokemon_name, count)
    sys.exit(0 if ok else 1)