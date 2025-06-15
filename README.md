# Realtime API GUI

OpenAI の Realtime API を使用したリアルタイム音声生成 GUI アプリケーション

## 概要

このアプリケーションは、OpenAI の Realtime API を使用して、リアルタイムでテキストから音声を生成する Python ベースの GUI アプリケーションです。複数の演者設定をサポートし、PyQt6 と Tkinter 両方のインターフェースを提供します。

## 主な機能

- 🎤 リアルタイム音声生成（OpenAI Realtime API 使用）
- 👥 複数演者対応（設定ファイルベース）
- 🖥️ 2つの UI 選択肢（PyQt6 / Tkinter）
- 🎵 音声ファイルの結合・編集機能
- 📁 Premiere Pro XML 出力対応

## 必要要件

- Python 3.8 以上
- OpenAI API キー
- uv（依存関係管理）

## インストール

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd realtime_api_gui
```

### 2. 依存関係のインストール
```bash
# uv を使用して依存関係をインストール
uv sync

# 仮想環境をアクティベート
source .venv/bin/activate
```

### 3. 環境設定
`.env` ファイルを作成し、OpenAI API キーを設定：
```env
OPENAI_API_KEY=your_api_key_here
```

## 基本的な使用方法

### GUI 起動

#### PyQt6 GUI（推奨）
```bash
python app.py
```

#### Tkinter GUI
```bash
python app.py --tkinter
```

### GUI 操作方法

1. **演者選択**: ドロップダウンメニューから演者を選択
2. **システムプロンプト**: 演者の設定に応じて自動入力（編集可能）
3. **演技指導**: 任意で演技の指導を入力
4. **セリフ**: 読み上げたいテキストを入力
5. **生成**: 「生成」ボタンまたは `Ctrl+Enter` で音声生成
6. **再生**: 生成された音声を再生
7. **保存**: 音声ファイルを保存
8. **設定**: 演者の設定を編集（システムプロンプト、音声タイプ、速度）

## 演者設定

演者の設定は `config/prompts.json` で管理されます。

### 設定ファイルの形式
```json
{
    "演者名": {
        "system_prompt": "システムプロンプト",
        "voice": "音声タイプ",
        "speed": 1.3
    }
}
```

### GUI での演者設定編集
1. アプリケーションの「設定」ボタンをクリック
2. 演者設定ダイアログで演者の追加・編集・削除が可能
3. システムプロンプト、音声タイプ、速度を設定
4. 「保存」ボタンで設定を保存

### 手動での演者追加
1. `config/prompts.json` を編集
2. 新しい演者のエントリを追加
3. アプリケーションを再起動

### 利用可能な音声タイプ
- `alloy`: 汎用音声
- `echo`: エコー効果
- `fable`: 物語調
- `onyx`: 深い音声
- `nova`: 新しい音声
- `shimmer`: きらめく音声
- `ballad`: バラード調
- `sage`: 賢者の音声

## 音声結合機能

複数の音声ファイルを結合し、編集用のファイルを作成できます。

### 基本的な結合
```bash
python app.py --mix --performer <演者名> --date <MMDD>
```

### 出力ファイル
- `<演者名>_<日付>_mixed.wav`: 結合された音声ファイル
- `<演者名>_<日付>_premiere.xml`: Premiere Pro 用 XML ファイル

## ファイル構成

```
realtime_api_gui/
├── app.py                    # メインアプリケーション
├── config/
│   └── prompts.json         # 演者設定ファイル
├── models/
│   └── voice_generator.py   # 音声生成エンジン
├── utils/
│   ├── ui/
│   │   ├── pyqt_window.py   # PyQt6 GUI
│   │   └── main_window.py   # Tkinter GUI
│   ├── audio/
│   │   └── mix_audio.py     # 音声結合
│   └── logger/
│       └── logger_utils.py  # ログ機能
├── temp/                    # 一時ファイル（自動作成）
└── log/                     # ログファイル（自動作成）
```

## 開発者向け

### コード品質チェック
```bash
# リンターの実行
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# コードフォーマット
uv run ruff format .
```

### 実行ファイルの作成
```bash
uv run pyinstaller app.py --name realtime-api-gui --onefile
```

## トラブルシューティング

### よくある問題

1. **OpenAI API エラー**
   - `.env` ファイルの API キーを確認
   - API キーの有効性を確認

2. **演者が表示されない**
   - `config/prompts.json` の存在を確認
   - JSON の構文エラーをチェック

3. **音声生成できない**
   - インターネット接続を確認
   - ログファイル（`log/` ディレクトリ）を確認

4. **PyQt6 エラー**
   - Tkinter 版を試す: `python app.py --tkinter`

### ログファイル
ログは `log/YYYY-MM-DD.log` に保存されます。問題が発生した場合は、このファイルを確認してください。

## ライセンス

このプロジェクトのライセンス情報については、プロジェクト管理者にお問い合わせください。

## サポート

問題や質問がある場合は、GitHub の Issue またはプロジェクト管理者にお問い合わせください。