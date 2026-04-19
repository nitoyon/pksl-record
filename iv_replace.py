"""
Pokemon Sleep Individual Pokemon Name Replacer for Google Sheets

Usage:
    iv_replace.py ユーザー名 旧ポケモン名 新ポケモン名
"""

import sys
import io
import yaml

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def _load_config():
    with open('conf/config.yaml', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config['NUZZLE_SHEET_ID']


def replace_pokemon_name(username, old_name, new_name,
                         service_account_file='conf/google-credentials.json',
                         spreadsheet_id=None,
                         sheet_name='ポケモン登録'):
    if spreadsheet_id is None:
        spreadsheet_id = _load_config()

    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    sheets = service.spreadsheets()

    # B列(ユーザー名)とC列(ポケモン名)を取得
    range_name = f"'{sheet_name}'!A:G"
    result = sheets.values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name,
    ).execute()

    rows = result.get('values', [])
    if not rows:
        print("シートにデータがありません")
        return

    updates = []
    for i, row in enumerate(rows):
        row_num = i + 1  # 1-based
        # B列: index 1, C列: index 2
        if len(row) > 2 and row[1] == username and row[2] == old_name:
            updates.append({
                'range': f"'{sheet_name}'!C{row_num}",
                'values': [[new_name]],
            })
            print(f"  行{row_num}: [{row[1]}] {row[2]} → {new_name}")

    if not updates:
        print(f"対象なし: ユーザー名={username}, 旧ポケモン名={old_name}")
        return

    print(f"\n{len(updates)}件を置換します...")
    result = sheets.values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'valueInputOption': 'USER_ENTERED', 'data': updates},
    ).execute()

    updated = result.get('totalUpdatedCells', 0)
    print(f"✅ {updated} cell(s) updated")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} ユーザー名 旧ポケモン名 新ポケモン名")
        print(f"Example: {sys.argv[0]} nitoyon ピカチュウ ライチュウ")
        sys.exit(1)

    replace_pokemon_name(sys.argv[1], sys.argv[2], sys.argv[3])
