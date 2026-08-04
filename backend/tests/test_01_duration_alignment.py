"""测试用例 1：视频时长严格与音频时长一致。

覆盖：direction="in"（推近）与 direction="out"（拉远）两种方向，
输出视频时长与音频时长偏差必须 < 0.1s。
"""

import os

from common import OUT_DIR, ensure_fixtures  # noqa: E402 需先注入 backend 到 sys.path
from app.services.video_composer import VideoComposer

# 时长对齐容差（秒）
TOLERANCE = 0.1


def main() -> None:
    img, audio = ensure_fixtures()
    composer = VideoComposer()

    audio_dur = composer._probe_duration(audio)
    print(f"音频时长: {audio_dur:.3f}s")

    cases = [
        ("in",  "推近"),
        ("out", "拉远"),
    ]
    for direction, label in cases:
        out = os.path.join(OUT_DIR, f"test01_{direction}.mp4")
        composer.compose(img, audio, "三年之期已满，龙神归位！你们苏家，高攀不起！",
                         out, direction=direction)
        dur = composer._probe_duration(out)
        diff = abs(dur - audio_dur)
        print(f"[{label}] 视频时长: {dur:.3f}s | 偏差: {diff * 1000:.1f}ms")
        assert diff < TOLERANCE, f"{label} 视频时长未对齐: {diff:.3f}s"
        assert os.path.getsize(out) > 0, "输出文件为空"

    print("PASS: 用例1 时长严格对齐验证通过")


if __name__ == "__main__":
    main()
