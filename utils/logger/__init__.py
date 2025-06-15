import coloredlogs
import logging
import os
from datetime import datetime
import sys

# ルートディレクトリの特定
# 絶対パスを取得
root_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# ログディレクトリの作成
log_dir = os.path.join(root_dir, "log")
os.makedirs(log_dir, exist_ok=True)

# ログファイル名の設定（現在の日付を使用）
current_date = datetime.now().strftime("%Y-%m-%d")
log_file = os.path.join(log_dir, f"{current_date}.log")

# ロガーの設定
logger = logging.getLogger("voice_app")
logger.setLevel(logging.INFO)
# 既存のハンドラを削除（二重登録防止）
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

# ファイルハンドラーの設定
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# コンソールハンドラーの設定（カラー付き）
coloredlogs.install(
    level=logging.INFO,
    logger=logger,
    fmt="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level_styles={
        "debug": {"color": "cyan"},
        "info": {"color": "green"},
        "warning": {"color": "yellow"},
        "error": {"color": "red"},
        "critical": {"color": "red", "bold": True},
    },
)

logger.info(f"ログシステム初期化: {log_file}")
logger.debug(f"アプリケーションルートディレクトリ: {root_dir}")


def get_logger():
    """アプリケーションロガーを取得する関数"""
    return logger
