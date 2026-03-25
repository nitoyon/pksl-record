"""
Pokemon Sleep Dish Recorder for Google Sheets

dish_recorder.py YYYY-MM-DD 朝|昼|晩 !|_ 料理名 エナジー
"""

import sys
import io
from datetime import date

# Windows (cp932) で絵文字の出力エラーを回避する
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from date_utils import calculate_row_number
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 料理の種類 → 列マッピング (大成功, 料理名, エナジー)
MEAL_COLUMNS = {
    '朝': ('L', 'M', 'N'),
    '昼': ('O', 'P', 'Q'),
    '晩': ('R', 'S', 'T'),
}


class DishRecorder:
    """Handles Pokemon Sleep dish data recording to Google Sheets"""

    def __init__(self, service_account_file='conf/google-credentials.json',
                 spreadsheet_id='11HR57XGS5ST-a5iF9dq-qND5EXFriFs-bnSPqZTEtgw',
                 sheet_name='記録'):
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

    def get_valid_dish_names(self, cell_range):
        """
        Get valid dish names from data validation on the given cell.

        Args:
            cell_range: e.g. "'記録'!M1152"

        Returns:
            list of str
        """
        result = self.sheets_service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id,
            ranges=[cell_range],
            fields='sheets.data.rowData.values.dataValidation'
        ).execute()

        try:
            dv = result['sheets'][0]['data'][0]['rowData'][0]['values'][0]['dataValidation']
            return [v['userEnteredValue'] for v in dv['condition']['values']]
        except (KeyError, IndexError):
            return []

    def find_dish_name(self, query, valid_names):
        """
        Find a dish name by partial match.

        Args:
            query: user input dish name
            valid_names: list of valid dish names from data validation

        Returns:
            str or None
        """
        matches = [name for name in valid_names if query in name]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            # 完全一致するものがあればそれを返す（重複登録対策）
            unique_matches = list(set(matches))
            if len(unique_matches) == 1:
                return unique_matches[0]
            print(f"❌ 複数の料理名が一致しました: {matches}")
            return None
        return None

    def record(self, target_date, meal_type, is_success, dish_name_query, energy):
        """
        Record dish data to Google Sheets.

        Args:
            target_date: date object
            meal_type: '朝', '昼', or '晩'
            is_success: True if 大成功
            dish_name_query: dish name to search
            energy: int value
        """
        if self.sheets_service is None:
            self.init_sheets()

        row = calculate_row_number(target_date)
        if row is None:
            print("❌ 行番号の計算に失敗しました")
            return False

        col_success, col_name, col_energy = MEAL_COLUMNS[meal_type]

        # 入力規則から料理名を部分一致で取得
        name_range = f"'{self.sheet_name}'!{col_name}{row}"
        valid_names = self.get_valid_dish_names(name_range)
        if not valid_names:
            print(f"❌ 入力規則が見つかりません: {name_range}")
            return False

        dish_name = self.find_dish_name(dish_name_query, valid_names)
        if dish_name is None:
            print(f"❌ 料理名が見つかりません: {dish_name_query}")
            print(f"   候補: {valid_names}")
            return False

        # batchUpdate で3セルをまとめて更新
        data = [
            {
                'range': f"'{self.sheet_name}'!{col_success}{row}",
                'values': [['❗️' if is_success else '']],
            },
            {
                'range': name_range,
                'values': [[dish_name]],
            },
            {
                'range': f"'{self.sheet_name}'!{col_energy}{row}",
                'values': [[energy]],
            },
        ]

        print(f"📝 {target_date} {meal_type}: {dish_name} ({energy:,})"
              + (" 大成功❗️" if is_success else ""))

        result = self.sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'valueInputOption': 'USER_ENTERED', 'data': data},
        ).execute()

        updated = result.get('totalUpdatedCells', 0)
        print(f"✅ {updated} cell(s) updated")
        return True


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print(f"Usage: {sys.argv[0]} YYYY-MM-DD 朝|昼|晩 !|_ 料理名 エナジー")
        print(f"Example: {sys.argv[0]} 2026-02-16 朝 ! カレー 4500")
        sys.exit(1)

    target_date = date.fromisoformat(sys.argv[1])
    meal_type = sys.argv[2]
    is_success = sys.argv[3] == '!'
    dish_name_query = sys.argv[4]
    energy = int(sys.argv[5])

    if meal_type not in MEAL_COLUMNS:
        print(f"❌ 料理の種類は 朝, 昼, 晩 のいずれかを指定してください: {meal_type}")
        sys.exit(1)

    recorder = DishRecorder()
    ok = recorder.record(target_date, meal_type, is_success, dish_name_query, energy)
    sys.exit(0 if ok else 1)
