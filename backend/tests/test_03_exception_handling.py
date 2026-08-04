"""测试用例 3：异常处理与边界场景。

覆盖：
- 图片文件不存在 → 抛 FileNotFoundError
- 音频文件不存在 → 抛 FileNotFoundError
- 空字幕（不烧字幕）→ 正常合成，时长仍严格对齐
- 非法超大分辨率 → ffmpeg 失败抛 RuntimeError
- 输出目录不存在 → 自动创建并成功输出
"""

import os

from common import OUT_DIR, ensure_fixtures
from app.services.video_composer import VideoComposer


def main() -> None:
    img, audio = ensure_fixtures()
    composer = VideoComposer()
    audio_dur = composer._probe_duration(audio)

    # ── 1. 图片缺失 → FileNotFoundError ──────────────────
    try:
        composer.compose("/nonexistent_scene.png", audio, "x",
                         os.path.join(OUT_DIR, "test03_nope1.mp4"))
        raise AssertionError("图片缺失未抛 FileNotFoundError！")
    except FileNotFoundError as e:
        print(f"图片缺失 OK: {e}")

    # ── 2. 音频缺失 → FileNotFoundError ──────────────────
    try:
        composer.compose(img, "/nonexistent_voice.wav", "x",
                         os.path.join(OUT_DIR, "test03_nope2.mp4"))
        raise AssertionError("音频缺失未抛 FileNotFoundError！")
    except FileNotFoundError as e:
        print(f"音频缺失 OK: {e}")

    # ── 3. 空字幕 → 正常合成且时长对齐 ──────────────────
    out = os.path.join(OUT_DIR, "test03_no_sub.mp4")
    composer.compose(img, audio, "", out, direction="out")
    dur = composer._probe_duration(out)
    print(f"空字幕合成时长: {dur:.3f}s | 偏差: {abs(dur - audio_dur) * 1000:.1f}ms")
    assert abs(dur - audio_dur) < 0.1, "空字幕合成时长未对齐！"

    # ── 4. 非法超大分辨率 → ffmpeg 失败抛 RuntimeError ───
    try:
        composer.compose(img, audio, "x", os.path.join(OUT_DIR, "test03_bad.mp4"),
                         width=99999, height=99999)
        raise AssertionError("非法分辨率未抛 RuntimeError！")
    except RuntimeError as e:
        print(f"FFmpeg 失败 OK: {str(e)[:60]}...")

    # ── 5. 输出目录不存在 → 自动创建并成功 ───────────────
    deep_out = os.path.join(OUT_DIR, "nested", "deep", "test03_auto_dir.mp4")
    composer.compose(img, audio, "自动创建输出目录", deep_out)
    print(f"自动建目录输出: {os.path.getsize(deep_out) / 1024:.0f}KB")
    assert os.path.isfile(deep_out) and os.path.getsize(deep_out) > 0

    print("PASS: 用例3 异常处理与边界场景验证通过")


if __name__ == "__main__":
    main()
