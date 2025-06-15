from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QApplication,
    QComboBox,
    QProgressBar,
)
from PyQt6.QtCore import Qt
import json
from datetime import datetime
import os
from models.voice_generator import VoiceGenerator
from utils.logger import get_logger

# ロガーの取得
logger = get_logger()

# アプリケーションのルートディレクトリを取得
# PyInstaller で実行されている場合の対応
import sys
if getattr(sys, 'frozen', False):
    # PyInstaller で実行されている場合
    ROOT_DIR = sys._MEIPASS
else:
    # 通常の Python で実行されている場合
    ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class FocusTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabChangesFocus(True)  # Tabキーでフォーカス移動を有効化

    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            # Ctrl+Enterで複数行入力を可能に
            super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Return:
            # 通常のEnterキーは無視（送信を防ぐ）
            event.ignore()
        else:
            super().keyPressEvent(event)


class VoiceGeneratorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("アプリケーションを初期化中...")
        
        # VoiceGeneratorを初期化（APIキーエラーの場合は設定ダイアログを表示）
        self.voice_generator = None
        
        # プロンプトの初期値を設定（後でJSONから読み込まれる）
        self.prompts = {}
        self.load_prompts()
        self.init_ui()
        
        self._initialize_voice_generator()
        
        logger.info("アプリケーションの初期化が完了しました")
    
    def _initialize_voice_generator(self):
        """VoiceGeneratorを初期化（APIキーエラー時は設定ダイアログを表示）"""
        try:
            self.voice_generator = VoiceGenerator()
            # 初期の演者を設定
            if self.prompts:
                first_actor = list(self.prompts.keys())[0]
                self.voice_generator.set_actor(first_actor)
        except ValueError as e:
            if "OPENAI_API_KEY" in str(e):
                logger.warning("APIキーが設定されていないため、設定ダイアログを表示します")
                self.status_label.setText("APIキーが設定されていません。設定画面を開いてください。")
                
                # 設定ダイアログを自動で開く
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self._show_api_key_setup)
            else:
                raise
    
    def _show_api_key_setup(self):
        """APIキー設定ダイアログを表示"""
        reply = QMessageBox.question(
            self,
            "APIキー設定",
            "OpenAI APIキーが設定されていません。\n設定画面を開きますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.open_settings()

    def load_prompts(self):
        try:
            config_file = os.path.join(ROOT_DIR, "config", "prompts.json")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    self.prompts = json.load(f)
                    logger.info("プロンプト設定を読み込みました")
            else:
                logger.error("prompts.jsonファイルが見つかりません")
                raise FileNotFoundError("config/prompts.jsonファイルが必要です。")
        except Exception as e:
            logger.error(f"プロンプト設定の読み込みに失敗しました: {str(e)}")
            raise RuntimeError(f"prompts.jsonの読み込みに失敗しました: {str(e)}")

        # ドロップダウンを更新（まだ存在する場合）
        if hasattr(self, "actor_combo"):
            current_selection = self.actor_combo.currentText()
            self.actor_combo.clear()
            self.actor_combo.addItems(list(self.prompts.keys()))
            # 以前の選択を復元するか、最初のアイテムを選択
            if current_selection in self.prompts:
                self.actor_combo.setCurrentText(current_selection)
            elif self.prompts:
                self.actor_combo.setCurrentIndex(0)
                first_actor_config = list(self.prompts.values())[0]
                if "system_prompt" in first_actor_config:
                    self.system_prompt.setText(first_actor_config["system_prompt"])

    def init_ui(self):
        self.setWindowTitle("Voice Generator")
        self.setGeometry(100, 100, 800, 600)

        # メインウィジェットとレイアウト
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # 演者選択（ドロップダウン）
        actor_layout = QHBoxLayout()
        actor_label = QLabel("演者:")
        actor_layout.addWidget(actor_label)

        self.actor_combo = QComboBox()
        # プロンプトが存在する場合のみアイテムを追加
        if self.prompts:
            self.actor_combo.addItems(list(self.prompts.keys()))
            self.actor_combo.setCurrentIndex(0)
        # 接続は最後に設定
        self.actor_combo.currentTextChanged.connect(self.on_actor_changed)
        actor_layout.addWidget(self.actor_combo)
        actor_layout.addStretch()  # 残りのスペースを埋める

        layout.addLayout(actor_layout)

        # システムプロンプト
        layout.addWidget(QLabel("システム:"))
        self.system_prompt = FocusTextEdit()
        self.system_prompt.setPlaceholderText("システムプロンプトを入力してください")
        self.system_prompt.setMaximumHeight(100)
        layout.addWidget(self.system_prompt)

        # 演技指導
        layout.addWidget(QLabel("演技指導: (任意)"))
        self.acting_prompt = FocusTextEdit()
        self.acting_prompt.setPlaceholderText("演技指導を入力してください（空欄可）")
        self.acting_prompt.setMaximumHeight(100)
        layout.addWidget(self.acting_prompt)

        # セリフ
        layout.addWidget(QLabel("セリフ:"))
        self.text_input = FocusTextEdit()
        self.text_input.setPlaceholderText("セリフを入力してください")
        layout.addWidget(self.text_input)

        # ボタン
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("生成")
        self.play_btn = QPushButton("再生")
        self.save_btn = QPushButton("保存")
        self.mix_btn = QPushButton("結合")
        self.settings_btn = QPushButton("設定")

        self.generate_btn.clicked.connect(self.generate_voice)
        self.play_btn.clicked.connect(self.play_voice)
        self.save_btn.clicked.connect(self.save_voice)
        self.mix_btn.clicked.connect(self.mix_audio)
        self.settings_btn.clicked.connect(self.open_settings)

        # ショートカットキーの設定
        self.generate_btn.setShortcut("Ctrl+Return")  # Ctrl+Enterで生成

        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.play_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.mix_btn)
        button_layout.addStretch()  # 右寄せのためのスペーサー
        button_layout.addWidget(self.settings_btn)
        layout.addLayout(button_layout)

        # 最初の演者のプロンプトを設定
        if self.prompts:
            first_actor = list(self.prompts.keys())[0]
            self.system_prompt.setText(self.prompts[first_actor]["system_prompt"])

        # プログレスバーとステータス表示
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)  # 初期は非表示
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("QLabel { color: #333; font-weight: bold; }")
        progress_layout.addWidget(self.status_label)
        
        layout.addLayout(progress_layout)

    def get_current_actor(self):
        return self.actor_combo.currentText() if hasattr(self, "actor_combo") else None

    def on_actor_changed(self, actor):
        if actor and hasattr(self, "prompts") and actor in self.prompts:
            # システムプロンプトを更新
            self.system_prompt.setText(self.prompts[actor]["system_prompt"])
            # 音声設定を更新
            if hasattr(self, 'voice_generator') and self.voice_generator:
                self.voice_generator.set_actor(actor)
                logger.info(f"演者を切り替え: {actor}")

    def generate_voice(self):
        try:
            # プログレスバーとステータス表示を開始
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不確定なプログレス
            self.status_label.setText("🎤 音声生成中...")
            self.status_label.setStyleSheet("QLabel { color: #2196F3; font-weight: bold; }")
            self.generate_btn.setEnabled(False)
            self.play_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            QApplication.processEvents()  # UIを更新

            # VoiceGeneratorが初期化されているかチェック
            if not self.voice_generator:
                msg = "⚠️ APIキーが設定されていません。設定画面でAPIキーを設定してください。"
                logger.warning(msg)
                self.status_label.setText(msg)
                self.status_label.setStyleSheet("QLabel { color: #FF9800; font-weight: bold; }")
                self._show_api_key_setup()
                self._reset_ui_state()
                return
            
            text = self.text_input.toPlainText()
            if not text.strip():
                msg = "⚠️ セリフが入力されていません"
                logger.warning(msg)
                self.status_label.setText(msg)
                self.status_label.setStyleSheet("QLabel { color: #FF9800; font-weight: bold; }")
                self._reset_ui_state()
                return

            # プログレスコールバック関数
            def update_progress(message):
                self.status_label.setText(message)
                QApplication.processEvents()

            self.voice_generator.generate_voice(
                self.system_prompt.toPlainText(),
                self.acting_prompt.toPlainText(),
                text,
                progress_callback=update_progress
            )
            
            # 生成完了
            self.status_label.setText("✅ 音声生成完了")
            self.status_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
            self.play_voice()
        except Exception as e:
            error_msg = f"❌ 音声生成エラー: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("QLabel { color: #F44336; font-weight: bold; }")
        finally:
            self._reset_ui_state()

    def _reset_ui_state(self):
        """UIの状態をリセット"""
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def play_voice(self):
        try:
            if not self.voice_generator:
                self.status_label.setText("APIキーが設定されていません")
                return
            self.voice_generator.play_audio()
        except Exception as e:
            error_msg = f"音声再生エラー: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_label.setText(error_msg)

    def save_voice(self):
        try:
            if not self.voice_generator:
                self.status_label.setText("APIキーが設定されていません")
                return
            actor = self.get_current_actor()
            if actor:
                saved_path = self.voice_generator.save_voice(actor)
                if saved_path:
                    msg = f"保存完了: {saved_path}"
                    logger.info(msg)
                    self.status_label.setText(msg)
                else:
                    msg = "保存するファイルがありません"
                    logger.warning(msg)
                    self.status_label.setText(msg)
        except Exception as e:
            error_msg = f"保存エラー: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_label.setText(error_msg)

    def mix_audio(self):
        """音声ファイルを結合して無音を除去する"""
        try:
            # 現在選択されている演者を取得
            actor = self.get_current_actor()
            if not actor:
                self.status_label.setText("演者が選択されていません")
                return

            # 現在の日付を取得
            current_date = datetime.now().strftime("%m%d")

            # 確認ダイアログ
            result = QMessageBox.question(
                self,
                "確認",
                f"{actor}の今日({current_date})の音声ファイルを結合しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if result == QMessageBox.StandardButton.No:
                return

            self.status_label.setText(f"{actor}の音声を結合中...")
            QApplication.processEvents()

            # 音声結合処理
            try:
                from utils.audio.mix_audio import process_audio

                # すべての処理を一度に実行（音声結合と無音除去）
                output_file = process_audio(actor, current_date)

                if output_file:
                    self.status_label.setText(
                        f"音声結合完了: {os.path.basename(output_file)}"
                    )

                    # 結果を表示する確認ダイアログ
                    QMessageBox.information(
                        self,
                        "処理完了",
                        f"音声結合が完了しました。\nファイル: {output_file}",
                        QMessageBox.StandardButton.Ok,
                    )
                else:
                    self.status_label.setText("音声結合に失敗しました")
                    QMessageBox.warning(
                        self,
                        "エラー",
                        "音声結合処理に失敗しました。ログを確認してください。",
                        QMessageBox.StandardButton.Ok,
                    )

            except Exception as e:
                import traceback

                logger.error(f"音声結合エラー: {str(e)}\n{traceback.format_exc()}")
                self.status_label.setText("音声結合エラー")
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"音声結合中にエラーが発生しました:\n{str(e)}",
                    QMessageBox.StandardButton.Ok,
                )

        except Exception as e:
            logger.error(f"音声結合エラー: {str(e)}")
            self.status_label.setText("エラーが発生しました")
            QMessageBox.critical(
                self,
                "エラー",
                f"エラーが発生しました:\n{str(e)}",
                QMessageBox.StandardButton.Ok,
            )
    
    def open_settings(self):
        """設定ダイアログを開く"""
        try:
            from .performer_settings_dialog import PerformerSettingsDialog
            
            dialog = PerformerSettingsDialog(self)
            dialog.settings_changed.connect(self.on_settings_changed)
            dialog.exec()
            
        except Exception as e:
            error_msg = f"設定画面の表示エラー: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_label.setText(error_msg)
    
    def on_settings_changed(self):
        """設定が変更された時の処理"""
        try:
            # 現在選択中の演者を保存
            current_actor = self.get_current_actor()
            
            # プロンプト設定を再読み込み
            self.load_prompts()
            
            # ドロップダウンを更新
            if hasattr(self, "actor_combo"):
                self.actor_combo.clear()
                self.actor_combo.addItems(list(self.prompts.keys()))
                
                # 以前選択していた演者を復元（存在する場合）
                if current_actor and current_actor in self.prompts:
                    self.actor_combo.setCurrentText(current_actor)
                elif self.prompts:
                    self.actor_combo.setCurrentIndex(0)
                    first_actor_config = list(self.prompts.values())[0]
                    if "system_prompt" in first_actor_config:
                        self.system_prompt.setText(first_actor_config["system_prompt"])
            
            # ボイスジェネレータの設定も更新
            if hasattr(self.voice_generator, 'load_performer_configs'):
                self.voice_generator.performer_configs = self.voice_generator.load_performer_configs()
            
            # VoiceGeneratorを再初期化（APIキー設定が更新された可能性があるため）
            try:
                self._initialize_voice_generator()
                logger.info("VoiceGeneratorが再初期化されました")
            except Exception as e:
                logger.error(f"VoiceGeneratorの再初期化に失敗: {e}")
            
            logger.info("設定が更新されました")
            self.status_label.setText("設定が更新されました")
            
        except Exception as e:
            error_msg = f"設定更新エラー: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.status_label.setText(error_msg)
