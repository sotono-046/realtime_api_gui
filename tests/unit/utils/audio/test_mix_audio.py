#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音声処理ユーティリティのユニットテスト
"""

import pytest
import numpy as np
import xml.etree.ElementTree as ET
from unittest.mock import patch

from utils.audio.mix_audio import generate_premiere_xml, process_audio


class TestMixAudio:
    """音声処理ユーティリティのテスト"""

    @pytest.mark.unit
    def test_generate_premiere_xml_success(self, temp_dir):
        """Premiere Pro XMLファイル生成成功のテスト"""
        # テスト用ファイルパス
        input_file = temp_dir / "test_audio.wav"
        output_xml = temp_dir / "test_output.xml"
        
        # テスト用音声ファイルを作成
        input_file.touch()
        
        # XMLファイルを生成
        result = generate_premiere_xml(str(input_file), str(output_xml))
        
        # 結果を確認
        assert result == str(output_xml)
        assert output_xml.exists()
        
        # XMLファイルの内容を確認
        with open(output_xml, "r", encoding="utf-8") as f:
            xml_content = f.read()
            
        # 基本的なXML構造が含まれていることを確認
        assert "xmeml" in xml_content
        assert "project" in xml_content
        assert "sequence" in xml_content
        assert "test_audio" in xml_content

    @pytest.mark.unit
    def test_generate_premiere_xml_with_parsing(self, temp_dir):
        """生成されたXMLファイルの詳細解析テスト"""
        input_file = temp_dir / "sample_audio.wav"
        output_xml = temp_dir / "sample_output.xml"
        
        input_file.touch()
        
        result = generate_premiere_xml(str(input_file), str(output_xml))
        
        # XMLをパースして構造を確認
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        assert root.tag == "xmeml"
        assert root.get("version") == "4"
        
        # プロジェクト名を確認
        project = root.find("project")
        assert project is not None
        
        name_element = project.find("name")
        assert name_element is not None
        assert "sample_audio_cut" in name_element.text

    @pytest.mark.unit
    def test_generate_premiere_xml_file_error(self, temp_dir):
        """XMLファイル生成時のファイルエラーテスト"""
        input_file = temp_dir / "nonexistent.wav"
        output_xml = temp_dir / "readonly"
        
        # 書き込み不可のディレクトリを作成
        output_xml.mkdir()
        output_xml.chmod(0o444)  # 読み取り専用
        
        try:
            xml_output = output_xml / "test.xml"
            result = generate_premiere_xml(str(input_file), str(xml_output))
            
            # エラーの場合はNoneが返されることを確認
            assert result is None
        finally:
            # パーミッションを戻す
            output_xml.chmod(0o755)

    @pytest.mark.unit
    @patch("utils.audio.mix_audio.glob.glob")
    @patch("utils.audio.mix_audio.sf.read")
    @patch("utils.audio.mix_audio.sf.write")
    @patch("utils.audio.mix_audio.generate_premiere_xml")
    def test_process_audio_success(self, mock_xml, mock_write, mock_read, mock_glob, temp_dir):
        """音声処理成功のテスト"""
        # モック設定
        performer = "テスト演者"
        date = "0615"
        
        # ファイル一覧のモック
        mock_files = [
            f"/path/{performer}/{performer}_{date}_001.wav",
            f"/path/{performer}/{performer}_{date}_002.wav"
        ]
        mock_glob.return_value = mock_files
        
        # 音声データのモック
        sample_audio_data = np.array([0.1, 0.2, 0.3])
        sample_rate = 44100
        mock_read.return_value = (sample_audio_data, sample_rate)
        
        # XMLファイル生成のモック
        mock_xml.return_value = "/path/test.xml"
        
        with patch("utils.audio.mix_audio.ROOT_DIR", str(temp_dir)), \
             patch("utils.audio.mix_audio.os.path.exists", return_value=True):
            
            result = process_audio(performer, date)
            
            # 結果を確認
            assert result is not None
            assert performer in result
            assert date in result
            
            # sf.writeが呼ばれることを確認
            mock_write.assert_called_once()
            
            # XMLファイル生成が呼ばれることを確認
            mock_xml.assert_called_once()

    @pytest.mark.unit
    @patch("utils.audio.mix_audio.glob.glob")
    def test_process_audio_no_files(self, mock_glob, temp_dir):
        """対象ファイルが見つからない場合のテスト"""
        # ファイルが見つからない場合
        mock_glob.return_value = []
        
        with patch("utils.audio.mix_audio.ROOT_DIR", str(temp_dir)), \
             patch("utils.audio.mix_audio.os.path.exists", return_value=True):
            
            result = process_audio("テスト演者", "0615")
            
            # Noneが返されることを確認
            assert result is None

    @pytest.mark.unit
    def test_process_audio_no_performer_dir(self, temp_dir):
        """演者ディレクトリが存在しない場合のテスト"""
        with patch("utils.audio.mix_audio.ROOT_DIR", str(temp_dir)):
            result = process_audio("存在しない演者", "0615")
            
            # Noneが返されることを確認
            assert result is None

    @pytest.mark.unit
    @patch("utils.audio.mix_audio.datetime")
    @patch("utils.audio.mix_audio.glob.glob")
    @patch("utils.audio.mix_audio.sf.read")
    @patch("utils.audio.mix_audio.sf.write")
    def test_process_audio_default_date(self, mock_write, mock_read, mock_glob, mock_datetime, temp_dir):
        """デフォルト日付での音声処理テスト"""
        # 現在日付のモック
        mock_datetime.now.return_value.strftime.return_value = "0615"
        
        # その他のモック設定
        performer = "テスト演者"
        mock_glob.return_value = [f"/path/{performer}/{performer}_0615_001.wav"]
        mock_read.return_value = (np.array([0.1, 0.2]), 44100)
        
        with patch("utils.audio.mix_audio.ROOT_DIR", str(temp_dir)), \
             patch("utils.audio.mix_audio.os.path.exists", return_value=True), \
             patch("utils.audio.mix_audio.generate_premiere_xml", return_value="/path/test.xml"):
            
            # 日付を指定しない場合
            result = process_audio(performer)
            
            # 現在日付が使用されることを確認
            mock_datetime.now.return_value.strftime.assert_called_with("%m%d")
            assert result is not None

    @pytest.mark.unit
    @patch("utils.audio.mix_audio.sf.read")
    @patch("utils.audio.mix_audio.sf.write")
    @patch("utils.audio.mix_audio.glob.glob")
    def test_process_audio_stereo_handling(self, mock_glob, mock_write, mock_read, temp_dir):
        """ステレオ音声ファイルの処理テスト"""
        performer = "テスト演者"
        date = "0615"
        
        # ステレオ音声データのモック（2チャンネル）
        stereo_data = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
        sample_rate = 44100
        
        mock_files = [f"/path/{performer}_{date}_001.wav", f"/path/{performer}_{date}_002.wav"]
        mock_glob.return_value = mock_files
        mock_read.return_value = (stereo_data, sample_rate)
        
        with patch("utils.audio.mix_audio.ROOT_DIR", str(temp_dir)), \
             patch("utils.audio.mix_audio.os.path.exists", return_value=True), \
             patch("utils.audio.mix_audio.generate_premiere_xml", return_value="/path/test.xml"):
            
            result = process_audio(performer, date)
            
            # 結果を確認
            assert result is not None
            
            # sf.writeが呼ばれることを確認
            mock_write.assert_called_once()
            
            # 書き込まれたデータを確認
            call_args = mock_write.call_args[0]
            written_data = call_args[1]  # 音声データ
            written_sr = call_args[2]    # サンプルレート
            
            assert written_sr == sample_rate
            assert len(written_data.shape) == 2  # ステレオデータ
            assert written_data.shape[1] == 2   # 2チャンネル

    @pytest.mark.unit
    @patch("utils.audio.mix_audio.sf.read")
    def test_process_audio_read_error(self, mock_read, temp_dir):
        """音声ファイル読み込みエラーのテスト"""
        mock_read.side_effect = Exception("読み込みエラー")
        
        with patch("utils.audio.mix_audio.ROOT_DIR", str(temp_dir)), \
             patch("utils.audio.mix_audio.os.path.exists", return_value=True), \
             patch("utils.audio.mix_audio.glob.glob", return_value=["/path/test.wav"]):
            
            result = process_audio("テスト演者", "0615")
            
            # エラーの場合はNoneが返されることを確認
            assert result is None

    @pytest.mark.unit
    @patch("utils.audio.mix_audio.sf.read")
    @patch("utils.audio.mix_audio.sf.write")
    @patch("utils.audio.mix_audio.glob.glob")
    def test_process_audio_silence_insertion(self, mock_glob, mock_write, mock_read, temp_dir):
        """音声ファイル間の無音挿入テスト"""
        performer = "テスト演者"
        date = "0615"
        
        # モノラル音声データ
        mono_data = np.array([0.1, 0.2, 0.3])
        sample_rate = 44100
        
        mock_files = [f"/path/{performer}_{date}_001.wav", f"/path/{performer}_{date}_002.wav"]
        mock_glob.return_value = mock_files
        mock_read.return_value = (mono_data, sample_rate)
        
        with patch("utils.audio.mix_audio.ROOT_DIR", str(temp_dir)), \
             patch("utils.audio.mix_audio.os.path.exists", return_value=True), \
             patch("utils.audio.mix_audio.generate_premiere_xml", return_value="/path/test.xml"):
            
            result = process_audio(performer, date)
            
            assert result is not None
            
            # 書き込まれたデータを確認
            call_args = mock_write.call_args[0]
            written_data = call_args[1]
            
            # 元の音声データより長くなっていることを確認（無音が挿入されたため）
            original_length = len(mono_data)
            expected_silence_samples = int(0.5 * sample_rate)  # 0.5秒の無音
            expected_min_length = original_length * 2 + expected_silence_samples
            
            assert len(written_data) >= expected_min_length

    @pytest.mark.unit
    def test_process_audio_directory_creation(self, temp_dir):
        """ディレクトリ作成のテスト"""
        performer = "テスト演者"
        date = "0615"
        
        with patch("utils.audio.mix_audio.ROOT_DIR", str(temp_dir)), \
             patch("utils.audio.mix_audio.glob.glob", return_value=[]), \
             patch("utils.audio.mix_audio.os.path.exists") as mock_exists:
            
            # 演者ディレクトリは存在するが、outputディレクトリは存在しない設定
            def side_effect(path):
                if "output" in path:
                    return False
                if performer in path and "output" not in path:
                    return True
                return False
            
            mock_exists.side_effect = side_effect
            
            with patch("utils.audio.mix_audio.os.makedirs") as mock_makedirs:
                result = process_audio(performer, date)
                
                # ディレクトリ作成が呼ばれることを確認
                mock_makedirs.assert_called()