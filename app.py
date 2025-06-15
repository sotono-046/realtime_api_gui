#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from utils.logger import get_logger

# ロガーの初期化
logger = get_logger()

# アプリケーションのルートディレクトリを取得
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


def main():
    """アプリケーションのメインエントリーポイント"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="音声生成・編集アプリケーション")
    parser.add_argument(
        "--tkinter", "-tk", action="store_true", help="TkinterベースのUIを使用する"
    )
    parser.add_argument("--mix", "-m", action="store_true", help="音声結合モード")
    parser.add_argument("--performer", "-p", help="演者名（音声結合モード時に使用）")
    parser.add_argument("--date", "-d", help="日付（MMDD形式、音声結合モード時に使用）")

    args = parser.parse_args()

    try:
        # 音声結合モードの場合
        if args.mix:
            logger.info("音声結合モードで実行します")

            if not args.performer:
                logger.error("演者名が指定されていません")
                print("演者名を指定してください（例: --performer <演者名>）")
                sys.exit(1)

            # 音声結合処理を実行
            from utils.audio.mix_audio import process_audio

            mixed_file = process_audio(args.performer, args.date)

            if mixed_file:
                logger.info(f"結合ファイル: {mixed_file}")
                print(f"結合ファイル: {mixed_file}")
            else:
                logger.error("音声結合処理に失敗しました")
                print("音声結合処理に失敗しました")
                sys.exit(1)

            logger.info("処理が完了しました")
            print("処理が完了しました")

        # UIモードの場合
        else:
            logger.info("アプリケーションを起動します")

            # Tkinter版かPyQt版かを選択
            use_tkinter = args.tkinter

            if use_tkinter:
                # Tkinterバージョンを使用
                logger.info("Tkinter UIを使用します")
                from utils.ui.main_window import Application
                import tkinter as tk

                root = tk.Tk()
                app = Application(root)
                root.mainloop()
            else:
                # PyQtバージョンを使用（デフォルト）
                logger.info("PyQt UIを使用します")
                from PyQt6.QtWidgets import QApplication
                from utils.ui.pyqt_window import VoiceGeneratorGUI

                app = QApplication(sys.argv)
                window = VoiceGeneratorGUI()
                window.show()
                sys.exit(app.exec())

    except Exception as e:
        logger.error(
            f"アプリケーション実行中にエラーが発生しました: {str(e)}", exc_info=True
        )
        print(f"エラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
