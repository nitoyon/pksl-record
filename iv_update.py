"""
Pokemon Sleep Individual Pokemon Recorder for Google Sheets

iv_add.py ユーザーID ユーザー表示名 ニックネーム ポケモン名 スキル確率アップMの有無 スキル確率アップSの有無 せいかくの変化量
"""

import sys
import io
from datetime import date
import yaml


def _load_spreadsheet_id():
    with open('conf/config.yaml', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config['NUZZLE_SHEET_ID']

# Windows (cp932) で絵文字の出力エラーを回避する
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class IvRecorder:
    """Handles Pokemon Sleep individual pokemon data recording to Google Sheets"""

    # コマンドライン引数と記録先の列の対応
    # A: ユーザーID, B: ユーザー表示名, B: ニックネーム, C: ポケモン名,
    # D: スキルM, E: スキルS, F: せいかく変化量
    COLUMNS = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

    def __init__(self, service_account_file='conf/google-credentials.json',
                 spreadsheet_id=None,
                 sheet_name='ポケモン登録'):
        self.service_account_file = service_account_file
        self.spreadsheet_id = spreadsheet_id or _load_spreadsheet_id()
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

    def get_all_rows(self):
        """
        Get all rows from the sheet.

        Returns:
            list: list of rows (each row is a list of cell values)
        """
        range_name = f"'{self.sheet_name}'!A:G"
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
        ).execute()
        return result.get('values', [])

    def find_row(self, user_id, nickname):
        """
        Find the row number for the given user_id and nickname.

        Returns:
            int: row number (1-based), or None if not found
        """
        rows = self.get_all_rows()
        for i, row in enumerate(rows):
            row_user_id = row[0] if len(row) > 0 else ''
            row_nickname = row[2] if len(row) > 2 else ''
            if row_user_id == user_id and row_nickname == nickname:
                return i + 1  # 1-based
        return None

    def record(self, user_id, user_name, nickname, pokemon_name, skill_m, skill_s, nature_delta):
        """
        Record individual pokemon data to Google Sheets.
        If a row with the same user_id and nickname exists, update it.

        Args:
            user_id: ユーザーID
            user_name: ユーザー表示名
            nickname: ニックネーム
            pokemon_name: ポケモン名
            skill_m: スキル確率アップMの有無 (0 or 1)
            skill_s: スキル確率アップSの有無 (0 or 1)
            nature_delta: せいかくの変化量 (-1, 0, 1)
        """
        if self.sheets_service is None:
            self.init_sheets()

        existing_row = self.find_row(user_id, nickname)
        if existing_row is not None:
            target_row = existing_row
            action = f"🔄 行{target_row}を更新"
        else:
            rows = self.get_all_rows()
            target_row = len(rows) + 1
            action = f"📝 行{target_row}に追加"

        values = [user_id, user_name, nickname, pokemon_name, skill_m, skill_s, nature_delta]

        data = []
        for col, val in zip(self.COLUMNS, values):
            data.append({
                'range': f"'{self.sheet_name}'!{col}{target_row}",
                'values': [[val]],
            })

        print(f"{action}: [{user_id}] {user_name} / {pokemon_name} ({nickname}) "
              f"スキルM={skill_m} スキルS={skill_s} せいかく={nature_delta}")

        result = self.sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'valueInputOption': 'USER_ENTERED', 'data': data},
        ).execute()
        updated = result.get('totalUpdatedCells', 0)
        print(f"✅ {updated} cell(s) updated")
        return True


if __name__ == '__main__':
    if len(sys.argv) != 8:
        print(f"Usage: {sys.argv[0]} ユーザーID ユーザー表示名 ニックネーム ポケモン名 スキル確率アップMの有無 スキル確率アップSの有無 せいかくの変化量")
        print(f"Example: {sys.argv[0]} nitoyon2 nitoyon ピカチュウくん ピカチュウ 1 0 1")
        sys.exit(1)

    user_id = sys.argv[1]
    user_name = sys.argv[2]
    nickname = sys.argv[3]
    pokemon_name = sys.argv[4]
    skill_m = int(sys.argv[5])
    skill_s = int(sys.argv[6])
    nature_delta = int(sys.argv[7])

    recorder = IvRecorder()
    ok = recorder.record(user_id, user_name, nickname, pokemon_name, skill_m, skill_s, nature_delta)
    sys.exit(0 if ok else 1)
