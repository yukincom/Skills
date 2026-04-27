# LINE通知 + M5Stack 音声連携 修正版

今回は構成を整理し、**`voice_handler.py` を使わない**形に変更しました。

- `server.py`（El Capitan 側アプリ）
- `voice_server.py`（M4 側の音声生成サーバー）

## 方針

- 音声生成は M4 側 `voice_server.py` のみで実行。
- El Capitan 側 `server.py` は `requests` で M4 の `/generate` を直接呼ぶ。
- El Capitan 側は生成済み音声の URL を保持し、`/voice/latest` で M4 音声をプロキシ返却する。

## 主な修正点

### server.py (El Capitan)

- `voice_handler` の import を削除。
- `generate_voice()` を `server.py` 内に実装（`VOICE_SERVER_URL/generate` へ直接POST）。
- `cleanup_old_voice_files()` を `server.py` 内に実装（`VOICE_SERVER_URL/cleanup` へ直接POST）。
- 生成失敗時は `latest_ready=False` のままにして古い音声再配信を防止。
- `/health` に `voice_server` 接続先を表示して確認しやすくした。

### voice_server.py (M4)

- `/generate` のデフォルト音声を `O-Ren` に統一。
- `say` + `afconvert` でWAV生成、保存、`/voice/<voice_id>` で配信。
- `/voices` を追加（`say -v ?` の一覧取得）。
- `/cleanup` で古いWAV削除。

## 環境変数

El Capitan 側 `.env`:

```env
VOICE_SERVER_URL=http://192.168.1.48:5001
VOICE_REQUEST_TIMEOUT=30
```

M4 側（必要なら）:

```env
VOICE_STORAGE_DIR=/tmp/voice_gen_store
```

## 動作確認

```bash
curl http://<M4_IP>:5001/health
curl http://<M4_IP>:5001/voices
curl http://<ELCAP_IP>:5000/health
```


## 声が変わらない時の確認ポイント

1. `server.py` の `/health` で `voice_default` が期待通りか確認
2. M4 の `/voices` で指定した音声名が存在するか確認
3. `/voice/latest` のレスポンスヘッダ `X-Voice-Name` を確認（実際に使われた声）
4. M5 側キャッシュ回避のため、`/voice/latest` は no-cache ヘッダ付き

```bash
curl http://<ELCAP_IP>:5000/health
curl http://<M4_IP>:5001/voices
curl -I http://<ELCAP_IP>:5000/voice/latest
```


## サンプルの `/tmp/test.aiff` が Finder で見えない件

- macOS の `/tmp` は実体が `/private/tmp` です。Finder で見る場合は `⌘+Shift+G` で以下を開いてください。
  - `/private/tmp`
  - `VOICE_TMP_DIR` に変更した場合はそのディレクトリ
- 現在の実装では `voice_server.py` の `/health` で `tmp_dir` と `storage_dir` を確認できます。

```bash
curl http://<M4_IP>:5001/health
```

## サンプリング周波数について

- `say` の生成AIFFは 22.05kHz になることがあります（これは正常）。
- その後 `afconvert` で `LEI16@44100` + `--src-complexity bats` を指定して 44.1kHz WAV に変換しています。
- そのため最終WAVは `afinfo` で 44.1kHz 表示になる想定です。
