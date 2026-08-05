# 🎬 AI漫剧制作平台

基于**大模型生态**的模板驱动式 AI 漫剧批量生产平台：从剧本到成片的六步全流程自动化，
支持变量注入模板、真实文生图、自动配音与 Ken Burns 视频合成，最终产出带字幕的完整竖屏漫剧视频。

> 面向短剧制作团队：填几个变量 → 一键生成一部完整漫剧短片。

---

## ✨ 功能特性

| 模块 | 说明 |
|------|------|
| 🧩 **模板中心** | 内置 10 套原创模板（都市赘婿 / 古风甜宠 / 校园甜宠 / 重生首富 / 玄幻退婚 / 闪婚豪门 / 午夜来电 / 嫡女归来 / 总裁老婆 / 末日求生），支持分类、搜索、收藏 |
| 📝 **剧本合成** | 模板变量实时注入（`${变量}` 自动替换），AI 一键补全可选变量，五步进度状态机实时可见 |
| 🎭 **分镜脚本** | 每套模板含 8~18 镜完整脚本（画面 / 台词 / 情绪），逐镜可预览 |
| 🖼️ **分镜生图** | 真实文生图（Pollinations 免费服务），720×1280 竖屏，失败自动回落本地占位图，进度实时回传 |
| 🎙️ **自动配音** | 免费在线 TTS（微软 Edge-TTS 默认，中文音质好），免 Key 真实合成，男女声自动交替；失败自动降级静音音频兜底 |
| 🎞️ **视频合成** | 逐镜 Ken Burns 推拉运镜 + 字幕烧录 + 音画严格对齐，concat 拼接输出完整漫剧 |
| 🚀 **其他创新** | 模板变量驱动批量生产 / 男女声自动交替 / 画风一键切换（古风·赛博·日漫·水彩）/ 每日限额 / VIP 收藏上限 |

## 🛠 技术栈

**后端**：FastAPI · SQLAlchemy 2.0 · Pydantic v2 · SQLite（可选 MySQL）· FFmpeg · Pillow
**前端**：Vue 3.5 · Vite · Element Plus · Pinia · Vue Router
**模型服务**：Edge-TTS 配音 + Pollinations 文生图（免费免 Key）· DeepSeek LLM（可选）

## 🏗 项目架构

```
模板中心 ──> 模板工作台（变量注入）──> 生成任务（五步状态机）
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
  ① 剧本合成（模板渲染）         ③ 分镜生图（批量并发）          ⑤ 配音+渲染
        │                               │                               │
        ▼                               ▼                               ▼
  ② 分镜脚本（逐镜预览）         ④ 图片转视频（Ken Burns）        ⑥ 完整漫剧（concat 拼接）
```

**核心流水线**（后端 `app/routers/generate.py`）：`变量注入模板 → 剧本自动合成 → 角色图生成 → 分镜批量绘图 → 配音合成+渲染`

---

## 🚀 快速开始

### 环境要求

- Python 3.10+（开发环境为 3.14）
- Node.js 18+（仅开发模式需要）
- FFmpeg（`ffmpeg`、`ffprobe` 需在 PATH 中；macOS：`brew install ffmpeg`）

### 方式一：一键启动（推荐）

```bash
# macOS / Linux
./start.sh

# Windows
start.bat
```

脚本会自动：创建虚拟环境 → 安装依赖 → 初始化数据库（含 10 套模板种子）→ 启动服务。

- 若 `frontend/dist` 已构建：**仅需运行后端**，浏览器打开 http://localhost:8000
- 否则自动拉起前端开发服务器：http://localhost:5173

### 方式二：手动启动（开发模式）

```bash
# 1. 后端
cd backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python init_db.py            # 初始化数据库（幂等）
./venv/bin/uvicorn app.main:app --reload --port 8000

# 2. 前端（另一终端）
cd frontend
npm install
npm run dev                             # http://localhost:5173

# 3. 生产模式：前端构建后由后端托管（单命令全站访问）
npm run build                           # 生成 frontend/dist
# 仅启动后端即可访问 http://localhost:8000
```

