#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ログユーティリティのユニットテスト
"""

import pytest
import logging
from utils.logger.logger_utils import get_logger


class TestLoggerUtils:
    """ログユーティリティのテスト"""

    @pytest.mark.unit
    def test_get_logger_returns_logger(self):
        """ロガー取得のテスト"""
        logger = get_logger()
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    @pytest.mark.unit
    def test_logger_has_handlers(self):
        """ロガーハンドラーのテスト"""
        logger = get_logger()
        
        # ハンドラーが設定されていることを確認
        assert len(logger.handlers) > 0

    @pytest.mark.unit
    def test_logger_level_configuration(self):
        """ログレベル設定のテスト"""
        logger = get_logger()
        
        # INFOレベル以上が有効であることを確認
        assert logger.isEnabledFor(logging.INFO)
        assert logger.isEnabledFor(logging.WARNING)
        assert logger.isEnabledFor(logging.ERROR)

    @pytest.mark.unit
    def test_logger_consistency(self):
        """ロガーの一貫性テスト"""
        logger1 = get_logger()
        logger2 = get_logger()
        
        # 同じロガーインスタンスが返されることを確認
        assert logger1 is logger2