import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QTextEdit, QLineEdit, QComboBox, QDoubleSpinBox,
    QMessageBox, QSplitter, QWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.logger import get_logger

logger = get_logger()

class PerformerSettingsDialog(QDialog):
    # 設定変更を通知するシグナル
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("演者設定")
        self.setGeometry(200, 200, 800, 600)
        self.setModal(True)
        
        # 設定ファイルのパス
        self.config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config', 'prompts.json'
        )
        
        # 演者設定データ
        self.performers = {}
        self.current_performer = None
        
        self.init_ui()
        self.load_performers()
        
    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout()
        
        # メインスプリッター
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側：演者リスト
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # 演者リストラベル
        left_layout.addWidget(QLabel("演者一覧:"))
        
        # 演者リスト
        self.performer_list = QListWidget()
        self.performer_list.currentItemChanged.connect(self.on_performer_selected)
        left_layout.addWidget(self.performer_list)
        
        # 演者追加・削除ボタン
        list_button_layout = QHBoxLayout()
        self.add_btn = QPushButton("追加")
        self.delete_btn = QPushButton("削除")
        self.add_btn.clicked.connect(self.add_performer)
        self.delete_btn.clicked.connect(self.delete_performer)
        list_button_layout.addWidget(self.add_btn)
        list_button_layout.addWidget(self.delete_btn)
        left_layout.addLayout(list_button_layout)
        
        left_widget.setLayout(left_layout)
        main_splitter.addWidget(left_widget)
        
        # 右側：演者詳細設定
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # 演者名
        right_layout.addWidget(QLabel("演者名:"))
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_setting_changed)
        right_layout.addWidget(self.name_edit)
        
        # システムプロンプト
        right_layout.addWidget(QLabel("システムプロンプト:"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.textChanged.connect(self.on_setting_changed)
        self.prompt_edit.setMaximumHeight(200)
        right_layout.addWidget(self.prompt_edit)
        
        # 音声設定
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("音声タイプ:"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "alloy", "echo", "fable", "onyx", "nova", "shimmer", "ballad", "sage"
        ])
        self.voice_combo.currentTextChanged.connect(self.on_setting_changed)
        voice_layout.addWidget(self.voice_combo)
        
        voice_layout.addWidget(QLabel("速度:"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.5, 2.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setValue(1.0)
        self.speed_spin.valueChanged.connect(self.on_setting_changed)
        voice_layout.addWidget(self.speed_spin)
        
        right_layout.addLayout(voice_layout)
        
        # 詳細情報を伸縮可能にするためのスペーサー
        right_layout.addStretch()
        
        right_widget.setLayout(right_layout)
        main_splitter.addWidget(right_widget)
        
        # スプリッターの比率設定
        main_splitter.setSizes([300, 500])
        
        layout.addWidget(main_splitter)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.cancel_btn = QPushButton("キャンセル")
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 初期状態では詳細設定を無効化
        self.set_detail_enabled(False)
        
    def set_detail_enabled(self, enabled):
        """詳細設定の有効/無効を切り替え"""
        self.name_edit.setEnabled(enabled)
        self.prompt_edit.setEnabled(enabled)
        self.voice_combo.setEnabled(enabled)
        self.speed_spin.setEnabled(enabled)
        
    def load_performers(self):
        """演者設定を読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.performers = json.load(f)
                    logger.info("演者設定を読み込みました")
            else:
                self.performers = {}
                logger.warning("設定ファイルが見つかりません")
                
            self.update_performer_list()
            
        except Exception as e:
            logger.error(f"演者設定の読み込みに失敗: {e}")
            QMessageBox.critical(self, "エラー", f"設定ファイルの読み込みに失敗しました:\n{e}")
            
    def update_performer_list(self):
        """演者リストを更新"""
        self.performer_list.clear()
        for name in self.performers.keys():
            item = QListWidgetItem(name)
            self.performer_list.addItem(item)
            
    def on_performer_selected(self, current, previous):
        """演者が選択された時の処理"""
        if current is None:
            self.current_performer = None
            self.set_detail_enabled(False)
            return
            
        performer_name = current.text()
        self.current_performer = performer_name
        
        if performer_name in self.performers:
            performer_data = self.performers[performer_name]
            
            # 詳細設定を有効化
            self.set_detail_enabled(True)
            
            # フィールドを更新（シグナルを一時的に無効化）
            self.name_edit.blockSignals(True)
            self.prompt_edit.blockSignals(True)
            self.voice_combo.blockSignals(True)
            self.speed_spin.blockSignals(True)
            
            self.name_edit.setText(performer_name)
            self.prompt_edit.setPlainText(performer_data.get('system_prompt', ''))
            
            voice = performer_data.get('voice', 'alloy')
            index = self.voice_combo.findText(voice)
            if index >= 0:
                self.voice_combo.setCurrentIndex(index)
                
            self.speed_spin.setValue(performer_data.get('speed', 1.0))
            
            # シグナルを再有効化
            self.name_edit.blockSignals(False)
            self.prompt_edit.blockSignals(False)
            self.voice_combo.blockSignals(False)
            self.speed_spin.blockSignals(False)
            
    def on_setting_changed(self):
        """設定が変更された時の処理"""
        if self.current_performer is None:
            return
            
        # 現在の設定を更新
        old_name = self.current_performer
        new_name = self.name_edit.text().strip()
        
        if not new_name:
            return
            
        # 演者名が変更された場合
        if old_name != new_name:
            if new_name in self.performers and new_name != old_name:
                QMessageBox.warning(self, "警告", "同じ名前の演者が既に存在します。")
                self.name_edit.setText(old_name)
                return
                
            # 古い名前のデータを削除し、新しい名前で追加
            performer_data = self.performers.pop(old_name)
            self.performers[new_name] = performer_data
            self.current_performer = new_name
            
            # リストを更新
            self.update_performer_list()
            
            # 新しい名前のアイテムを選択
            for i in range(self.performer_list.count()):
                if self.performer_list.item(i).text() == new_name:
                    self.performer_list.setCurrentRow(i)
                    break
        
        # 設定を更新
        if self.current_performer in self.performers:
            self.performers[self.current_performer].update({
                'system_prompt': self.prompt_edit.toPlainText(),
                'voice': self.voice_combo.currentText(),
                'speed': self.speed_spin.value()
            })
            
    def add_performer(self):
        """新しい演者を追加"""
        name = f"新しい演者{len(self.performers) + 1}"
        counter = 1
        while name in self.performers:
            counter += 1
            name = f"新しい演者{counter}"
            
        # デフォルト設定で新しい演者を追加
        self.performers[name] = {
            'system_prompt': 'あなたは声優です。かぎ括弧で囲まれた文章を自然に読み上げてください。',
            'voice': 'alloy',
            'speed': 1.0
        }
        
        self.update_performer_list()
        
        # 新しく追加された演者を選択
        for i in range(self.performer_list.count()):
            if self.performer_list.item(i).text() == name:
                self.performer_list.setCurrentRow(i)
                break
                
    def delete_performer(self):
        """選択された演者を削除"""
        if self.current_performer is None:
            return
            
        reply = QMessageBox.question(
            self, "確認", 
            f"演者「{self.current_performer}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.performers[self.current_performer]
            self.update_performer_list()
            self.current_performer = None
            self.set_detail_enabled(False)
            
    def save_settings(self):
        """設定を保存"""
        try:
            # 設定ファイルのディレクトリが存在しない場合は作成
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                
            # JSONファイルに保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.performers, f, ensure_ascii=False, indent=4)
                
            logger.info("演者設定を保存しました")
            QMessageBox.information(self, "保存完了", "演者設定を保存しました。")
            
            # 設定変更を通知
            self.settings_changed.emit()
            self.accept()
            
        except Exception as e:
            logger.error(f"設定の保存に失敗: {e}")
            QMessageBox.critical(self, "エラー", f"設定の保存に失敗しました:\n{e}")