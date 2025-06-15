#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VoiceGeneratorクラスのユニットテスト
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, mock_open

from models.voice_generator import VoiceGenerator


class TestVoiceGenerator:
    """VoiceGeneratorクラスのテスト"""

    @pytest.fixture
    def mock_api_key(self):
        """テスト用APIキー"""
        return "test-api-key-12345"

    @pytest.fixture
    def voice_generator(self, mock_env_vars, mock_prompts_file):
        """VoiceGeneratorインスタンス"""
        with patch("models.voice_generator.ROOT_DIR", str(mock_prompts_file.parent.parent)):
            return VoiceGenerator()

    @pytest.mark.unit
    def test_init_without_api_key(self):
        """APIキーなしでの初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEYが設定されていません"):
                VoiceGenerator()

    @pytest.mark.unit
    def test_init_with_api_key(self, mock_env_vars, mock_prompts_file):
        """APIキーありでの初期化テスト"""
        with patch("models.voice_generator.ROOT_DIR", str(mock_prompts_file.parent.parent)), \
             patch("models.voice_generator.VoiceGenerator._create_temp_file"):
            vg = VoiceGenerator()
            assert vg.client is not None
            assert vg.current_actor is None
            assert isinstance(vg.performer_configs, dict)

    @pytest.mark.unit
    def test_load_performer_configs_file_exists(self, voice_generator, sample_prompts_config):
        """プロンプト設定ファイルが存在する場合のテスト"""
        configs = voice_generator.performer_configs
        assert configs == sample_prompts_config
        assert "テスト演者1" in configs
        assert "テスト演者2" in configs

    @pytest.mark.unit
    def test_load_performer_configs_file_not_exists(self, mock_env_vars):
        """プロンプト設定ファイルが存在しない場合のテスト"""
        with patch("models.voice_generator.ROOT_DIR", "/nonexistent"), \
             patch("models.voice_generator.VoiceGenerator._create_temp_file"):
            vg = VoiceGenerator()
            assert vg.performer_configs == {}

    @pytest.mark.unit
    def test_set_actor(self, voice_generator):
        """演者設定のテスト"""
        actor_name = "テスト演者1"
        voice_generator.set_actor(actor_name)
        assert voice_generator.current_actor == actor_name

    @pytest.mark.unit
    def test_create_temp_file(self, voice_generator, temp_dir):
        """一時ファイル作成のテスト"""
        with patch("models.voice_generator.ROOT_DIR", str(temp_dir)):
            voice_generator._create_temp_file()
            
            assert voice_generator.temp_file is not None
            assert voice_generator.temp_file.endswith(".wav")
            
            # tempディレクトリが作成されることを確認
            temp_path = temp_dir / "temp"
            assert temp_path.exists()

    @pytest.mark.unit
    def test_fallback_voice_setting(self, voice_generator):
        """フォールバック音声設定のテスト"""
        # 存在しない演者を設定
        voice_generator.set_actor("存在しない演者")
        
        # フォールバック設定が使用されることを確認
        assert hasattr(voice_generator, 'FALLBACK_VOICE_SETTING')
        fallback = voice_generator.FALLBACK_VOICE_SETTING
        assert "voice" in fallback
        assert "speed" in fallback

    @pytest.mark.unit
    @patch("models.voice_generator.WebSocketApp")
    def test_generate_voice_no_actor(self, mock_websocket, voice_generator):
        """演者未設定時の音声生成エラーテスト"""
        with pytest.raises(ValueError, match="演者が設定されていません"):
            voice_generator.generate_voice("system", "acting", "text")

    @pytest.mark.unit
    @patch("models.voice_generator.WebSocketApp")
    @patch("models.voice_generator.os.path.exists")
    def test_generate_voice_success(self, mock_exists, mock_websocket_class, voice_generator, temp_dir):
        """音声生成成功のテスト"""
        # 設定
        voice_generator.set_actor("テスト演者1")
        mock_temp_file = temp_dir / "test.wav"
        voice_generator.temp_file = str(mock_temp_file)
        
        # モック設定
        mock_websocket = Mock()
        mock_websocket_class.return_value = mock_websocket
        mock_exists.return_value = True
        
        # テスト実行
        result = voice_generator.generate_voice("system prompt", "acting prompt", "test text")
        
        # 検証
        assert result == str(mock_temp_file)
        mock_websocket.run_forever.assert_called_once()
        assert voice_generator.current_system_prompt == "system prompt"
        assert "acting prompt" in voice_generator.current_text
        assert "test text" in voice_generator.current_text

    @pytest.mark.unit
    def test_on_message_audio_delta(self, voice_generator):
        """音声データ受信メッセージのテスト"""
        mock_ws = Mock()
        test_audio_data = b"test audio data"
        encoded_data = "dGVzdCBhdWRpbyBkYXRh"  # base64エンコードされた "test audio data"
        
        message = json.dumps({
            "type": "response.audio.delta",
            "delta": encoded_data
        })
        
        voice_generator._on_message(mock_ws, message)
        
        assert test_audio_data in voice_generator.audio_chunks

    @pytest.mark.unit
    @patch("models.voice_generator.wave.open")
    def test_on_message_audio_done(self, mock_wave_open, voice_generator, temp_dir):
        """音声データ完了メッセージのテスト"""
        mock_ws = Mock()
        voice_generator.audio_chunks = bytearray(b"test audio data")
        
        # 一時ファイルの設定
        with patch("models.voice_generator.ROOT_DIR", str(temp_dir)):
            voice_generator._create_temp_file()
        
        mock_wav_file = Mock()
        mock_wave_open.return_value.__enter__.return_value = mock_wav_file
        
        message = json.dumps({"type": "response.audio.done"})
        
        voice_generator._on_message(mock_ws, message)
        
        # WAVファイルの設定が呼ばれることを確認
        mock_wav_file.setnchannels.assert_called_with(1)
        mock_wav_file.setsampwidth.assert_called_with(2)
        mock_wav_file.setframerate.assert_called_with(24000)
        # 音声データが書き込まれることを確認（空でない）
        mock_wav_file.writeframes.assert_called_once()

    @pytest.mark.unit
    def test_on_message_response_done(self, voice_generator):
        """レスポンス完了メッセージのテスト"""
        mock_ws = Mock()
        voice_generator.ws = mock_ws
        
        message = json.dumps({"type": "response.done"})
        
        voice_generator._on_message(mock_ws, message)
        
        mock_ws.close.assert_called_once()

    @pytest.mark.unit
    def test_on_error(self, voice_generator):
        """WebSocketエラーハンドリングのテスト"""
        mock_ws = Mock()
        voice_generator.ws = mock_ws
        
        voice_generator._on_error(mock_ws, "Test error")
        
        mock_ws.close.assert_called_once()

    @pytest.mark.unit
    def test_on_open_with_known_actor(self, voice_generator):
        """既知の演者でのWebSocket接続開始テスト"""
        mock_ws = Mock()
        voice_generator.set_actor("テスト演者1")
        voice_generator.current_system_prompt = "test system prompt"
        voice_generator.current_text = "test text"
        
        voice_generator._on_open(mock_ws)
        
        # 2回の送信が行われることを確認（設定とメッセージ）
        assert mock_ws.send.call_count == 3  # session.update, conversation.item.create, response.create

    @pytest.mark.unit
    def test_on_open_with_unknown_actor(self, voice_generator):
        """未知の演者でのWebSocket接続開始テスト（フォールバック使用）"""
        mock_ws = Mock()
        voice_generator.set_actor("未知の演者")
        voice_generator.current_system_prompt = "test system prompt"
        voice_generator.current_text = "test text"
        
        voice_generator._on_open(mock_ws)
        
        # フォールバック設定が使用されることを確認
        assert mock_ws.send.call_count == 3

    @pytest.mark.unit
    @patch("models.voice_generator.os.path.exists")
    @patch("models.voice_generator.os.makedirs")
    def test_save_voice_success(self, mock_makedirs, mock_exists, voice_generator, temp_dir):
        """音声保存成功のテスト"""
        # テスト用一時ファイルを作成
        temp_file = temp_dir / "temp.wav"
        temp_file.write_bytes(b"test audio data")
        voice_generator.temp_file = str(temp_file)
        
        mock_exists.return_value = True
        
        with patch("models.voice_generator.ROOT_DIR", str(temp_dir)), \
             patch("builtins.open", mock_open(read_data=b"test audio data")) as mock_file, \
             patch("models.voice_generator.os.remove") as mock_remove:
            
            result = voice_generator.save_voice("テスト演者")
            
            assert result is not None
            assert "テスト演者" in result
            mock_remove.assert_called_once()

    @pytest.mark.unit
    def test_save_voice_no_temp_file(self, voice_generator):
        """一時ファイルなしでの音声保存テスト"""
        voice_generator.temp_file = None
        
        result = voice_generator.save_voice("テスト演者")
        
        assert result is None

    @pytest.mark.unit
    @patch("models.voice_generator.sf.read")
    @patch("models.voice_generator.sd.play")
    @patch("models.voice_generator.sd.wait")
    def test_play_audio_success(self, mock_wait, mock_play, mock_read, voice_generator, temp_dir):
        """音声再生成功のテスト"""
        # テスト用音声ファイル
        audio_file = temp_dir / "test.wav"
        audio_file.write_bytes(b"test audio data")
        
        mock_read.return_value = ([0.1, 0.2, 0.3], 44100)
        
        voice_generator.play_audio(str(audio_file))
        
        mock_read.assert_called_once_with(str(audio_file))
        mock_play.assert_called_once()
        mock_wait.assert_called_once()

    @pytest.mark.unit
    def test_play_audio_no_file(self, voice_generator):
        """ファイルなしでの音声再生テスト"""
        voice_generator.temp_file = None
        
        # エラーなく終了することを確認
        voice_generator.play_audio()

    @pytest.mark.unit
    def test_performer_configs_integration(self, voice_generator, sample_prompts_config):
        """演者設定の統合テスト"""
        # 設定が正しく読み込まれていることを確認
        assert voice_generator.performer_configs == sample_prompts_config
        
        # 各演者の設定を確認
        for actor_name, config in sample_prompts_config.items():
            voice_generator.set_actor(actor_name)
            assert voice_generator.current_actor == actor_name
            
            # 設定が存在することを確認
            assert actor_name in voice_generator.performer_configs
            actor_config = voice_generator.performer_configs[actor_name]
            assert "system_prompt" in actor_config
            assert "voice" in actor_config
            assert "speed" in actor_config