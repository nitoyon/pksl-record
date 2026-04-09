"""
Pokemon Sleep Nuzzle (ほっぺすりすり) Target Pokemon Replacer for Google Sheets

Usage:
    nuzzle_replace.py ユーザーID 旧ポケモン名 新ポケモン名
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


def replace_target(user_id, old_target, new_target,
                   service_account_file='conf/google-credentials.json',
                   spreadsheet_id=None,
                   sheet_name='スキル記録'):
    if spreadsheet_id is None:
        spreadsheet_id = _load_config()

    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)
    sheets = service.spreadsheets()

    # C列(ユーザーID)とG列(回復対象)を取得
    range_name = f"'{sheet_name}'!A:H"
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
        # C列: index 2, G列: index 6
        if len(row) > 6 and row[2] == user_id and row[6] == old_target:
            updates.append({
                'range': f"'{sheet_name}'!G{row_num}",
                'values': [[new_target]],
            })
            print(f"  行{row_num}: {row[0]} [{row[2]}] {row[6]} → {new_target}")

    if not updates:
        print(f"対象なし: ユーザーID={user_id}, 旧ポケモン名={old_target}")
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
        print(f"Usage: {sys.argv[0]} ユーザーID 旧ポケモン名 新ポケモン名")
        print(f"Example: {sys.argv[0]} nitoyon2 おてぼんね ブルー")
        sys.exit(1)

    replace_target(sys.argv[1], sys.argv[2], sys.argv[3])
