#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import glob
from datetime import datetime
import soundfile as sf
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom
from utils.logger import get_logger

# ロガーの取得
logger = get_logger()

# アプリケーションのルートディレクトリを取得
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def generate_premiere_xml(input_file, output_xml):
    """Premiere Pro用のXMLファイルを生成する関数

    Args:
        input_file (str): 参照する音声ファイルのパス
        output_xml (str): 出力するXMLファイルのパス

    Returns:
        str: 生成されたXMLファイルのパス
    """
    try:
        logger.info(f"Premiere Pro用XMLファイルを生成します: {output_xml}")

        # XML構造の作成
        root = ET.Element("xmeml", version="4")

        # プロジェクト情報
        project = ET.SubElement(root, "project")
        name = ET.SubElement(project, "name")
        name.text = os.path.basename(os.path.splitext(input_file)[0]) + "_cut"

        # シーケンス情報
        sequence = ET.SubElement(project, "sequence")
        seq_name = ET.SubElement(sequence, "name")
        seq_name.text = os.path.basename(os.path.splitext(input_file)[0]) + "_cut"

        # メディア情報
        media = ET.SubElement(sequence, "media")

        # オーディオトラック
        audio = ET.SubElement(media, "audio")
        track = ET.SubElement(audio, "track")

        # クリップ情報
        clip = ET.SubElement(track, "clipitem")
        clip_name = ET.SubElement(clip, "name")
        clip_name.text = os.path.basename(input_file)

        # ファイル参照
        file = ET.SubElement(clip, "file")
        file_path = ET.SubElement(file, "filepath")
        file_path.text = os.path.abspath(input_file)

        # XMLをきれいに整形
        rough_string = ET.tostring(root, "utf-8")
        reparsed = minidom.parseString(rough_string)
        xml_str = reparsed.toprettyxml(indent="  ")

        # XMLファイルに保存
        with open(output_xml, "w", encoding="utf-8") as f:
            f.write(xml_str)

        logger.info(f"XMLファイルを生成しました: {output_xml}")
        return output_xml

    except Exception as e:
        logger.error(f"XMLファイル生成エラー: {str(e)}", exc_info=True)
        return None


def process_audio(performer, date=None):
    """音声ファイルを処理する関数

    Args:
        performer (str): 演者名（フォルダ名）
        date (str, optional): 日付（MMDD形式、例: 0330）。デフォルトは現在の日付。

    Returns:
        str: 結合された音声ファイルのパス。失敗した場合はNone。
    """
    try:
        logger.info(f"音声結合処理開始: 演者={performer}, 日付={date}")

        # 日付が指定されていない場合は今日の日付を使用
        if not date:
            date = datetime.now().strftime("%m%d")

        # 出力ディレクトリの作成（outputフォルダ内に演者フォルダを作成）
        output_base_dir = os.path.join(ROOT_DIR, "output")
        if not os.path.exists(output_base_dir):
            os.makedirs(output_base_dir, exist_ok=True)
            logger.info(f"出力ベースディレクトリを作成しました: {output_base_dir}")

        # 演者ディレクトリの作成
        performer_output_dir = os.path.join(output_base_dir, performer)
        if not os.path.exists(performer_output_dir):
            os.makedirs(performer_output_dir, exist_ok=True)
            logger.info(f"演者出力ディレクトリを作成しました: {performer_output_dir}")

        # 演者の元データディレクトリ
        performer_dir = os.path.join(ROOT_DIR, performer)
        if not os.path.exists(performer_dir):
            logger.error(f"演者ディレクトリが見つかりません: {performer_dir}")
            return None

        # 指定した日付のファイルを検索
        pattern = os.path.join(performer_dir, f"{performer}_{date}_*.wav")
        files = sorted(glob.glob(pattern))

        if not files:
            logger.error(f"結合対象のファイルが見つかりません: {pattern}")
            return None

        logger.info(f"対象ファイル数: {len(files)}")

        # 結合用のディレクトリを作成
        output_dir = os.path.join(performer_output_dir, f"{date}-mixed")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # 結合したファイルの出力パス
        output_filename = f"{performer}_{date}-mixed.wav"
        output_path = os.path.join(output_dir, output_filename)

        # すべてのファイルを結合
        combined = None
        sample_rate = None

        for i, file in enumerate(files):
            # 音声ファイルを読み込む
            audio_data, sr = sf.read(file)

            # 最初のファイルの場合
            if combined is None:
                combined = audio_data
                sample_rate = sr
                logger.info(
                    f"ファイル読み込み({i + 1}/{len(files)}): {os.path.basename(file)}"
                )
                continue

            # 無音を生成（形状を合わせる）
            silence_duration = 0.5  # 0.5秒の無音
            silence_samples = int(silence_duration * sample_rate)

            # 音声データの形状を取得
            if len(audio_data.shape) == 1:  # モノラル
                silence = np.zeros(silence_samples)
            else:  # ステレオまたはマルチチャンネル
                silence = np.zeros((silence_samples, audio_data.shape[1]))

            # 無音と音声を結合
            combined = np.concatenate([combined, silence, audio_data])
            logger.info(f"ファイル結合({i + 1}/{len(files)}): {os.path.basename(file)}")

        # 結合したファイルを保存
        sf.write(output_path, combined, sample_rate)
        logger.info(f"結合ファイルを保存しました: {output_path}")

        # XMLファイルを生成
        xml_output_path = os.path.splitext(output_path)[0] + "_cut.xml"
        xml_path = generate_premiere_xml(output_path, xml_output_path)

        if xml_path and os.path.exists(xml_path):
            logger.info(f"XMLファイルを生成しました: {xml_path}")
        else:
            logger.warning("XMLファイルの生成に失敗しました")

        return output_path

    except Exception as e:
        logger.error(f"音声処理中にエラーが発生しました: {str(e)}", exc_info=True)
        return None


def main():
    """コマンドラインから実行するためのメイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="音声ファイルを結合して処理します")
    parser.add_argument("performer", help="演者名（フォルダ名）")
    parser.add_argument("--date", "-d", help="日付（MMDD形式、例: 0330）")

    args = parser.parse_args()

    # 音声処理を実行
    output_file = process_audio(args.performer, args.date)

    if output_file:
        print(f"処理が完了しました: {output_file}")
        sys.exit(0)
    else:
        print("処理に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
