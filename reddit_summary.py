import sys
import io
import re
import argparse
import html
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# Windows cp932 対策
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TOP_RSS = "https://www.reddit.com/r/PokemonSleep/top.rss?t=day&limit=10"
POST_RSS = "https://www.reddit.com/comments/{post_id}.rss?sort=best&limit={limit}"
HEADERS = {"User-Agent": "pksl-record/1.0"}

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
}


def fetch_xml(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return ET.fromstring(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {e.code} ({url})", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def extract_post_id(url):
    m = re.search(r'/comments/([a-z0-9]+)', url)
    if not m:
        print(f"Error: URL から post_id を抽出できませんでした: {url}", file=sys.stderr)
        sys.exit(1)
    return m.group(1)


def strip_html(text):
    return html.unescape(re.sub(r'<[^>]+>', '', text or '')).strip()


def parse_entry(entry):
    title = (entry.findtext("atom:title", namespaces=NS) or "").strip()
    link_el = entry.find("atom:link", NS)
    url = link_el.get("href", "") if link_el is not None else ""
    content = strip_html(entry.findtext("atom:content", namespaces=NS) or "")
    author = (entry.findtext("atom:author/atom:name", namespaces=NS) or "").strip()
    return {"title": title, "url": url, "content": content, "author": author}


def fetch_post_by_url(url, num_comments):
    post_id = extract_post_id(url)

    # 投稿本体
    root = fetch_xml(TOP_RSS)
    post_entry = None
    for entry in root.findall("atom:entry", NS):
        link_el = entry.find("atom:link[@rel='alternate']", NS)
        href = link_el.get("href", "") if link_el is not None else ""
        if post_id in href:
            post_entry = entry
            break

    # 投稿が top10 にない場合は RSS から直接取得
    if post_entry is None:
        root = fetch_xml(f"https://www.reddit.com/comments/{post_id}.rss?limit=1")
        entries = root.findall("atom:entry", NS)
        post_entry = entries[0] if entries else None

    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    print(f"取得日時: {now}")

    if post_entry is not None:
        p = parse_entry(post_entry)
        print(f"URL: {p['url']}")
        print()
        print(f"タイトル: {p['title']}")
        print()
        if p["content"]:
            print(f"本文:\n{p['content']}")
        else:
            print("本文: (画像/リンク投稿)")
        print()

    # コメント取得
    if num_comments > 0:
        croot = fetch_xml(POST_RSS.format(post_id=post_id, limit=num_comments))
        entries = croot.findall("atom:entry", NS)
        # 最初のエントリは投稿本体なので除外
        comment_entries = entries[1:num_comments + 1]
        if comment_entries:
            print(f"コメント ({len(comment_entries)}件):")
            for e in comment_entries:
                author = (e.findtext("atom:author/atom:name", namespaces=NS) or "").strip()
                body = strip_html(e.findtext("atom:content", namespaces=NS) or "")
                print(f"  [{author}] {body}")
                print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--comments", type=int, default=0, metavar="N",
                        help="投稿詳細表示時にコメントを N 件取得する (--url 指定時のみ有効)")
    parser.add_argument("--url", type=str, default=None, metavar="URL",
                        help="特定の Reddit 投稿 URL を指定して詳細取得する")
    args = parser.parse_args()

    if args.url:
        num_comments = args.comments if args.comments > 0 else 50
        fetch_post_by_url(args.url, num_comments)
        return

    root = fetch_xml(TOP_RSS)
    entries = root.findall("atom:entry", NS)

    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    print(f"取得日時: {now}")
    print("期間: 過去24時間のトップ投稿 (r/PokemonSleep)")
    print()

    for i, entry in enumerate(entries, 1):
        p = parse_entry(entry)
        body = p["content"][:300] + ("..." if len(p["content"]) > 300 else "") if p["content"] else "(画像/リンク投稿)"
        print(f"[{i}] {p['title']}")
        print(f"    URL: {p['url']}")
        print(f"    本文: {body}")
        print()


if __name__ == "__main__":
    main()
