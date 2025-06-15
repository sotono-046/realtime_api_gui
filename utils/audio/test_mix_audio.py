#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import argparse
from datetime import datetime
from utils.logger import get_logger
from utils.audio.mix_audio import process_audio

# ロガーの取得
logger = get_logger()


def setup_test_files(performer, sample_files=None, date=None):
    """テスト用の音声ファイルを準備する関数

    Args:
        performer (str): 演者名（フォルダ名）
        sample_files (list, optional): サンプルファイルのリスト
        date (str, optional): 日付（MMDD形式）

    Returns:
        list: 作成されたテストファイルのパスのリスト
    """
    # 現在の日付を取得（未指定の場合）
    if not date:
        date = datetime.now().strftime("%m%d")

    # アプリケーションのルートディレクトリを取得
    root_dir = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )

    # 演者のフォルダパスを設定
    performer_dir = os.path.join(root_dir, performer)
    if not os.path.exists(performer_dir):
        os.makedirs(performer_dir, exist_ok=True)
        logger.info(f"演者フォルダを作成: {performer_dir}")

    # サンプルファイルが指定されていない場合はデフォルトを使用
    if not sample_files:
        # テスト用ディレクトリのパス
        test_dir = os.path.join(os.path.dirname(__file__), "test_samples")
        if os.path.exists(test_dir):
            sample_files = [
                os.path.join(test_dir, f)
                for f in os.listdir(test_dir)
                if f.endswith(".wav")
            ]
        else:
            logger.error(f"テスト用サンプルディレクトリが見つかりません: {test_dir}")
            return []

    created_files = []
    current_time = datetime.now()

    # サンプルファイルをコピーして演者のフォルダに配置
    for i, sample_file in enumerate(sample_files):
        # 時間を少しずつ変えてファイル名を生成
        time_str = (current_time.replace(minute=current_time.minute + i)).strftime(
            "%H%M%S"
        )
        target_filename = f"{performer}_{date}_{time_str}.wav"
        target_path = os.path.join(performer_dir, target_filename)

        # ファイルをコピー
        shutil.copy2(sample_file, target_path)
        logger.info(f"テストファイルを作成: {target_path}")
        created_files.append(target_path)

    return created_files


def clean_test_files(performer, date=None, mixed_dir=None):
    """テスト後にファイルをクリーンアップする関数

    Args:
        performer (str): 演者名（フォルダ名）
        date (str, optional): 日付（MMDD形式）
        mixed_dir (str, optional): 作成された混合ディレクトリ
    """
    # 現在の日付を取得（未指定の場合）
    if not date:
        date = datetime.now().strftime("%m%d")

    # アプリケーションのルートディレクトリを取得
    root_dir = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )

    # 演者のフォルダパスを設定
    performer_dir = os.path.join(root_dir, performer)

    # 日付でフィルタリングしたファイルを削除
    if os.path.exists(performer_dir):
        for file in os.listdir(performer_dir):
            if file.endswith(".wav") and date in file and performer in file:
                file_path = os.path.join(performer_dir, file)
                try:
                    os.remove(file_path)
                    logger.info(f"テストファイルを削除: {file_path}")
                except Exception as e:
                    logger.error(f"ファイル削除エラー: {file_path}, {str(e)}")

    # 混合ディレクトリを削除（outputディレクトリ内の演者フォルダを確認）
    output_dir = os.path.join(root_dir, "output", performer)
    if not mixed_dir and os.path.exists(output_dir):
        mixed_dir = os.path.join(output_dir, f"{date}-mixed")

    if mixed_dir and os.path.exists(mixed_dir):
        try:
            shutil.rmtree(mixed_dir)
            logger.info(f"混合ディレクトリを削除: {mixed_dir}")
        except Exception as e:
            logger.error(f"ディレクトリ削除エラー: {mixed_dir}, {str(e)}")


