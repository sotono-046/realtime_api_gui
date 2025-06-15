import coloredlogs
import logging
import os
from datetime import datetime

# ログディレクトリの作成
# PyInstaller 実行時は書き込み可能なディレクトリを使用
import sys
if getattr(sys, 'frozen', False):
    # PyInstaller で実行されている場合
    import tempfile
    log_dir = os.path.join(tempfile.gettempdir(), "realtime_api_gui", "log")
else:
    # 通常の Python で実行されている場合
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")

try:
    os.makedirs(log_dir, exist_ok=True)
except PermissionError:
    # 権限エラーの場合、システムの一時ディレクトリを使用
    import tempfile
    log_dir = tempfile.gettempdir()

# ログファイル名の設定（現在の日付を使用）
current_date = datetime.now().strftime("%Y-%m-%d")
log_file = os.path.join(log_dir, f"{current_date}.log")

# ロガーの設定
logger = logging.getLogger(__name__)
coloredlogs.install(
    level="INFO", fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
)

# ログファイル設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ファイルハンドラーの設定
file_handler = logging.FileHandler(log_file, encoding="utf-8")

file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# コンソールハンドラーの設定（カラー付き）
coloredlogs.install(
    level=logging.INFO,
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


def get_logger():
    return logger
