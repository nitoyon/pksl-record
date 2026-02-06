# DiscordBot

## Python 環境

このプロジェクトでは venv を使用している。Python スクリプトを実行する際は、環境に応じたパスを使うこと。

- Windows: `venv\Scripts\python`
- Linux (WSL2): `venv-linux/bin/python`

### Windows 環境での注意点

Windows 環境では Bash ツールの既定シェルが bash であるため、パス区切りにバックスラッシュ (`\`) ではなくフォワードスラッシュ (`/`) を使うこと。

```
venv/Scripts/python script.py
```