### 默认账号

| 账号 | 密码 | 说明 |
|------|------|------|
| `admin` | `admin123` | 管理员（VIP，不限生成次数 / 收藏 20 套上限） |

> 开发模式默认关闭鉴权，无需登录即可使用。

---

## 🔑 模型 API 配置（选择与配置说明）

三大 AI 模块（**配音 TTS / 文生图 / 剧本 LLM**）全部通过 `backend/.env` 环境变量一键切换引擎，**无需改代码**。项目内置**免费免 Key 方案**（开箱即用，只需能访问外网），也预留了**真实厂商 API 配置位**（申请到 Key 后填入环境变量即可接入）。

```bash
cd backend && cp .env.example .env   # 默认即免费方案，零配置跑通全流程
```

### 1. 配音 TTS 引擎（`TTS_ENGINE`）

| 引擎 | `TTS_ENGINE` | Key | 说明 |
|------|-------------|-----|------|
| **微软 Edge-TTS**（默认） | `edge` | 免 Key | 免费高质量中文，需外网；失败自动降级静音音频，保证出片 |
| Pollinations 在线 TTS | `pollinations` | 免 Key | 备选；公共端点可能受限（404），可用时免 Key |
| 静音音频（兜底） | `silence` | — | 无配音但能出片 |
| macOS 本地语音 | `say` | — | 仅本机演示 |
| 阿里云 / 火山 CosyVoice 等（预留） | `aliyun` / `cosyvoice` | 需申请 | 见下文「真实厂商接入」 |

```ini
TTS_ENGINE=edge                  # 微软 Edge-TTS（默认，免费）
# TTS_ENGINE=pollinations        # 备选：Pollinations 在线 TTS（端点可能受限）
POLLINATIONS_TTS_BASE_URL=https://text.pollinations.ai
POLLINATIONS_TTS_TIMEOUT=90      # 单次合成超时（秒）
```

### 2. 文生图引擎（`IMAGE_GEN_ENGINE`）

| 引擎 | `IMAGE_GEN_ENGINE` | Key | 说明 |
|------|-------------------|-----|------|
| **Pollinations 文生图**（默认） | `pollinations` | 免 Key | 免费真实出图，需外网；失败自动回落本地占位图 |
| 硅基流动·可图 Kolors（推荐真实方案） | `kolors` | 需申请 | 更快更稳，OpenAI 兼容 |
| 智谱 CogView（可选） | `cogview` | 需申请 | 需自行接入实现 |
| 本地离线（评测/无网） | `local` | — | 纯占位图 |

```ini
IMAGE_GEN_ENGINE=pollinations    # 免费真实文生图（默认）
IMAGE_CONCURRENCY=1              # 免费服务建议 1，稳定优先
# IMAGE_GEN_ENGINE=kolors        # 换用硅基流动·可图
# KOLORS_API_KEY=sk-xxxx
```

### 3. 剧本大模型 LLM（可选，`LLM_API_KEY` 等）

模板驱动模式**无需 LLM** 即可跑通全流程；填入 Key 后启用 AI 剧本改写与变量智能补全（OpenAI 兼容接口）：

```ini
# 方式一：DeepSeek 官方（https://platform.deepseek.com 申请 Key）
LLM_API_KEY=sk-xxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 方式二：硅基流动（https://siliconflow.cn 申请 Key，可用 DeepSeek-V3 等）
# LLM_BASE_URL=https://api.siliconflow.cn/v1
# LLM_MODEL=deepseek-ai/DeepSeek-V3
```

### 4. 真实厂商接入（最终成品推荐方案）

最终交付建议申请以下 API 并填入环境变量，获得更好的音画质量（各引擎实现类按下方说明在 `backend/app/services/` 下注册即可，上层流程零改动）：

