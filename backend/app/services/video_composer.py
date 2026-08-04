"""VideoComposer：利用 FFmpeg 将「图片 + 音频 + 字幕」合成为带 Ken Burns 动态效果的视频片段。

核心特性：
- 视频时长严格与音频时长一致（先 ffprobe 探测音频时长，再按帧数精确控制 + -t 截断）
- 静态图施加推/拉镜头 Ken Burns 效果（zoompan 滤镜），避免画面僵硬
- 台词自动烧录为底部字幕（Pillow 渲染透明字幕 PNG + overlay 叠加，内置中文字体探测，自动换行）

说明：本机 brew 版 FFmpeg 未编译 drawtext/subtitles 滤镜，故字幕采用
Pillow 预处理成 RGBA PNG，再用 overlay 滤镜叠加，兼容任何精简版 FFmpeg。

依赖：系统需安装 ffmpeg（含 ffprobe）与 Python 包 pillow。
macOS: brew install ffmpeg && pip install pillow
"""

import os
import subprocess
import tempfile
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = ImageDraw = ImageFont = None

# 常见中文字体路径（按系统探测）
_FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",                # macOS 苹方
    "/System/Library/Fonts/Hiragino Sans GB.ttc",        # macOS 冬青黑体
    "/System/Library/Fonts/STHeiti Light.ttc",           # macOS 华文黑体
    "/System/Library/Fonts/Supplemental/Songti.ttc",     # macOS 宋体
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux Noto
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",      # Linux 文泉驿
]


