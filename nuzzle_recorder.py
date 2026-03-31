"""
Pokemon Sleep Nuzzle (ほっぺすりすり) Recorder for Google Sheets

nuzzle_recorder.py 日時 チャンネル名 ユーザーID ユーザー表示名 発動者 スキルレベル 回復対象 追加ボーナスの有無
"""

import sys
import io
from datetime import date, datetime, timezone, timedelta
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


class NuzzleRecorder:
    """Handles Pokemon Sleep nuzzle skill data recording to Google Sheets"""

    # コマンドライン引数と記録先の列の対応
    # A: 日付, B: チャンネル名, C: ユーザーID, D: ユーザー表示名, E: 発動者
    # F: スキルレベル, G: 回復対象, H: 追加ボーナス
    COLUMNS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

    def __init__(self, service_account_file='conf/google-credentials.json',
                 spreadsheet_id=None,
                 sheet_name='スキル記録'):
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

    def record(self, created, channel_name, user_id, user_name, skill_user, skill_level, target, bonus):
        """
        Record nuzzle skill data to Google Sheets.

        Args:
            created: 発動日時 (ISO 8601 format)
            channel_name: チャンネル名
            user_id: ユーザーID
            user_name: ユーザー表示名
            skill_user: 発動者
            skill_level: スキルレベル (1-6)
            target: 回復対象 (ポケモン名)
            bonus: 追加ボーナスの有無 (0 or 1)
        """
        if self.sheets_service is None:
            self.init_sheets()

        last_row = self.get_last_row()
        new_row = last_row + 1

        JST = timezone(timedelta(hours=9))
        dt = datetime.fromisoformat(created.replace('Z', '+00:00')).astimezone(JST)
        created_str = dt.strftime('%Y-%m-%d %H:%M:%S')

        values = [created_str, channel_name, user_id, user_name, skill_user, skill_level, target, bonus]

        data = []
        for col, val in zip(self.COLUMNS, values):
            data.append({
                'range': f"'{self.sheet_name}'!{col}{new_row}",
                'values': [[val]],
            })

        print(f"📝 行{new_row}: {created} [{user_id}] {user_name} "
              f"SLv{skill_level} 対象={target} 追加ボーナス={bonus}")

        result = self.sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'valueInputOption': 'USER_ENTERED', 'data': data},
        ).execute()

        updated = result.get('totalUpdatedCells', 0)
        print(f"✅ {updated} cell(s) updated")
        return True


if __name__ == '__main__':
    if len(sys.argv) != 9:
        print(f"Usage: {sys.argv[0]} 日時 チャンネル名 ユーザーID ユーザー表示名 発動者 スキルレベル 回復対象 追加ボーナスの有無")
        print(f"Example: {sys.argv[0]} 2024-01-01T12:00:00.000Z general nitoyon2 nitoyon 温丸 6 おてぼんね 1")
        sys.exit(1)

    created = sys.argv[1]
    channel_name = sys.argv[2]
    user_id = sys.argv[3]
    user_name = sys.argv[4]
    skill_user = sys.argv[5]
    skill_level = int(sys.argv[6])
    target = sys.argv[7]
    bonus = int(sys.argv[8])

    recorder = NuzzleRecorder()
    ok = recorder.record(created, channel_name, user_id, user_name, skill_user, skill_level, target, bonus)
    sys.exit(0 if ok else 1)
