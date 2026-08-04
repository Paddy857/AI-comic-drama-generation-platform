"""共享测试基础设施：素材生成 + 路径配置。

三个测试用例（test_01/02/03）共用本模块，避免重复代码。
"""

import os
import shutil
import subprocess
import sys

# 使脚本可直接运行：sys.path 注入 backend 根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# 测试素材与输出目录
TMP_DIR = os.path.join(BASE_DIR, "_fixtures")
OUT_DIR = os.path.join(TMP_DIR, "out")

SCENE_IMG = os.path.join(TMP_DIR, "scene.png")     # 1080x1920 竖屏静态图
VOICE_AUDIO = os.path.join(TMP_DIR, "voice.wav")   # 5.3s 正弦音频（非整数秒，验证对齐）


def ensure_fixtures() -> tuple[str, str]:
    """幂等生成测试素材，返回 (图片路径, 音频路径)。"""
    os.makedirs(OUT_DIR, exist_ok=True)
    if not (os.path.isfile(SCENE_IMG) and os.path.isfile(VOICE_AUDIO)):
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
             "-i", "testsrc=size=1080x1920", "-frames:v", "1", SCENE_IMG],
            check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
             "-i", "sine=frequency=440:duration=5.3", VOICE_AUDIO],
            check=True,
        )
    return SCENE_IMG, VOICE_AUDIO


def cleanup() -> None:
    """删除测试素材与输出（readme 中说明，可手动调用）。"""
    shutil.rmtree(TMP_DIR, ignore_errors=True)


def extract_frame(video_path: str, frame_index: int, png_path: str) -> str:
    """抽取视频指定帧为 PNG，返回路径。"""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", video_path,
         "-vf", f"select=eq(n\\,{frame_index})", "-frames:v", "1", png_path],
        check=True,
    )
    return png_path