def show_results(mixed_file, xml_file):
    """テスト結果を表示する関数

    Args:
        mixed_file (str): 結合ファイルのパス
        xml_file (str): XMLファイルのパス
    """
    print("\n" + "=" * 80)
    print(" テスト結果 ".center(80, "="))
    print("=" * 80)

    if os.path.exists(mixed_file):
        file_size = os.path.getsize(mixed_file) / 1024  # KBに変換
        print(f"✅ 結合ファイル: {os.path.basename(mixed_file)} ({file_size:.2f} KB)")
    else:
        print(f"❌ 結合ファイル: {os.path.basename(mixed_file)} (未生成)")

    if os.path.exists(xml_file):
        file_size = os.path.getsize(xml_file) / 1024  # KBに変換
        print(f"✅ XMLファイル: {os.path.basename(xml_file)} ({file_size:.2f} KB)")

        # XMLファイルの内容を確認（最初の数行）
        try:
            with open(xml_file, "r", encoding="utf-8") as f:
                content = f.readlines()
                print("\nXMLファイルの内容 (最初の5行):")
                print("-" * 80)
                for i, line in enumerate(content[:5]):
                    print(f"{i + 1}: {line.strip()}")
                print("-" * 80)
        except Exception as e:
            print(f"XMLファイルの読み込みエラー: {str(e)}")
    else:
        print(f"❌ XMLファイル: {os.path.basename(xml_file)} (未生成)")

    print("=" * 80 + "\n")


def test_mix_audio_button(performer, clean=True, date=None, view_results=False):
    """音声結合ボタンを押した挙動をシミュレートするテスト関数

    Args:
        performer (str): 演者名（フォルダ名）
        clean (bool, optional): テスト後にファイルをクリーンアップするかどうか
        date (str, optional): 日付（MMDD形式）
        view_results (bool, optional): テスト結果を表示するかどうか

    Returns:
        bool: テストが成功したかどうか
    """
    # 現在の日付を取得（未指定の場合）
    if not date:
        date = datetime.now().strftime("%m%d")

    try:
        logger.info(f"===== 音声結合テスト開始: 演者={performer}, 日付={date} =====")

        # テスト用のファイルを準備
        test_files = setup_test_files(performer, date=date)

        if not test_files:
            logger.error("テストファイルの準備に失敗しました")
            return False

        logger.info(f"テストファイル数: {len(test_files)}")

        # 音声結合処理を実行
        mixed_file = process_audio(performer, date)

        if not mixed_file:
            logger.error("音声結合処理に失敗しました")
            return False

        # XMLファイルのパスを取得
        xml_file = os.path.splitext(mixed_file)[0] + "_cut.xml"

        # 結果を検証
        success = os.path.exists(mixed_file) and os.path.exists(xml_file)

        if success:
            logger.info(
                f"テスト成功: 結合ファイル={mixed_file}, XMLファイル={xml_file}"
            )

            # 結果の表示（オプション）
            if view_results:
                show_results(mixed_file, xml_file)

        else:
            logger.error(f"テスト失敗: 結合ファイルまたはXMLファイルが見つかりません")
            if not os.path.exists(mixed_file):
                logger.error(f"結合ファイルが見つかりません: {mixed_file}")
            if not os.path.exists(xml_file):
                logger.error(f"XMLファイルが見つかりません: {xml_file}")

        # クリーンアップ（オプション）
        if clean and not view_results:  # 結果を表示する場合はクリーンアップしない
            mixed_dir = os.path.dirname(mixed_file)
            clean_test_files(performer, date, mixed_dir)
        elif not clean and view_results:
            print(f"\n🔍 生成されたファイルは以下のディレクトリに保存されています:")
            print(f"   {os.path.dirname(mixed_file)}\n")

        logger.info(f"===== 音声結合テスト終了: {'成功' if success else '失敗'} =====")
        return success

    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {str(e)}", exc_info=True)
        return False


def main():
    """コマンドラインから実行するためのメイン関数"""
    parser = argparse.ArgumentParser(description="音声結合処理のテストを実行します")
    parser.add_argument("performer", help="演者名（フォルダ名）")
    parser.add_argument("--date", "-d", help="日付（MMDD形式、例: 0330）")
    parser.add_argument(
        "--no-clean",
        "-n",
        action="store_true",
        help="テスト後のクリーンアップをスキップする",
    )
    parser.add_argument(
        "--view", "-v", action="store_true", help="テスト結果を表示して終了する"
    )

    args = parser.parse_args()

    try:
        # テストを実行
        success = test_mix_audio_button(
            args.performer, not args.no_clean, args.date, args.view
        )

        # 結果に応じて終了コードを設定
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
