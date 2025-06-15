import os
from pathlib import Path
import tempfile
from datetime import datetime
import soundfile as sf
import sounddevice as sd
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from utils.logger import get_logger
from websocket._app import WebSocketApp
import json
import base64
import wave

# ロガーの取得
logger = get_logger()

# アプリケーションのルートディレクトリを取得
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# .envファイルを検索して読み込む
dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path, override=True)
    logger.info(f".envファイルを読み込みました: {dotenv_path}")
else:
    logger.warning(".envファイルが見つかりませんでした")


class VoiceGenerator:
    # その他の演者用のデフォルト設定
    FALLBACK_VOICE_SETTING = {
        "voice": "alloy",  # デフォルト音声
        "speed": 1.3,  # 通常より30%早く
    }

    def __init__(self):
        api_key = self._get_api_key()
        if not api_key:
            logger.error("OPENAI_API_KEYが設定されていません")
            raise ValueError(
                "OPENAI_API_KEYが設定されていません。GUI設定または.envファイルを確認してください。"
            )

        # WebSocket接続の設定
        self.ws = None
        self.ws_url = (
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
        )
        self.ws_headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        self.audio_chunks = bytearray()
        self.client = OpenAI(api_key=api_key)
        self.temp_file = None
        self._create_temp_file()
        self.current_actor = None
        self.current_system_prompt = ""
        self.current_text = ""
        
        # 演者設定をJSONから読み込み
        self.performer_configs = self.load_performer_configs()
        
        logger.info("VoiceGeneratorが初期化されました")
    
    def _get_api_key(self):
        """APIキーを取得（GUI設定ファイル → 環境変数の順で確認）"""
        # 1. GUI設定ファイルから取得を試行
        try:
            settings_file = os.path.join(ROOT_DIR, 'config', 'settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    api_key = settings.get('openai_api_key', '').strip()
                    if api_key:
                        logger.info("GUI設定からAPIキーを読み込みました")
                        return api_key
        except Exception as e:
            logger.warning(f"GUI設定ファイルの読み込みに失敗: {e}")
        
        # 2. 環境変数から取得
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            logger.info("環境変数からAPIキーを読み込みました")
            return api_key.strip()
        
        return None

    def _create_temp_file(self):
        """一時ファイルを作成する"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except (OSError, PermissionError) as e:
                logger.warning(f"一時ファイルの削除に失敗しました: {e}")

        # tempモジュールを使用して一時ファイルを作成
        temp_dir = os.path.join(ROOT_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        self.temp_file = tempfile.mktemp(suffix=".wav", dir=temp_dir)
        logger.debug(f"一時ファイルを作成: {self.temp_file}")
    
    def load_performer_configs(self):
        """演者設定をJSONファイルから読み込み"""
        try:
            config_file = os.path.join(ROOT_DIR, "config", "prompts.json")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning("prompts.jsonファイルが見つかりません")
                return {}
        except Exception as e:
            logger.error(f"演者設定の読み込みに失敗: {e}")
            return {}

    def set_actor(self, actor: str):
        """演者を設定する"""
        self.current_actor = actor
        logger.info(f"演者を設定: {actor}")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            logger.debug(f"受信データ: {data['type']}")

            if data["type"] == "response.audio.delta":
                if "delta" not in data:
                    logger.error("音声データが未定義です")
                    return
                audio_buffer = base64.b64decode(data["delta"])
                self.audio_chunks.extend(audio_buffer)
                logger.debug(
                    f"音声データ受信. Chunk size: {len(audio_buffer)}, Total size: {len(self.audio_chunks)}"
                )

            elif data["type"] == "response.audio.done":
                logger.info("音声データの受信が完了しました")
                if len(self.audio_chunks) == 0:
                    logger.warning("音声データが空です")
                    return

                # 一時ファイルを作成
                self._create_temp_file()

                # WAVファイルとして保存
                with wave.open(self.temp_file, "wb") as wav_file:
                    wav_file.setnchannels(1)  # モノラル
                    wav_file.setsampwidth(2)  # 16ビット
                    wav_file.setframerate(24000)  # サンプルレート
                    wav_file.writeframes(self.audio_chunks)

                self.audio_chunks = bytearray()
                logger.info(f"音声ファイルを保存: {self.temp_file}")

            elif data["type"] == "response.done":
                logger.info("レスポンスが完了しました")
                # WebSocket接続を閉じる
                if self.ws:
                    self.ws.close()

        except Exception as e:
            logger.error(f"メッセージ処理エラー: {str(e)}", exc_info=True)

    def _on_error(self, ws, error):
        logger.error(f"WebSocketエラー: {str(error)}")
        # エラー発生時も接続を閉じる
        if self.ws:
            self.ws.close()

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket接続が閉じられました")

    def _on_open(self, ws):
        logger.info("WebSocket接続が確立されました")
        # セッション設定を送信
        # 演者の音声設定をJSONから取得（存在しない場合はフォールバック設定を使用）
        if self.current_actor in self.performer_configs and "voice" in self.performer_configs[self.current_actor]:
            voice_config = {
                "voice": self.performer_configs[self.current_actor]["voice"],
                "speed": self.performer_configs[self.current_actor].get("speed", 1.3)
            }
        else:
            voice_config = self.FALLBACK_VOICE_SETTING
            logger.warning(f"演者 '{self.current_actor}' の音声設定が見つかりません。デフォルト設定を使用します。")
        
        session_config = {
            "type": "session.update",
            "session": {
                "voice": voice_config["voice"],
                "instructions": self.current_system_prompt,
                "turn_detection": {"type": "server_vad"},
                "modalities": ["text", "audio"],
                "temperature": 0.8,
            },
        }
        ws.send(json.dumps(session_config))

        # メッセージを作成して送信
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": self.current_text}],
            },
        }
        ws.send(json.dumps(message))
        ws.send(json.dumps({"type": "response.create"}))

    def generate_voice(self, system_prompt: str, acting_prompt: str, text: str) -> str:
        """音声を生成する"""
        if not self.current_actor:
            logger.error("演者が設定されていません")
            raise ValueError(
                "演者が設定されていません。set_actorを呼び出してください。"
            )

        # 現在の演者の音声設定を取得
        if self.current_actor in self.performer_configs and "voice" in self.performer_configs[self.current_actor]:
            voice_config = {
                "voice": self.performer_configs[self.current_actor]["voice"],
                "speed": self.performer_configs[self.current_actor].get("speed", 1.3)
            }
        else:
            voice_config = self.FALLBACK_VOICE_SETTING
            logger.warning(f"演者 '{self.current_actor}' の音声設定が見つかりません。デフォルト設定を使用します。")
        logger.info(f"音声生成開始 - 演者: {self.current_actor}")

        try:
            # プロンプトとテキストを保存
            self.current_system_prompt = system_prompt
            self.current_text = f"{acting_prompt}\n「{text}」"

            # WebSocket接続を確立
            self.ws = WebSocketApp(
                self.ws_url,
                header=self.ws_headers,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open,
            )
            self.ws.run_forever()

            # 接続が閉じられた後に一時ファイルが存在することを確認
            if not self.temp_file or not os.path.exists(self.temp_file):
                raise Exception("音声ファイルの生成に失敗しました")

            return self.temp_file
        except Exception as e:
            logger.error(f"音声生成エラー: {str(e)}", exc_info=True)
            raise

    def save_voice(self, actor: str) -> str:
        """生成した音声を保存する"""
        if not self.temp_file or not os.path.exists(self.temp_file):
            logger.warning("保存するファイルがありません")
            return None

        timestamp = datetime.now().strftime("%m%d_%H%M%S")

        # 演者のディレクトリを作成
        actor_dir = os.path.join(ROOT_DIR, actor)
        os.makedirs(actor_dir, exist_ok=True)

        save_path = os.path.join(actor_dir, f"{actor}_{timestamp}.wav")
        try:
            # 一時ファイルからコピーして保存（os.renameは異なるディスクだとエラーになる可能性がある）
            with open(self.temp_file, "rb") as src, open(save_path, "wb") as dst:
                dst.write(src.read())
            # 一時ファイルを削除
            os.remove(self.temp_file)
            self.temp_file = None
            logger.info(f"音声ファイルを保存: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"ファイル保存エラー: {str(e)}", exc_info=True)
            raise

    def play_audio(self, file_path: str = None):
        """音声を再生する"""
        target_file = file_path if file_path else self.temp_file
        if not target_file or not os.path.exists(target_file):
            logger.warning("再生するファイルがありません")
            return

        try:
            data, samplerate = sf.read(target_file)
            sd.play(data, samplerate)
            sd.wait()
            logger.info("音声再生完了")
        except Exception as e:
            logger.error(f"音声再生エラー: {str(e)}", exc_info=True)
            raise
