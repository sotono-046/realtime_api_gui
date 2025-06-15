#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音声生成機能のテストスクリプト
"""

import os
from models.voice_generator import VoiceGenerator
from utils.logger import get_logger

# ロガーの初期化
logger = get_logger()

def test_voice_generation():
    """音声生成のテスト"""
    try:
        print("音声生成テストを開始します...")
        
        # VoiceGeneratorを初期化
        vg = VoiceGenerator()
        print("✅ VoiceGenerator初期化成功")
        
        # 演者を設定
        vg.set_actor('神田')
        print("✅ 演者設定成功")
        
        # 設定確認
        if vg.current_actor in vg.performer_configs:
            config = vg.performer_configs[vg.current_actor]
            print(f"✅ 演者設定確認: voice={config.get('voice')}, speed={config.get('speed')}")
        
        # 短いテストテキストで音声生成
        system_prompt = "あなたは日本語を読み上げる声優です。"
        acting_prompt = "自然に読んでください。"
        test_text = "こんにちは、これは音声生成のテストです。"
        
        print("🎤 音声生成を開始...")
        print(f"   システムプロンプト: {system_prompt[:30]}...")
        print(f"   演技指導: {acting_prompt}")
        print(f"   テキスト: {test_text}")
        
        # 音声生成を実行
        result = vg.generate_voice(system_prompt, acting_prompt, test_text)
        
        if result and os.path.exists(result):
            print(f"✅ 音声生成成功: {result}")
            file_size = os.path.getsize(result)
            print(f"   ファイルサイズ: {file_size} bytes")
            return True
        else:
            print("❌ 音声ファイルが生成されませんでした")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️  ユーザーによりテストが中断されました")
        return False
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        logger.error(f"音声生成テストエラー: {str(e)}", exc_info=True)
        return False

def main():
    """メイン関数"""
    print("=" * 50)
    print("  音声生成機能テスト")
    print("=" * 50)
    
    # 環境チェック
    print("ℹ️  APIキーはGUI設定ファイルまたは環境変数から読み込まれます")
    
    # テスト実行
    success = test_voice_generation()
    
    print("=" * 50)
    if success:
        print("✅ テスト完了: 音声生成が正常に動作しています")
    else:
        print("❌ テスト失敗: 音声生成に問題があります")
    print("=" * 50)

if __name__ == "__main__":
    main()