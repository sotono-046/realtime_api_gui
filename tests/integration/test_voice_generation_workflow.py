#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音声生成ワークフローの統合テスト
"""

import pytest
import os
import json
from unittest.mock import Mock, patch

from models.voice_generator import VoiceGenerator


class TestVoiceGenerationWorkflow:
    """音声生成ワークフローの統合テスト"""

    @pytest.fixture
    def integration_config(self, temp_dir):
        """統合テスト用設定"""
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        
        config_data = {
            "統合テスト演者1": {
                "system_prompt": "統合テスト用のシステムプロンプト1",
                "voice": "ballad",
                "speed": 1.0
            },
            "統合テスト演者2": {
                "system_prompt": "統合テスト用のシステムプロンプト2",
                "voice": "sage", 
                "speed": 1.2
            }
        }
        
        config_file = config_dir / "prompts.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        return config_file

    @pytest.fixture
    def mock_websocket_workflow(self):
        """WebSocketワークフロー用のモック"""
        mock_ws = Mock()
        
        # WebSocket接続成功のシミュレーション
        def run_forever_side_effect():
            # on_openコールバックを実行
            if hasattr(mock_ws, '_on_open_callback'):
                mock_ws._on_open_callback(mock_ws)
            
            # 音声データ受信をシミュレーション
            if hasattr(mock_ws, '_on_message_callback'):
                # 音声データのチャンクを送信
                delta_message = json.dumps({
                    "type": "response.audio.delta",
                    "delta": "dGVzdCBhdWRpbyBkYXRh"  # "test audio data" in base64
                })
                mock_ws._on_message_callback(mock_ws, delta_message)
                
                # 音声完了を送信
                done_message = json.dumps({"type": "response.audio.done"})
                mock_ws._on_message_callback(mock_ws, done_message)
                
                # レスポンス完了を送信
                response_done = json.dumps({"type": "response.done"})
                mock_ws._on_message_callback(mock_ws, response_done)
        
        mock_ws.run_forever.side_effect = run_forever_side_effect
        
        return mock_ws

    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_voice_generation_workflow(self, mock_env_vars, integration_config, temp_dir, mock_websocket_workflow):
        """完全な音声生成ワークフローのテスト"""
        with patch("models.voice_generator.ROOT_DIR", str(integration_config.parent.parent)), \
             patch("models.voice_generator.WebSocketApp", return_value=mock_websocket_workflow), \
             patch("models.voice_generator.wave.open") as mock_wave_open:
            
            # WAVファイル書き込みのモック
            mock_wav_file = Mock()
            mock_wave_open.return_value.__enter__.return_value = mock_wav_file
            
            # VoiceGeneratorを初期化
            vg = VoiceGenerator()
            
            # WebSocketコールバックを設定
            mock_websocket_workflow._on_open_callback = vg._on_open
            mock_websocket_workflow._on_message_callback = vg._on_message
            
            # 演者を設定
            vg.set_actor("統合テスト演者1")
            assert vg.current_actor == "統合テスト演者1"
            
            # 音声生成を実行
            system_prompt = "統合テスト用のシステムプロンプト"
            acting_prompt = "自然に読んでください"
            text = "これは統合テストです"
            
            # 一時ファイルの存在をモック
            with patch("models.voice_generator.os.path.exists", return_value=True):
                result = vg.generate_voice(system_prompt, acting_prompt, text)
            
            # 結果を確認
            assert result is not None
            assert result == vg.temp_file
            
            # WebSocketが正しく呼ばれたことを確認
            mock_websocket_workflow.run_forever.assert_called_once()
            
            # WAVファイルが作成されたことを確認
            mock_wav_file.setnchannels.assert_called_with(1)
            mock_wav_file.setsampwidth.assert_called_with(2) 
            mock_wav_file.setframerate.assert_called_with(24000)

    @pytest.mark.integration
    def test_performer_config_integration(self, mock_env_vars, integration_config, temp_dir):
        """演者設定の統合テスト"""
        with patch("models.voice_generator.ROOT_DIR", str(integration_config.parent.parent)):
            vg = VoiceGenerator()
            
            # 設定が正しく読み込まれることを確認
            assert "統合テスト演者1" in vg.performer_configs
            assert "統合テスト演者2" in vg.performer_configs
            
            # 各演者の設定を確認
            config1 = vg.performer_configs["統合テスト演者1"]
            assert config1["voice"] == "ballad"
            assert config1["speed"] == 1.0
            
            config2 = vg.performer_configs["統合テスト演者2"]
            assert config2["voice"] == "sage"
            assert config2["speed"] == 1.2

    @pytest.mark.integration
    def test_websocket_message_flow(self, mock_env_vars, integration_config, temp_dir):
        """WebSocketメッセージフローの統合テスト"""
        with patch("models.voice_generator.ROOT_DIR", str(integration_config.parent.parent)):
            vg = VoiceGenerator()
            vg.set_actor("統合テスト演者1")
            
            # 各種メッセージの処理をテスト
            mock_ws = Mock()
            
            # 音声データ受信のテスト
            audio_message = json.dumps({
                "type": "response.audio.delta",
                "delta": "dGVzdCBhdWRpbyBkYXRh"  # base64エンコードされたテストデータ
            })
            
            vg._on_message(mock_ws, audio_message)
            
            # 音声データが蓄積されることを確認
            assert len(vg.audio_chunks) > 0
            assert b"test audio data" in vg.audio_chunks

    @pytest.mark.integration
    @patch("models.voice_generator.sf.read")
    @patch("models.voice_generator.sd.play")
    @patch("models.voice_generator.sd.wait")
    def test_audio_playback_integration(self, mock_wait, mock_play, mock_read, mock_env_vars, integration_config, temp_dir):
        """音声再生の統合テスト"""
        import numpy as np
        
        with patch("models.voice_generator.ROOT_DIR", str(integration_config.parent.parent)):
            vg = VoiceGenerator()
            
            # テスト用音声データ
            test_audio_data = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
            test_sample_rate = 44100
            mock_read.return_value = (test_audio_data, test_sample_rate)
            
            # 一時ファイルを設定
            test_file = temp_dir / "test_audio.wav"
            test_file.write_bytes(b"test audio content")
            vg.temp_file = str(test_file)
            
            # 音声再生を実行
            vg.play_audio()
            
            # 正しい引数で再生されることを確認
            mock_read.assert_called_once_with(str(test_file))
            mock_play.assert_called_once_with(test_audio_data, test_sample_rate)
            mock_wait.assert_called_once()

    @pytest.mark.integration
    def test_file_save_integration(self, mock_env_vars, integration_config, temp_dir):
        """ファイル保存の統合テスト"""
        with patch("models.voice_generator.ROOT_DIR", str(integration_config.parent.parent)):
            vg = VoiceGenerator()
            
            # テスト用一時ファイルを作成
            temp_audio_file = temp_dir / "temp_audio.wav"
            test_audio_content = b"test audio file content"
            temp_audio_file.write_bytes(test_audio_content)
            vg.temp_file = str(temp_audio_file)
            
            # 演者を設定
            actor_name = "統合テスト演者1"
            vg.set_actor(actor_name)
            
            # 演者ディレクトリを作成
            actor_dir = temp_dir / actor_name
            actor_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存処理を実行
            with patch("models.voice_generator.ROOT_DIR", str(temp_dir)):
                saved_path = vg.save_voice(actor_name)
                
                # 保存パスが正しいことを確認
                assert saved_path is not None
                assert actor_name in saved_path
                assert saved_path.endswith(".wav")
                
                # 保存されたファイルが存在することを確認
                assert os.path.exists(saved_path)

    @pytest.mark.integration
    def test_error_handling_workflow(self, mock_env_vars, integration_config, temp_dir):
        """エラーハンドリングワークフローのテスト"""
        with patch("models.voice_generator.ROOT_DIR", str(integration_config.parent.parent)):
            vg = VoiceGenerator()
            
            # 演者未設定でのエラーテスト
            with pytest.raises(ValueError, match="演者が設定されていません"):
                vg.generate_voice("system", "acting", "text")
            
            # WebSocketエラーのテスト
            mock_ws = Mock()
            vg.ws = mock_ws
            
            vg._on_error(mock_ws, "テストエラー")
            
            # エラー時に接続が閉じられることを確認
            mock_ws.close.assert_called_once()

    @pytest.mark.integration
    def test_fallback_voice_settings_workflow(self, mock_env_vars, temp_dir):
        """フォールバック音声設定のワークフローテスト"""
        # 空の設定ファイルを作成
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        config_file = config_dir / "prompts.json"
        with open(config_file, "w") as f:
            json.dump({}, f)
        
        with patch("models.voice_generator.ROOT_DIR", str(temp_dir)):
            vg = VoiceGenerator()
            
            # 存在しない演者を設定
            vg.set_actor("存在しない演者")
            
            # フォールバック設定が使用されることを確認
            mock_ws = Mock()
            vg.current_system_prompt = "test"
            vg.current_text = "test"
            
            vg._on_open(mock_ws)
            
            # セッション設定が送信されることを確認
            assert mock_ws.send.call_count >= 2  # session.update + message

    @pytest.mark.integration
    @patch("models.voice_generator.WebSocketApp")
    def test_websocket_connection_workflow(self, mock_websocket_class, mock_env_vars, integration_config, temp_dir):
        """WebSocket接続ワークフローのテスト"""
        mock_ws = Mock()
        mock_websocket_class.return_value = mock_ws
        
        with patch("models.voice_generator.ROOT_DIR", str(integration_config.parent.parent)), \
             patch("models.voice_generator.os.path.exists", return_value=True):
            
            vg = VoiceGenerator()
            vg.set_actor("統合テスト演者1")
            
            # 音声生成を実行
            result = vg.generate_voice("system", "acting", "text")
            
            # WebSocketAppが正しい引数で作成されることを確認
            mock_websocket_class.assert_called_once()
            call_args = mock_websocket_class.call_args
            
            # URL、ヘッダー、コールバック関数が設定されることを確認
            assert vg.ws_url in call_args[0]
            assert "header" in call_args[1]
            assert "on_message" in call_args[1]
            assert "on_error" in call_args[1]
            assert "on_close" in call_args[1]
            assert "on_open" in call_args[1]

    @pytest.mark.integration
    def test_temp_file_management_workflow(self, mock_env_vars, integration_config, temp_dir):
        """一時ファイル管理ワークフローのテスト"""
        with patch("models.voice_generator.ROOT_DIR", str(integration_config.parent.parent)):
            vg = VoiceGenerator()
            
            # 初期状態で一時ファイルが設定されることを確認
            initial_temp_file = vg.temp_file
            assert initial_temp_file is not None
            assert initial_temp_file.endswith(".wav")
            
            # 一時ファイルの再作成
            vg._create_temp_file()
            
            # 新しい一時ファイルが作成されることを確認
            new_temp_file = vg.temp_file
            assert new_temp_file is not None
            assert new_temp_file != initial_temp_file