class VideoComposer:
    FPS = 25

    def __init__(self, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe", fps: int = 25):
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe
        self.FPS = fps
        self._ensure_binaries()

    # ── 公共入口 ──────────────────────────────────────────

    def compose(
        self,
        image_path: str,
        audio_path: str,
        subtitle_text: str,
        output_path: str,
        width: int = 1080,
        height: int = 1920,
        direction: str = "in",
        font_path: Optional[str] = None,
        wrap_chars: int = 18,
    ) -> str:
        """合成视频片段。

        Args:
            image_path: 静态图片路径
            audio_path: 配音音频路径
            subtitle_text: 台词文本（烧录为底部字幕；空字符串则不烧字幕）
            output_path: 输出视频路径（mp4）
            width/height: 输出分辨率（默认竖屏 1080x1920）
            direction: Ken Burns 方向 "in"(推近) / "out"(拉远)，None 则随机
            font_path: 字幕中文字体路径；缺省自动探测系统字体
            wrap_chars: 字幕单行最大字符数（自动换行）

        Returns:
            输出视频路径

        Raises:
            FileNotFoundError: 输入文件缺失
            RuntimeError: ffmpeg 执行失败（含 stderr 摘要）
        """
        if Image is None:
            raise RuntimeError("缺少 Pillow 依赖，请先执行: pip install pillow")

        for p, label in ((image_path, "图片"), (audio_path, "音频")):
            if not os.path.isfile(p):
                raise FileNotFoundError(f"{label}文件不存在: {p}")

        duration = self._probe_duration(audio_path)
        if duration <= 0:
            raise RuntimeError(f"无法获取音频时长: {audio_path}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        subtitle_png = self._render_subtitle_png(
            self._wrap_text(subtitle_text, wrap_chars),
            output_path=output_path,
            width=width,
            height=height,
            font_path=font_path or self._find_font(),
        )

        try:
            cmd = self._build_command(
                image_path=image_path,
                audio_path=audio_path,
                subtitle_png=subtitle_png,
                output_path=output_path,
                duration=duration,
                width=width,
                height=height,
                direction=direction,
            )
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg 合成失败(exit={proc.returncode}): "
                    f"{proc.stderr.strip()[-800:]}"
                )
            if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                raise RuntimeError("FFmpeg 未生成输出文件")
            return output_path
        finally:
            if subtitle_png and os.path.exists(subtitle_png):
                os.remove(subtitle_png)

    # ── FFmpeg 命令构建 ───────────────────────────────────

    def _build_command(
        self,
        image_path: str,
        audio_path: str,
        subtitle_png: Optional[str],
        output_path: str,
        duration: float,
        width: int,
        height: int,
        direction: Optional[str],
    ) -> list:
        total_frames = max(2, round(duration * self.FPS))
        dir_ = direction or ("in" if (total_frames % 2 == 0) else "out")
        if dir_ == "in":
            zoom = f"1.0+0.15*on/({total_frames}-1)"
        else:
            zoom = f"1.15-0.15*on/({total_frames}-1)"

        # 第一段：缩放铺满 + 居中裁剪 + Ken Burns 推拉镜头
        kenburns = (
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={self.FPS}"
        )

        cmd = [self.ffmpeg, "-y", "-i", image_path]
        if subtitle_png:
            cmd += ["-i", subtitle_png]
            # 第二段：字幕 PNG 叠加到底部居中（eof_action=repeat 保证持续到主视频结束）
            vf = (
                f"{kenburns}[v0];"
                f"[v0][1:v]overlay=x=(W-w)/2:y=H-h-120:eof_action=repeat[v]"
            )
            audio_idx = 2
        else:
            vf = kenburns + "[v]"
            audio_idx = 1

        cmd += [
            "-i", audio_path,
            "-filter_complex", vf,
            "-map", "[v]", "-map", f"{audio_idx}:a",
            "-t", f"{duration:.3f}",   # 严格截断到音频时长
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",                # 兜底：任一输入结束即结束
            "-movflags", "+faststart",
            output_path,
        ]
        return cmd

    # ── 辅助方法 ──────────────────────────────────────────

    @staticmethod
    def concat_clips(clip_paths, output_path, ffmpeg: str = "ffmpeg") -> str:
        """按顺序拼接多个同参数视频片段（concat demuxer + 流复制）"""
        if not clip_paths:
            raise ValueError("没有可拼接的视频片段")
        list_file = output_path + ".txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in clip_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")
        try:
            subprocess.run(
                [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", list_file,
                 "-c", "copy", output_path],
                check=True, capture_output=True, timeout=600,
            )
        finally:
            if os.path.exists(list_file):
                os.remove(list_file)
        return output_path

    def _probe_duration(self, media_path: str) -> float:
        """ffprobe 探测媒体时长（秒）"""
        proc = subprocess.run(
            [self.ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", media_path],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"ffprobe 探测失败: {proc.stderr.strip()}")
        return float(proc.stdout.strip())

    def _render_subtitle_png(
        self,
        text: str,
        output_path: str,
        width: int,
        height: int,
        font_path: Optional[str],
    ) -> Optional[str]:
        """用 Pillow 把字幕渲染成透明背景 PNG（白字+黑描边，每行居中，底部留白）。

        返回 PNG 路径；文本为空返回 None（不烧字幕）。
        """
        if not text:
            return None

        font_size = max(24, min(42, height // 50))  # 1080x1920 → 38px
        try:
            font = ImageFont.truetype(font_path, font_size) if font_path else None
        except OSError:
            font = None
        if font is None:
            font = ImageFont.load_default()

        ascent, descent = font.getmetrics()
        line_h = ascent + descent + 8
        stroke_w = max(2, font_size // 12)
        pad = 8

        lines = text.split("\n")
        total_h = line_h * len(lines) + pad * 2

        # 整幅宽度的透明画布，每行单独居中绘制，再裁剪到文字紧贴区域
        img = Image.new("RGBA", (width, total_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        y = pad
        for line in lines:
            bbox = draw.textbbox((0, y), line, font=font, stroke_width=stroke_w)
            line_w = bbox[2] - bbox[0]
            x = max(0, (width - line_w) // 2)
            draw.text(
                (x, y), line, font=font,
                fill=(255, 255, 255, 255),
                stroke_width=stroke_w,
                stroke_fill=(0, 0, 0, 220),
            )
            y += line_h

        tight = img.getbbox()
        if tight:
            img = img.crop(tight)

        fd, png_path = tempfile.mkstemp(
            suffix=".png", dir=os.path.dirname(os.path.abspath(output_path))
        )
        os.close(fd)
        img.save(png_path, "PNG")
        return png_path

    @staticmethod
    def _wrap_text(text: str, wrap_chars: int) -> str:
        """按字符数自动换行（最多 3 行，超出截断加省略号）"""
        text = (text or "").strip()
        if not text:
            return ""
        lines = [text[i : i + wrap_chars] for i in range(0, len(text), wrap_chars)]
        if len(lines) > 3:
            lines = lines[:3]
            lines[-1] = lines[-1][:-1] + "…"
        return "\n".join(lines)

    @staticmethod
    def _find_font() -> Optional[str]:
        """探测系统可用中文字体"""
        for path in _FONT_CANDIDATES:
            if os.path.isfile(path):
                return path
        return None

    @staticmethod
    def _ensure_binaries() -> None:
        for binary in ("ffmpeg", "ffprobe"):
            if not VideoComposer._which(binary):
                raise RuntimeError(
                    f"未找到 {binary}，请先安装 FFmpeg（macOS: brew install ffmpeg）"
                )

    @staticmethod
    def _which(binary: str) -> Optional[str]:
        for path in os.environ.get("PATH", "").split(os.pathsep):
            candidate = os.path.join(path, binary)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        return None
