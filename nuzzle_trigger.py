"""
ほっぺすりすり記録スクリプト

標準入力からプロンプトを受け取り、.tmp フォルダの画像を OCR 処理してから
スプレッドシートに記録し、Discord 用メッセージを stdout に出力する。

stdin 形式 (プロンプトをそのまま渡す):
  username: <ユーザー名>
  displayname: <表示名>
  channelname: <チャンネル名>
  created: <ISO 8601 日時>
"""

import sys
import io
import re
import os
import glob
from pathlib import Path
import subprocess

if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stdin.encoding and sys.stdin.encoding.lower().startswith('cp'):
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

from nuzzle_recorder import NuzzleRecorder


SKILL_RE = re.compile(r'ほっぺすりすり[（(]げんきエールS[）)]Lv[．.]\s*(\d+)')
MAINSK_RE = re.compile(r'(.+?)のメインスキル[!！]')
GENKI_RE = re.compile(r'(.+?)のげんきが(\d+)回復[!！]')
BONUS_RE = re.compile(r'さらに、.+?はメインスキルの準備が整った[!！]')

ENERGY = "<:energy:1488038051832791132>"
BONUS_ICON = "<:bonus:1488040085499809792>"
NOBONUS_ICON = "<:nobonus:1488040146250240041>"


def parse_meta(text):
    meta = {}
    for line in text.splitlines():
        m = re.match(r'^(\w+):\s*(.+)$', line.strip())
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta


def parse_ocr(text):
    """OCR テキストからスキル発動情報のリストを返す。

    スキルが2回発動している場合、OCR テキスト上の出現順で返す。
    (下のスキルが1回目として先に記録されるよう呼び出し側で逆順にする)
    """
    skills = []
    matches = list(SKILL_RE.finditer(text))
    for i, m in enumerate(matches):
        level = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segment = text[start:end]

        mu = MAINSK_RE.search(segment)
        mg = GENKI_RE.search(segment)

        if mu and mg:
            skills.append({
                'level': level,
                'user': mu.group(1),
                'target': mg.group(1),
                'bonus': 1 if BONUS_RE.search(segment) else 0,
            })

    return skills


def cleanup_tmp():
    for pattern in ['.tmp/*.txt', '.tmp/*.json', '.tmp/*.xml']:
        for f in glob.glob(pattern):
            os.remove(f)


def main():
    prompt = sys.stdin.read()
    meta = parse_meta(prompt)

    msg_id = meta.get('id', '')
    username = meta.get('username', '')
    displayname = meta.get('displayname', username)
    channelname = meta.get('channelname', '')
    created = meta.get('created', '')
    attachments = meta.get('attachments', '').split(' ')

    print(f"!discord reaction {msg_id} 👀", flush=True)
    print("OCR開始します...", flush=True)

    png_files = glob.glob('.tmp/*.png')
    if not png_files:
        print("エラー: .tmp フォルダに画像ファイルが見つかりません", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        [r'ndl-ocr\.venv\Scripts\python', r'ndl-ocr\src\ocr.py',
         '--sourcedir', '.tmp', '--output', '.tmp'],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    if result.returncode != 0:
        print(f"OCR エラー:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    print("OCR完了しました", flush=True)

    recorder = NuzzleRecorder()
    all_records = []
    errors = []

    for index, attachment in enumerate(attachments):
        text_path = Path(attachment).with_suffix('.txt')
        if not text_path:
            errors.append(f"OCR結果がみつかりません: {os.path.basename(attachment)}")
            continue
        with open(text_path, encoding='utf-8') as f:
            text = f.read()

        skills = parse_ocr(text)
        if not skills:
            errors.append(f"スキル発動が見つかりませんでした: {os.path.basename(attachment)}")
            continue
        print(f"{index+1}枚目の写真: スキル{len(skills)}回", flush=True)

        # 2回発動の場合、OCR では上(2回目)が先に現れるため逆順で記録する
        for skill in reversed(skills):
            try:
                recorder.record(created, channelname, username, displayname,
                                skill['user'], skill['level'],
                                skill['target'], skill['bonus'])
                all_records.append(skill)
            except Exception as e:
                errors.append(f"記録エラー ({os.path.basename(attachment)}): {e}")

    lines = [f"📝{displayname}さんのすりすりを記録しました"]
    for r in all_records:
        bonus_str = BONUS_ICON if r['bonus'] else NOBONUS_ICON
        lines.append(f"* {ENERGY}{r['user']} (Lv.{r['level']}) {bonus_str} {r['target']}")
    for e in errors:
        lines.append(f"* ⚠️ {e}")
    print("!discord reply <<EOF\n%s\nEOF" % '\n'.join(lines))
    print(f"!discord reaction {msg_id} -👀", flush=True)
    print(f"!discord reaction {msg_id} ✅", flush=True)

    cleanup_tmp()

if __name__ == '__main__':
    main()
