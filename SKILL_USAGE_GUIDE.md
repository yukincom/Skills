# Gemini Image Analysis Skill - Quick Start Guide

## 📦 What's Included

このスキルには以下が含まれています：

### Core Documentation
- **SKILL.md** - メインガイド（よくあるミスと解決策）
- **references/troubleshooting-guide.md** - 詳細なエラー対処法
- **references/complete-script-template.py** - すぐ使える完全なスクリプト

### Utility Scripts
- **scripts/validate_images.py** - 画像の事前チェック
- **scripts/merge_results.py** - 複数のExcel結果を統合

---

## 🚀 このスキルでできること

1. **大量画像の自動分析** (10〜1000枚以上)
2. **カスタムカテゴリーでの分類** (有無判定、複数選択、程度評価)
3. **Excel形式での結果出力**
4. **Google Cloud Storage / Google Driveからの画像読み込み**

---

## 💡 使い方

### パターン1: 基本的な使い方

**ユーザー**: 「600枚の画像を分析して、それぞれにAIの表情、デバイスの有無、本の量を判定してExcelに出力したい」

**Claude**: このスキルを使用して：
1. カテゴリー定義を作成
2. GCSバケットの画像を読み込み
3. バッチ処理で分析
4. Excel出力

### パターン2: トラブルシューティング

**ユーザー**: 「エラーが出て動かない...」

**Claude**: スキルのトラブルシューティングガイドを参照して：
1. エラーメッセージから原因を特定
2. 段階的な解決策を提示
3. 必要に応じてスクリプト修正

### パターン3: 既存スクリプトの改善

**ユーザー**: 「このスクリプト、よく失敗するんだけど...」

**Claude**: スキルの「よくある落とし穴」セクションをチェックして：
1. 隠しファイルフィルタリング追加
2. リトライロジック実装
3. MIME type自動判定

---

## 🎯 スキルが自動でカバーする初心者のミス

### 1. macOSの隠しファイル
❌ **よくあるミス**: `._`ファイルが原因で "invalid image" エラー
✅ **スキルの対処**: 自動フィルタリングのコード例を提供

### 2. モデル名の間違い
❌ **よくあるミス**: `gemini-2.5-flash` (存在しないモデル)
✅ **スキルの対処**: 正しいモデル名リストを提示

### 3. MIME typeのミスマッチ
❌ **よくあるミス**: `.webp`ファイルに `image/jpeg` を指定
✅ **スキルの対処**: 拡張子から自動判定するコード

### 4. レート制限エラー
❌ **よくあるミス**: 429エラーでスクリプトが止まる
✅ **スキルの対処**: 指数バックオフのリトライロジック

### 5. 仮想環境の混乱
❌ **よくあるミス**: venv内で実行してるのにライブラリがない
✅ **スキルの対処**: 環境チェック方法と修正手順

### 6. 認証エラー
❌ **よくあるミス**: Application Default Credentials未設定
✅ **スキルの対処**: `gcloud auth application-default login` など具体的コマンド

---

## 📚 スキルの構成

```
gemini-image-analysis/
├── SKILL.md                              # メインガイド
│   ├── Quick Start                       # 前提条件チェック
│   ├── Critical Pitfalls                 # よくある6つのミス
│   ├── Schema Definition                 # カテゴリー定義方法
│   ├── Batch Processing Optimization     # バッチサイズと待機時間
│   ├── Cost Estimation                   # 料金計算
│   └── Troubleshooting                   # 基本的な対処法
│
├── references/
│   ├── complete-script-template.py       # 本番レディのスクリプト
│   └── troubleshooting-guide.md          # 詳細なエラー対処
│       ├── Authentication Errors
│       ├── API Errors
│       ├── Model Errors
│       ├── Data Errors
│       ├── Environment Errors
│       ├── File System Errors
│       ├── Performance Issues
│       ├── Quality Issues
│       └── Recovery Strategies
│
└── scripts/
    ├── validate_images.py                # 画像の事前検証
    └── merge_results.py                  # 結果の統合
```

---

## 🔍 スキルを使う具体例

### 例1: スクリプト作成を依頼された場合

```
User: 500枚の画像を分析して、感情とデバイスを判定したい

Claude: 
1. [SKILL.mdを読む]
2. カテゴリー定義を確認
3. complete-script-template.pyをベースに作成
4. 隠しファイルフィルタ、MIMEタイプ判定、リトライロジックを自動で含める
5. ユーザーに設定箇所（PROJECT_ID等）を説明
```

### 例2: エラーが出た場合

```
User: "429 Resource exhausted" って出たんだけど

Claude:
1. [troubleshooting-guide.mdを読む]
2. レート制限エラーのセクションを参照
3. 指数バックオフコードを提示
4. バッチサイズ調整も提案
```

### 例3: 品質改善を求められた場合

```
User: 結果が不正確なんだけど

Claude:
1. [SKILL.mdのQuality Issuesセクション]
2. プロンプトに具体例を追加する方法
3. カテゴリーをシンプルにする提案
4. より高品質なモデルへの変更方法
```

---

## 💰 コスト例（参考）

- **100枚**: 約¥1
- **600枚**: 約¥6
- **1000枚**: 約¥10

（Gemini 2.0 Flash使用時の目安）

---

## ✨ スキルの強み

1. **網羅性**: 初心者が陥りやすいミスをすべてカバー
2. **実用性**: すぐ動かせるテンプレート付き
3. **段階的**: Quick Start → 詳細ガイド → トラブルシューティング
4. **自己完結**: 外部ドキュメントへの依存なし

---

## 🎓 学習曲線

### レベル1: 初心者（このスキルで十分）
- テンプレートをコピペして実行
- エラーが出たらトラブルシューティングガイド参照

### レベル2: 中級者
- カテゴリー定義をカスタマイズ
- バッチサイズを最適化
- 複数の結果を統合

### レベル3: 上級者
- Google Drive連携を追加
- 並列処理を実装
- カスタムバリデーションロジック

---

## 📞 サポート

このスキルで解決できないこと：
- **Vertex AIの初期設定** → 公式ドキュメント参照
- **GCPアカウント作成** → Googleサポート
- **独自モデルの学習** → 別のスキルが必要

それ以外の**Gemini画像分析に関するすべて**はこのスキルでカバー！
