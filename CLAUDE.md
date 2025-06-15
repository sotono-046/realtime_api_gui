# CLAUDE.md

このファイルは、Claude Code (claude.ai/code)がこのリポジトリのコードを操作する際のガイダンスを提供します。

## プロジェクト概要

これは、OpenAI の Realtime API を使用したリアルタイム音声生成のための Python ベースの GUI アプリケーションです。PyQt6 と Tkinter の両方のインターフェースをサポートし、音声処理機能を含んでいます。

## 対応言語

**日本語対応**: このプロジェクトは日本語での作業に最適化されており、Claude Code との連携において日本語でのコミュニケーションとコード説明を前提としています。

## 一般的な開発コマンド

### セットアップと依存関係

```bash
# uvを使用して依存関係をインストール
uv sync

# 仮想環境をアクティベート
source .venv/bin/activate
```

### アプリケーションの実行

```bash
# PyQt6 GUIで実行（デフォルト）
python app.py

# Tkinter GUIで実行
python app.py --tkinter

# 音声結合モードで実行
python app.py --mix --performer 神田 --date 0614

```

### コード品質

```bash
# リンターの実行
uv run ruff check .

# リンターの問題を修正
uv run ruff check --fix .

# コードのフォーマット
uv run ruff format .
```

### 実行ファイルのビルド

```bash
# PyInstallerでスタンドアロン実行ファイルをビルド
uv run pyinstaller app.py --name realtime-api-gui --onefile
```

## アーキテクチャ

### コアコンポーネント

1. **音声生成** (`models/voice_generator.py`)

   - OpenAI の Realtime API への WebSocket ベース接続
   - 複数の音声設定でのテキスト読み上げ変換を処理
   - 特定の音声設定を持つ異なる演者をサポート（動的に`config/prompts.json`から読み込み）

2. **音声処理** (`utils/audio/`)

   - `mix_audio.py`: 複数の音声ファイルを Premiere Pro XML 出力と組み合わせ
   - 音声再生とファイル管理

3. **ユーザーインターフェース** (`utils/ui/`)
   - `pyqt_window.py`: メインの PyQt6 ベースインターフェース
   - `main_window.py`: 代替の Tkinter インターフェース
   - 両方ともリアルタイム音声生成と音声再生をサポート

### 主要な設計パターン

- WebSocket 通信のためのイベント駆動アーキテクチャ
- スレッドベースの音声ストリーミングと再生
- 複数のフレームワークをサポートするモジュラー UI 設計
- `utils/logger/logger_utils.py`を通じた集中ログ管理

### 環境設定

`.env`ファイルが必要:

```env
OPENAI_API_KEY=your_api_key_here
```

### 音声ファイルの組織

生成された音声ファイルは以下に保存されます：

- `temp/`ディレクトリ（実行時に作成）
- 命名形式: `{performer}_{timestamp}.wav`
- 結合により日付プレフィックス付きの結合ファイルを作成

### 演者設定

演者の設定は`config/prompts.json`で管理されており、以下の方法で設定できます：

1. **GUI での設定**: アプリケーションの「設定」ボタンから演者設定ダイアログを開き、GUI で演者の追加・編集・削除が可能
2. **手動設定**: JSON ファイルを直接編集

UI は動的にプロンプト設定を読み込み、ドロップダウンメニューに表示します。設定変更は即座に反映されます。
