import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from datetime import datetime
from utils.logger import get_logger

# ロガー取得
logger = get_logger()

# アプリケーションのルートディレクトリを取得
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Recorder")
        self.root.geometry("400x300")

        # Load performers from prompts.json
        self.prompts = self.load_prompts()
        self.current_performer = tk.StringVar()
        # 最初の演者をデフォルトとして設定
        if self.prompts:
            self.current_performer.set(list(self.prompts.keys())[0])
        self.is_recording = False

        # 演者選択フレーム
        performer_frame = ttk.Frame(root)
        performer_frame.pack(pady=10)

        ttk.Label(performer_frame, text="演者:").pack(side=tk.LEFT, padx=(0, 10))
        
        # ドロップダウンメニュー
        self.performer_combo = ttk.Combobox(
            performer_frame, 
            textvariable=self.current_performer,
            values=list(self.prompts.keys()),
            state="readonly",
            width=15
        )
        self.performer_combo.pack(side=tk.LEFT)
        if self.prompts:
            self.performer_combo.current(0)  # 最初のアイテムを選択

        # ボタンフレーム
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=20)

        self.record_button = ttk.Button(
            button_frame, text="録音開始", command=self.toggle_recording
        )
        self.record_button.pack(side=tk.LEFT, padx=10)

        ttk.Button(button_frame, text="音声結合", command=self.mix_audio).pack(
            side=tk.LEFT, padx=10
        )
        
        ttk.Button(button_frame, text="設定", command=self.open_settings).pack(
            side=tk.LEFT, padx=10
        )

        # ステータスラベル
        self.status_label = ttk.Label(root, text="待機中")
        self.status_label.pack(pady=20)

    def toggle_recording(self):
        if not self.is_recording:
            performer = self.current_performer.get()
            logger.info(f"録音開始: {performer}")
            self.is_recording = True
            self.record_button.config(text="録音停止")
            self.status_label.config(text=f"{performer}で録音中...")
        else:
            logger.info("録音停止")
            self.is_recording = False
            self.record_button.config(text="録音開始")
            self.status_label.config(text="録音停止")

    def mix_audio(self):
        """音声ファイルを結合するメソッド"""
        try:
            # 現在選択中の演者を取得
            performer = self.get_current_performer()
            if not performer:
                messagebox.showerror("エラー", "演者が選択されていません")
                return

            # 確認ダイアログを表示
            if not messagebox.askyesno(
                "確認", f"{performer}の音声ファイルを結合しますか？"
            ):
                return

            # 現在の日付を取得
            date = datetime.now().strftime("%m%d")

            # 処理中表示
            self.status_label.config(text=f"{performer}の音声を結合中...")
            self.update()

            # 音声結合処理を実行
            from utils.audio.mix_audio import process_audio

            # 処理を実行
            result_file = process_audio(performer, date)

            if result_file and os.path.exists(result_file):
                xml_file = os.path.splitext(result_file)[0] + "_cut.xml"
                if os.path.exists(xml_file):
                    self.status_label.config(
                        text=f"音声結合完了: {os.path.basename(result_file)}"
                    )
                    messagebox.showinfo(
                        "完了",
                        f"音声ファイルの結合と XML 生成が完了しました:\n{os.path.basename(result_file)}\n{os.path.basename(xml_file)}",
                    )
                else:
                    self.status_label.config(
                        text=f"音声結合完了: {os.path.basename(result_file)}"
                    )
                    messagebox.showinfo(
                        "完了",
                        f"音声ファイルの結合が完了しました:\n{os.path.basename(result_file)}",
                    )
            else:
                self.status_label.config(text="音声結合に失敗しました")
                messagebox.showerror("エラー", "音声ファイルの結合に失敗しました")

        except Exception as e:
            logger.error(f"音声結合エラー: {str(e)}")
            self.status_label.config(text="エラーが発生しました")
            messagebox.showerror("エラー", f"処理中にエラーが発生しました: {str(e)}")
            import traceback

            traceback.print_exc()

    def get_current_performer(self):
        """現在選択されている演者を取得する"""
        return self.current_performer.get()
    
    def load_prompts(self):
        """プロンプト設定をJSONファイルから読み込む"""
        try:
            config_file = os.path.join(ROOT_DIR, "config", "prompts.json")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info("プロンプト設定を読み込みました")
                    return data
            else:
                logger.error("prompts.jsonファイルが見つかりません")
                raise FileNotFoundError("config/prompts.jsonファイルが必要です。")
        except Exception as e:
            logger.error(f"プロンプト設定の読み込みに失敗: {e}")
            raise RuntimeError(f"prompts.jsonの読み込みに失敗しました: {e}")
    
    def open_settings(self):
        """設定ダイアログを開く"""
        try:
            from .performer_settings_tkinter import PerformerSettingsWindow
            
            # 設定ウィンドウを開く
            PerformerSettingsWindow(self.root, callback=self.on_settings_changed)
            
        except Exception as e:
            logger.error(f"設定画面の表示エラー: {e}")
            self.status_label.config(text=f"エラー: {e}")
    
    def on_settings_changed(self):
        """設定が変更された時の処理"""
        try:
            # 現在選択中の演者を保存
            current_performer = self.get_current_performer()
            
            # プロンプト設定を再読み込み
            self.prompts = self.load_prompts()
            
            # ドロップダウンを更新
            if hasattr(self, "performer_combo"):
                self.performer_combo['values'] = list(self.prompts.keys())
                
                # 以前選択していた演者を復元（存在する場合）
                if current_performer and current_performer in self.prompts:
                    self.current_performer.set(current_performer)
                elif self.prompts:
                    self.current_performer.set(list(self.prompts.keys())[0])
                    self.performer_combo.current(0)
            
            logger.info("設定が更新されました")
            self.status_label.config(text="設定が更新されました")
            
        except Exception as e:
            logger.error(f"設定更新エラー: {e}")
            self.status_label.config(text=f"設定更新エラー: {e}")
