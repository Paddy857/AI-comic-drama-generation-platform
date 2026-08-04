"""测试用例 2：Ken Burns 推/拉镜头动态效果 + 中文台词字幕烧录。

覆盖：
- 画面动态：抽取相邻两帧做像素差分，差值必须 > 0（静态图被施加了运动效果，非静止画面）。
- 推近方向：推镜头时，末帧中心区域 = 首帧中心区域的 1.15 倍放大（等比 resize 后对齐，
  其 MSE 应显著小于「首帧角落区域 vs 末帧中心」的错位 MSE）。
- 字幕烧录：视频底部区域存在白色文字像素（白字+黑描边烧录成功）。
"""

import os

from PIL import Image

from common import OUT_DIR, extract_frame, ensure_fixtures
from app.services.video_composer import VideoComposer

SUB_TITLE = "我，龙傲天，回来了！今日本座，定要讨个说法！"
ZOOM_MAX = 1.15  # 与 video_composer 中 zoompan 的最大放大倍数一致


def _mean_diff(png_a: str, png_b: str) -> float:
    """两帧灰度图的平均绝对像素差（隔行采样）。"""
    a = Image.open(png_a).convert("L")
    b = Image.open(png_b).convert("L")
    w, h = a.size
    pa, pb = a.load(), b.load()
    total, count = 0, 0
    for y in range(0, h, 10):
        for x in range(0, w, 10):
            total += abs(pa[x, y] - pb[x, y])
            count += 1
    return total / count


def _mse(img_a: Image.Image, img_b: Image.Image) -> float:
    pa, pb = img_a.load(), img_b.load()
    w, h = img_a.size
    total, count = 0, 0
    for y in range(0, h, 6):
        for x in range(0, w, 6):
            total += (pa[x, y] - pb[x, y]) ** 2
            count += 1
    return total / count


def main() -> None:
    img, audio = ensure_fixtures()
    composer = VideoComposer()

    # ── 1. 合成推镜头视频（带字幕） ──────────────────────
    out = os.path.join(OUT_DIR, "test02_in.mp4")
    composer.compose(img, audio, SUB_TITLE, out, direction="in")

    # ── 2. 间隔帧差分：证明画面在动（Ken Burns 生效） ────
    # 轻微推镜头每帧变化极小，取间隔 20 帧（0.8s）差分放大信号
    f_a = extract_frame(out, 25, os.path.join(OUT_DIR, "test02_f25.png"))
    f_b = extract_frame(out, 45, os.path.join(OUT_DIR, "test02_f45.png"))
    diff = _mean_diff(f_a, f_b)
    print(f"间隔20帧平均像素差: {diff:.2f}")
    assert diff > 1.0, "画面静止，Ken Burns 动态效果未生效！"

    # ── 3. 推近方向：末帧中心 = 首帧中心的等比放大 ────────
    first = Image.open(extract_frame(out, 0, os.path.join(OUT_DIR, "test02_f0.png"))).convert("L")
    last = Image.open(extract_frame(out, 125, os.path.join(OUT_DIR, "test02_f125.png"))).convert("L")
    w, h = first.size
    c = 400                                  # 首帧中心取样边长
    c2 = int(c * ZOOM_MAX)                   # 放大后对应边长
    center_first = first.crop((w // 2 - c, h // 2 - c, w // 2 + c, h // 2 + c))
    zoomed_first = center_first.resize((c2, c2))          # 模拟末帧应显示的内容
    region_last = last.crop((w // 2 - c2, h // 2 - c2, w // 2 + c2, h // 2 + c2))
    corner_first = first.crop((0, 0, c2, c2)).resize((c2, c2))  # 错位对照：首帧角落

    mse_aligned = _mse(zoomed_first, region_last)
    mse_misaligned = _mse(corner_first, region_last)
    print(f"推近对齐 MSE: {mse_aligned:.2f} | 错位对照 MSE: {mse_misaligned:.2f}")
    assert mse_aligned < mse_misaligned * 0.8, "推近镜头中心未等比放大，方向异常！"

    # ── 4. 字幕烧录验证：底部区域白色像素 ───────────────
    frame = Image.open(f_b).convert("RGB")
    w, h = frame.size
    bottom = frame.crop((0, h - 250, w, h))
    px = bottom.load()
    white = sum(
        1 for y in range(0, bottom.height, 2) for x in range(0, bottom.width, 2)
        if px[x, y][0] > 230 and px[x, y][1] > 230 and px[x, y][2] > 230
    )
    print(f"字幕区白色像素数: {white}")
    assert white > 50, "字幕未烧录到底部区域！"

    # 清理抽帧产物
    for f in ("test02_f0.png", "test02_f25.png", "test02_f45.png", "test02_f125.png"):
        p = os.path.join(OUT_DIR, f)
        if os.path.exists(p):
            os.remove(p)

    print("PASS: 用例2 Ken Burns 动态效果 + 字幕烧录验证通过")


if __name__ == "__main__":
    main()
