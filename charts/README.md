# 报告图表源文件与导出清单

本目录提供报告所需的全部图表源文件（draw.io 格式 + mermaid 格式），任选一种导出 PNG 后放入项目根目录 `assets/`，然后重新生成 docx 即可。

## 导出方法

### 方式一：draw.io（推荐，老师推荐工具）
1. 打开 https://app.diagrams.net
2. File → Open from... → 选择本目录 `.drawio` 文件
3. File → Export as → PNG（缩放建议 200%）
4. 按下表文件名保存到 `assets/`

### 方式二：mermaid
1. 打开 https://mermaid.live
2. 粘贴对应 `.md` 文件中的 mermaid 代码
3. 右上角 Download → PNG
4. 按下表文件名保存到 `assets/`

## 需导出的图表清单

| 报告位置 | 图编号 | 文件名 | 源文件 |
|---|---|---|---|
| 2.2 用例图 | 图 2-1 | `usecase.png` | `usecase.drawio` / `usecase.md` |
| 3.1 系统架构图 | 图 3-1 | `architecture.png` | `architecture.drawio` / `architecture.md` |
| 3.3 数据流向图 | 图 3-2 | `dataflow.png` | `flow.drawio` / `flow.md` |
| 3.3 时序图 | 图 3-3 | `sequence.png` | `sequence.drawio` / `sequence.md` |
| 5.1 ER 图 | 图 5-1 | `er-diagram.png` | `er-diagram.drawio` / `er-diagram.md` |

导出完成后运行（在项目根目录）：

```bash
pandoc "AI漫剧制作平台实训报告.md" -o "202330124036_潘磊_实训报告.docx"
```

## 运行截图清单（必须实际运行画面，无法代截图）

| 报告位置 | 图编号 | 文件名 | 截图内容 |
|---|---|---|---|
| 11.1 | 图 11-1 | `shot-home.png` | 平台首页（运行 `./start.sh` 后打开 http://localhost:8000） |
| 11.1 | 图 11-2 | `shot-template.png` | 模板中心页面 |
| 11.1 | 图 11-3 | `shot-workspace.png` | 模板工作台（变量表单） |
| 11.1 | 图 11-4 | `shot-progress.png` | 生成任务五步进度 |
| 11.1 | 图 11-5 | `shot-images.png` | 分镜图片生成结果 |
| 11.1 | 图 11-6 | `shot-video.png` | 最终视频播放画面（含字幕） |
