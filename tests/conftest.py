#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
テスト用の共通フィクスチャとセットアップ
"""

import os
import sys
import tempfile
import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def project_root_path():
    """プロジェクトルートパスを返す"""
    return Path(__file__).parent.parent

@pytest.fixture
def temp_dir():
    """テスト用一時ディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_env_vars():
    """環境変数のモック"""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
        yield

@pytest.fixture
def sample_prompts_config():
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
def mock_prompts_file(temp_dir, sample_prompts_config):
    """テスト用プロンプト設定ファイル"""
    config_dir = temp_dir / "config"
    config_dir.mkdir()
    prompts_file = config_dir / "prompts.json"
    
    with open(prompts_file, "w", encoding="utf-8") as f:
        json.dump(sample_prompts_config, f, ensure_ascii=False, indent=2)
    
    return prompts_file

@pytest.fixture
def mock_websocket():
    """WebSocketのモック"""
    mock_ws = MagicMock()
    mock_ws.run_forever = MagicMock()
    mock_ws.close = MagicMock()
    return mock_ws

@pytest.fixture
def mock_audio_data():
    """テスト用音声データ"""
    # 簡単なWAVファイルヘッダーを模擬
    return b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00"

@pytest.fixture
def mock_temp_audio_file(temp_dir, mock_audio_data):
    """テスト用音声ファイル"""
    audio_file = temp_dir / "test_audio.wav"
    with open(audio_file, "wb") as f:
        f.write(mock_audio_data)
    return audio_file

@pytest.fixture(autouse=True)
def suppress_qt_warnings():
    """Qt関連の警告を抑制"""
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*qt.*")

@pytest.fixture
def mock_logger():
    """ロガーのモック"""
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.debug = MagicMock()
    return mock_logger

@pytest.fixture
def qt_app():
    """PyQt6アプリケーションのフィクスチャ"""
    try:
        from PyQt6.QtWidgets import QApplication
        import sys
        
        # 既存のQApplicationインスタンスがあるかチェック
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        yield app
        
        # クリーンアップ
        app.processEvents()
    except ImportError:
        pytest.skip("PyQt6が利用できません")

@pytest.fixture
def mock_sounddevice():
    """sounddeviceのモック"""
    with patch("sounddevice.play") as mock_play, \
         patch("sounddevice.wait") as mock_wait:
        mock_play.return_value = None
        mock_wait.return_value = None
        yield {"play": mock_play, "wait": mock_wait}

# テストマーカーの設定
def pytest_configure(config):
    """カスタムマーカーの設定"""
    config.addinivalue_line(
        "markers", "unit: ユニットテストマーカー"
    )
    config.addinivalue_line(
        "markers", "integration: 統合テストマーカー"
    )
    config.addinivalue_line(
        "markers", "gui: GUIテストマーカー"
    )
    config.addinivalue_line(
        "markers", "slow: 実行時間が長いテストマーカー"
    )