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
| 🎙️ **自动配音** | macOS 离线中文语音（Tingting 女声 / Sinji 男声交替），情绪控制语速；跨平台自动降级静音音频兜底 |
| 🎞️ **视频合成** | 逐镜 Ken Burns 推拉运镜 + 字幕烧录 + 音画严格对齐，concat 拼接输出完整漫剧 |
| 🚀 **其他创新** | 模板变量驱动批量生产 / 男女声自动交替 / 画风一键切换（古风·赛博·日漫·水彩）/ 每日限额 / VIP 收藏上限 |

## 🛠 技术栈

**后端**：FastAPI · SQLAlchemy 2.0 · Pydantic v2 · SQLite（可选 MySQL）· FFmpeg · Pillow
**前端**：Vue 3.5 · Vite · Element Plus · Pinia · Vue Router
**模型服务**：Pollinations 文生图（免费）· macOS say TTS（离线）· DeepSeek LLM（可选，预留）

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

## 🔑 模型 API 配置

所有配置集中在 `backend/.env`（模板见 `backend/.env.example`，复制即用）：

```bash
cd backend && cp .env.example .env
```

### 三大引擎一览

| 引擎 | 配置项 | 默认 | 说明 |
|------|--------|------|------|
| **TTS 配音** | `TTS_ENGINE` | `auto` | `auto`(macOS 语音/跨平台兜底) · `say` · `silence` · `edge` · `aliyun` |
| **文生图** | `IMAGE_GEN_ENGINE` | `pollinations` | `pollinations`(免费真实) · `local`(离线) · `mock` |
| **剧本 LLM** | `LLM_API_KEY` 等 | 空 | 模板驱动无需 LLM 即可跑通；填入后启用 AI 剧本/变量补全 |

### 详细配置示例

```ini
# ① 文生图：免费真实出图（默认，需外网）
IMAGE_GEN_ENGINE=pollinations
IMAGE_CONCURRENCY=1        # 免费服务建议 1，稳定优先

# 换用硅基流动·可图（更快、更稳，注册 https://siliconflow.cn 获取 Key）
# IMAGE_GEN_ENGINE=kolors
# KOLORS_API_KEY=sk-xxxx

# 换用本地离线出图（评测/无网环境）
# IMAGE_GEN_ENGINE=local

# ② 配音：macOS 用系统语音；Windows/Linux 自动静音兜底保证出片
TTS_ENGINE=auto

# 接入阿里云 TTS 提升音质（需云账号密钥）
# TTS_ENGINE=aliyun
# ALIYUN_TTS_ACCESS_KEY_ID=xxxx
# ALIYUN_TTS_ACCESS_KEY_SECRET=xxxx
# ALIYUN_TTS_APPKEY=xxxx

# ③ 剧本大模型（DeepSeek，可选）
# LLM_API_KEY=sk-xxxx
# LLM_BASE_URL=https://api.deepseek.com
# LLM_MODEL=deepseek-chat
```

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
│   │       ├── image_gen/        # 文生图：pollinations(真实) / local(离线) / mock
│   │       ├── tts/              # 配音：say(macOS) / silence(兜底) / edge(预留)
│   │       └── video_composer.py # Ken Burns 运镜 + 字幕烧录 + 拼接
│   ├── init_db.py                # 建库建表 + 10 套模板种子数据
│   ├── tests/                    # 自动化测试（时长对齐/运镜/字幕/异常）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/                # 模板中心/工作台/AI生成/登录等页面
│   │   └── api/index.js          # axios 封装（/api 代理）
│   └── vite.config.js            # 开发代理（/api、/uploads → :8000）
└── AI漫剧制作平台实训报告.md / .tex   # 实训报告（可转 docx）
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
默认 `TTS_ENGINE=auto`：非 macOS 自动使用静音音频兜底（视频可正常出片）。想要真实配音：接入阿里云/火山 TTS 并填入密钥，或配置代理使用 Edge-TTS。

**Q3：图片生成失败？**
Pollinations 为免费公共服，偶发限流。已内置 3 次重试 + 本地占位图回落，流水线不中断。离线环境可将 `IMAGE_GEN_ENGINE` 改为 `local`。

**Q4：如何换 MySQL？**
`backend/.env` 中 `DB_TYPE=mysql` 并填写 DB_HOST/DB_USER 等，随后重跑 `init_db.py` 即可（SQLAlchemy 自动建表）。

**Q5：部署到服务器？**
后端为纯 Python 服务：`uvicorn app.main:app --host 0.0.0.0 --port 8000`，前端构建后由后端自动托管；或用 `gunicorn -k uvicorn.workers.UvicornWorker` 多进程。

---

## 📄 实训报告

- `AI漫剧制作平台实训报告.md` / `.tex`：完整 12 章实训报告（需求分析 / 总体设计 / 数据库设计 / 模块实现 / 测试 / 总结）
- 报告配套：自动化测试数据、架构图、数据库 ER 图、接口文档

---

## 📜 开源协议

本项目为教学实训项目，代码仅供学习交流。
