# ポケスリ記録スキル集

## セットアップ手順

### 1. リポジトリのクローン/ダウンロード

このプロジェクトをローカル環境にクローンまたはダウンロードします。

### 2. 依存関係のインストール

仮想環境を作成し、必要なパッケージをインストールします:


```bash
# 仮想環境の作成（オプションですが推奨）
python -m venv venv

# 仮想環境の有効化
## Windows の場合
venv\Scripts\activate
## macOS/Linuxの場合:
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

`conf/google-credentials.json` に Google スプレッドシートにアクセス可能なサービスアカウントのトークンを配置します。

https://console.cloud.google.com/iam-admin/serviceaccounts/
