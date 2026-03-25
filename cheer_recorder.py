"""
Pokemon Sleep Cheer Recorder for Google Sheets

cheer_recorder.py YYYY-MM-DD hh:mm げんき1 げんき2 げんき3 げんき4 げんき5 スキル種類 スキルレベル 対象ポケモン 回復量
"""

import sys
import io
from datetime import date

# Windows (cp932) で絵文字の出力エラーを回避する
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class CheerRecorder:
    """Handles Pokemon Sleep cheer skill data recording to Google Sheets"""

    # コマンドライン引数と記録先の列の対応
    COLUMNS = ['A', 'B', 'D', 'F', 'H', 'J', 'L', 'N', 'O', 'P', 'R']

    def __init__(self, service_account_file='conf/google-credentials.json',
                 spreadsheet_id='11HR57XGS5ST-a5iF9dq-qND5EXFriFs-bnSPqZTEtgw',
                 sheet_name='げんきエール'):
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

    def record(self, target_date, time_str, genki1, genki2, genki3, genki4,
               genki5, skill_type, skill_level, target_pokemon, recovery):
        """
        Record cheer skill data to Google Sheets.

        Args:
            target_date: date object
            time_str: time string in hh:mm format
            genki1: げんき1 (0-150)
            genki2: げんき2 (0-150)
            genki3: げんき3 (0-150)
            genki4: げんき4 (0-150)
            genki5: げんき5 (0-150)
            skill_type: スキル種類 (ほっぺすりすり/マイナス/げんきエール)
            skill_level: スキルレベル
            target_pokemon: 対象ポケモン (1-5)
            recovery: 回復量
        """
        if self.sheets_service is None:
            self.init_sheets()

        last_row = self.get_last_row()
        new_row = last_row + 1

        values = [
            target_date.isoformat(), time_str,
            genki1, genki2, genki3, genki4, genki5,
            skill_type, skill_level, target_pokemon, recovery,
        ]

        data = []
        for col, val in zip(self.COLUMNS, values):
            data.append({
                'range': f"'{self.sheet_name}'!{col}{new_row}",
                'values': [[val]],
            })

        print(f"📝 行{new_row}: {target_date} {time_str} "
              f"げんき=[{genki1},{genki2},{genki3},{genki4},{genki5}] "
              f"{skill_type} Lv{skill_level} 対象={target_pokemon} 回復={recovery}")

        result = self.sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'valueInputOption': 'USER_ENTERED', 'data': data},
        ).execute()

        updated = result.get('totalUpdatedCells', 0)
        print(f"✅ {updated} cell(s) updated")
        return True


if __name__ == '__main__':
    if len(sys.argv) != 12:
        print(f"Usage: {sys.argv[0]} YYYY-MM-DD hh:mm げんき1 げんき2 げんき3 げんき4 げんき5 スキル種類 スキルレベル 対象ポケモン 回復量")
        print(f"Example: {sys.argv[0]} 2026-02-17 12:30 100 80 60 40 20 げんきエール 6 3 5")
        sys.exit(1)

    target_date = date.fromisoformat(sys.argv[1])
    time_str = sys.argv[2]
    genki1 = int(sys.argv[3])
    genki2 = int(sys.argv[4])
    genki3 = int(sys.argv[5])
    genki4 = int(sys.argv[6])
    genki5 = int(sys.argv[7])
    skill_type = sys.argv[8]
    skill_level = int(sys.argv[9])
    target_pokemon = int(sys.argv[10])
    recovery = int(sys.argv[11])

    recorder = CheerRecorder()
    ok = recorder.record(target_date, time_str, genki1, genki2, genki3,
                         genki4, genki5, skill_type, skill_level,
                         target_pokemon, recovery)
    sys.exit(0 if ok else 1)