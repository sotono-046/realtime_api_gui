#!/usr/bin/env python3
"""
ビルドされた実行ファイルの動作テスト
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def test_executable_startup():
    """実行ファイルの起動テスト（GUI なので数秒で終了）"""
    print("🧪 実行ファイルの起動テストを開始...")
    
    # 実行ファイルのパス
    exe_paths = [
        "dist/realtime-api-gui",
        "dist/realtime-api-gui.app/Contents/MacOS/realtime-api-gui"
    ]
    
    for exe_path in exe_paths:
        if not os.path.exists(exe_path):
            print(f"❌ {exe_path} が見つかりません")
            continue
            
        print(f"\n📱 {exe_path} の起動テスト...")
        
        try:
            # プロセスを開始
            process = subprocess.Popen(
                [exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 3秒待って終了
            time.sleep(3)
            
            # プロセスが生きているかチェック
            if process.poll() is None:
                print("✅ プロセスが正常に起動しました")
                # プロセスを終了
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print("✅ プロセスが正常に終了しました")
                except subprocess.TimeoutExpired:
                    print("⚠️  プロセスの終了に時間がかかっています。強制終了します")
                    process.kill()
                    process.wait()
            else:
                # プロセスがすでに終了している場合
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    print("✅ プロセスが正常に終了しました")
                else:
                    print(f"❌ プロセスがエラーで終了しました (終了コード: {process.returncode})")
                    if stderr:
                        print(f"   エラー出力: {stderr[:200]}...")
                
        except Exception as e:
            print(f"❌ 実行エラー: {str(e)}")
    
    print("\n🎯 起動テスト完了")

def check_file_sizes():
    """ファイルサイズをチェック"""
    print("\n📊 ファイルサイズ確認...")
    
    files_to_check = [
        "dist/realtime-api-gui",
        "dist/realtime-api-gui.app"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                size_mb = size / (1024 * 1024)
                print(f"📁 {file_path}: {size_mb:.1f} MB")
            else:
                # ディレクトリの場合、再帰的にサイズを計算
                total_size = 0
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        total_size += os.path.getsize(os.path.join(root, file))
                size_mb = total_size / (1024 * 1024)
                print(f"📁 {file_path} (ディレクトリ): {size_mb:.1f} MB")
        else:
            print(f"❌ {file_path} が見つかりません")

def main():
    """メイン関数"""
    print("=" * 60)
    print("  PyInstaller ビルド結果テスト")
    print("=" * 60)
    
    # ファイルサイズチェック
    check_file_sizes()
    
    # 実行テスト
    test_executable_startup()
    
    print("\n" + "=" * 60)
    print("✅ テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    main()