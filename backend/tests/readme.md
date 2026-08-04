# VideoComposer 视频合成测试用例

针对 [VideoComposer](../app/services/video_composer.py)（FFmpeg 将「图片 + 音频 + 字幕」合成为带 Ken Burns 动态效果的视频片段）的端到端验证测试。

## 目录结构

```
backend/tests/
├── common.py                            # 共享基础设施：素材生成、帧抽取、路径注入
├── test_01_duration_alignment.py        # 用例1：视频时长严格与音频时长一致
├── test_02_kenburns_subtitle.py         # 用例2：Ken Burns 推拉镜头 + 中文台词字幕烧录
├── test_03_exception_handling.py        # 用例3：异常处理与边界场景
└── readme.md                            # 本文档
```

运行后会在 `backend/tests/_fixtures/` 下生成测试素材与合成视频产物。

## 环境依赖

- FFmpeg（含 ffprobe），macOS: `brew install ffmpeg`
- Python 包：`pillow`（已加入 `backend/requirements.txt`）

## 运行方式

在 `backend/` 目录下，使用项目虚拟环境执行：

```bash
# 单个用例
./venv/bin/python tests/test_01_duration_alignment.py
./venv/bin/python tests/test_02_kenburns_subtitle.py
./venv/bin/python tests/test_03_exception_handling.py

# 全部用例
for t in tests/test_0*.py; do ./venv/bin/python "$t"; done
```

三个用例相互独立，任意一个失败时其余照常运行。全部通过时每个脚本输出 `PASS: ...` 并以退出码 0 结束。

## 用例覆盖说明

| 用例 | 覆盖点 | 验证标准 |
|---|---|---|
| test_01 | 时长严格对齐 | `direction="in"`（推近）与 `"out"`（拉远）输出视频时长与音频（5.3s）偏差 < 0.1s |
| test_02 | Ken Burns 动态 + 字幕 | 间隔 20 帧像素差分 > 1.0（画面在动）；末帧中心 = 首帧中心等比放大（对齐 MSE < 错位 MSE×0.8，验证推近方向）；底部 250px 区域白色文字像素 > 50（字幕烧录） |
| test_03 | 异常与边界 | 图片/音频缺失抛 `FileNotFoundError`；非法分辨率抛 `RuntimeError`；空字幕正常合成且时长对齐；输出目录不存在时自动创建 |

## 清理

测试素材与产物保存在 `backend/tests/_fixtures/`（重复运行自动复用素材、跳过重新生成）。如需清理：

```bash
./venv/bin/python -c "import sys; sys.path.insert(0, 'tests'); from common import cleanup; cleanup()"
```
