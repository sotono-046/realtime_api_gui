#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tkinter UI コンポーネントのユニットテスト
"""

import pytest
import sys
import os
import tkinter as tk
import json
from unittest.mock import Mock, patch, MagicMock

# Tkinter GUI テストをスキップする条件
def skip_if_no_display():
    """DISPLAY環境変数がない場合はテストをスキップ"""
    try:
        test_root = tk.Tk()
        test_root.destroy()
        return False
    except tk.TclError:
        return True

skip_gui_tests = skip_if_no_display()

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from utils.ui.main_window import Application


@pytest.mark.skipif(skip_gui_tests, reason="GUI環境が利用できません")
class TestApplication:
    """Applicationクラスのテスト"""

    @pytest.fixture
    def sample_prompts(self):
        """テスト用プロンプト設定"""
        return {
            "テスト演者1": {
                "system_prompt": "テスト用システムプロンプト1",
                "voice": "ballad",
                "speed": 1.0
            },
            "テスト演者2": {
                "system_prompt": "テスト用システムプロンプト2", 
                "voice": "sage",
                "speed": 1.2
            }
        }

    @pytest.fixture
    def tk_app(self, sample_prompts, temp_dir):
        """Tkinterアプリケーションのフィクスチャ"""
        # prompts.jsonを作成
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        prompts_file = config_dir / "prompts.json"
        with open(prompts_file, "w", encoding="utf-8") as f:
            json.dump(sample_prompts, f)
        
        try:
            with patch("utils.ui.main_window.ROOT_DIR", str(temp_dir)):
                root = tk.Tk()
                app = Application(root)
                
                # テスト用にウィンドウを非表示にする
                root.withdraw()
                
                yield app
                
                # クリーンアップ
                try:
                    root.destroy()
                except tk.TclError:
                    pass
        except tk.TclError:
            pytest.skip("Tkinter GUI initialization failed - likely headless environment")

    @pytest.mark.unit
    @pytest.mark.gui
    def test_app_initialization(self, tk_app, sample_prompts):
        """アプリケーション初期化のテスト"""
        assert tk_app.prompts == sample_prompts
        assert tk_app.current_performer is not None
        assert hasattr(tk_app, 'performer_combo')
        assert hasattr(tk_app, 'record_button')

    @pytest.mark.unit
    @pytest.mark.gui
    def test_load_prompts(self, tk_app, sample_prompts):
        """プロンプト読み込みのテスト"""
        prompts = tk_app.load_prompts()
        assert prompts == sample_prompts
        assert "テスト演者1" in prompts
        assert "テスト演者2" in prompts

    @pytest.mark.unit
    @pytest.mark.gui
    def test_get_current_performer(self, tk_app):
        """現在の演者取得のテスト"""
        tk_app.current_performer.set("テスト演者1")
        current = tk_app.get_current_performer()
        assert current == "テスト演者1"

    @pytest.mark.unit
    @pytest.mark.gui
    def test_toggle_recording(self, tk_app):
        """録音トグルのテスト"""
        # 初期状態は録音停止
        assert tk_app.is_recording is False
        assert tk_app.record_button.cget("text") == "録音開始"
        
        # 録音開始
        tk_app.toggle_recording()
        assert tk_app.is_recording is True
        assert tk_app.record_button.cget("text") == "録音停止"
        
        # 録音停止
        tk_app.toggle_recording()
        assert tk_app.is_recording is False
        assert tk_app.record_button.cget("text") == "録音開始"

    @pytest.mark.unit
    @pytest.mark.gui
    def test_combobox_population(self, tk_app, sample_prompts):
        """コンボボックスのデータ設定テスト"""
        combo_values = tk_app.performer_combo['values']
        
        for actor in sample_prompts.keys():
            assert actor in combo_values

    @pytest.mark.unit
    @pytest.mark.gui
    def test_ui_components_exist(self, tk_app):
        """UI コンポーネントの存在確認"""
        assert hasattr(tk_app, 'current_performer')
        assert hasattr(tk_app, 'performer_combo')
        assert hasattr(tk_app, 'record_button')
        assert hasattr(tk_app, 'status_label')

    @pytest.mark.unit
    @pytest.mark.gui
    @patch("utils.ui.main_window.process_audio")
    def test_mix_audio_success(self, mock_process_audio, tk_app, temp_dir):
        """音声結合成功のテスト"""
        # モックの設定
        output_file = temp_dir / "test_output.wav"
        output_file.write_bytes(b"test audio data")
        mock_process_audio.return_value = str(output_file)
        
        with patch("tkinter.messagebox.askyesno", return_value=True), \
             patch("tkinter.messagebox.showinfo") as mock_info, \
             patch.object(tk_app, 'update'):
            
            tk_app.current_performer.set("テスト演者1")
            tk_app.mix_audio()
            
            # process_audioが呼ばれることを確認
            mock_process_audio.assert_called_once()
            
            # 成功メッセージが表示されることを確認
            mock_info.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.gui
    def test_mix_audio_no_performer(self, tk_app):
        """演者未選択での音声結合テスト"""
        tk_app.current_performer.set("")
        
        with patch("tkinter.messagebox.showerror") as mock_error:
            tk_app.mix_audio()
            
            # エラーメッセージが表示されることを確認
            mock_error.assert_called_once_with("エラー", "演者が選択されていません")

    @pytest.mark.unit
    @pytest.mark.gui
    def test_mix_audio_user_cancel(self, tk_app):
        """ユーザーキャンセルでの音声結合テスト"""
        tk_app.current_performer.set("テスト演者1")
        
        with patch("tkinter.messagebox.askyesno", return_value=False):
            # キャンセルした場合、処理が中断されることを確認
            tk_app.mix_audio()
            # エラーが発生しないことを確認

    @pytest.mark.unit
    @pytest.mark.gui  
    def test_on_settings_changed(self, tk_app, sample_prompts):
        """設定変更時の処理テスト"""
        current_performer = "テスト演者1"
        tk_app.current_performer.set(current_performer)
        
        with patch.object(tk_app, 'load_prompts', return_value=sample_prompts):
            tk_app.on_settings_changed()
            
            # コンボボックスが更新されることを確認
            combo_values = tk_app.performer_combo['values']
            for actor in sample_prompts.keys():
                assert actor in combo_values

    @pytest.mark.unit
    @pytest.mark.gui
    def test_error_handling_in_mix_audio(self, tk_app):
        """音声結合エラーハンドリングのテスト"""
        tk_app.current_performer.set("テスト演者1")
        
        with patch("tkinter.messagebox.askyesno", return_value=True), \
             patch("utils.ui.main_window.process_audio", side_effect=Exception("テストエラー")), \
             patch("tkinter.messagebox.showerror") as mock_error:
            
            tk_app.mix_audio()
            
            # エラーメッセージが表示されることを確認
            mock_error.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.gui
    def test_window_properties(self, tk_app):
        """ウィンドウプロパティのテスト"""
        # ウィンドウタイトルが設定されていることを確認
        assert tk_app.root.title() == "Voice Recorder"
        
        # ウィンドウが初期化されていることを確認
        geometry = tk_app.root.geometry()
        assert geometry is not None