| 模块 | 推荐厂商 | 申请入口 | 待接入实现 |
|------|---------|---------|-----------|
| 配音 | 火山引擎 CosyVoice / 阿里云智能语音 | [volcengine.com](https://www.volcengine.com) / [aliyun.com](https://www.aliyun.com) | `services/tts/cosyvoice.py`、`services/tts/aliyun.py` |
| 文生图 | 硅基流动·可图 Kolors | [siliconflow.cn](https://siliconflow.cn) | `services/image_gen/kolors.py`（已预留接口） |
| 剧本 | DeepSeek / 硅基流动 | [platform.deepseek.com](https://platform.deepseek.com) | 已内置（配置 Key 即用） |

---

## 📂 项目结构

```
AIGC/
├── start.sh / start.bat          # 一键启动脚本
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 入口（含前端产物托管）
│   │   ├── core/config.py        # 配置（读取 .env）
│   │   ├── models/               # SQLAlchemy 模型（模板/任务/分镜/用户）
│   │   ├── schemas/              # Pydantic 模型
│   │   ├── routers/              # API 路由（templates/generate/tts/video/...）
│   │   └── services/
│   │       ├── image_gen/        # 文生图：pollinations(免费真实) / local(离线) / mock
│   │       ├── tts/              # 配音：edge(免费在线) / pollinations(备选) / silence(兜底) / say(macOS)
│   │       └── video_composer.py # Ken Burns 运镜 + 字幕烧录 + 拼接
│   ├── init_db.py                # 建库建表 + 10 套模板种子数据
│   ├── tests/                    # 自动化测试（时长对齐/运镜/字幕/异常）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/                # 模板中心/工作台/AI生成/登录等页面
│   │   └── api/index.js          # axios 封装（/api 代理）
│   └── vite.config.js            # 开发代理（/api、/uploads → :8000）
```

---

## 🧪 自动化测试

视频合成核心逻辑已覆盖 3 个测试用例（`backend/tests/`）：

```bash
cd backend && ./venv/bin/python tests/test_0*.py
```

| 用例 | 覆盖点 |
|------|--------|
| test_01_duration_alignment | 视频时长与配音严格对齐（误差 < 0.1s） |
| test_02_kenburns_subtitle | 推近/拉远运镜生效 + 字幕正确烧录 |
| test_03_exception_handling | 缺失素材 / 非法参数 / 空字幕 / 自动建目录 |

---

## ❓ 常见问题（FAQ）

**Q1：生成很慢？**
免费文生图（Pollinations）单张约 20~45 秒，串行保证稳定。接入付费引擎（硅基流动等）可降到 3~5 秒/张。

**Q2：Windows/Linux 上配音没声音？**
默认 `TTS_ENGINE=edge`：微软在线 TTS，任意平台都有真实中文配音。若离线或接口失败，自动降级静音音频兜底（视频仍可出片）。需要更高音质可接入火山/阿里云厂商 API。

**Q3：图片生成失败？**
Pollinations 为免费公共服，偶发限流。已内置 3 次重试 + 本地占位图回落，流水线不中断。离线环境可将 `IMAGE_GEN_ENGINE` 改为 `local`。

**Q4：如何换 MySQL？**
`backend/.env` 中 `DB_TYPE=mysql` 并填写 DB_HOST/DB_USER 等，随后重跑 `init_db.py` 即可（SQLAlchemy 自动建表）。

**Q5：部署到服务器？**
后端为纯 Python 服务：`uvicorn app.main:app --host 0.0.0.0 --port 8000`，前端构建后由后端自动托管；或用 `gunicorn -k uvicorn.workers.UvicornWorker` 多进程。

---

> **说明**：实训报告（含个人信息）仅保存在本地，不随代码仓库提交，以保护隐私。

---

## 📜 开源协议

本项目为教学实训项目，代码仅供学习交流。
