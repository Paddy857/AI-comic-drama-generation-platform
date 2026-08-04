"""Prompt 模板管理器：构建发送给 LLM 的「小说 → 分镜 JSON」提示词"""

from typing import List, Optional


class PromptTemplateManager:
    """统一管理分镜转换相关 Prompt 的构建，便于后续扩展（配音/绘图 Prompt 等）"""

    EMOTIONS = ["平静", "开心", "愤怒", "悲伤", "紧张", "疑惑", "嘲讽", "惊喜"]
    CAMERA_ANGLES = ["平视全景", "平视中景", "特写", "俯拍全景", "俯拍特写", "低机位仰拍", "过肩中景", "跟拍"]

    SYSTEM_PROMPT = """你是一位精通微短剧与漫画分镜的资深编剧。你的任务是把用户提供的小说文本，拆解成可直接用于 AI 视频漫剧制作的标准分镜 JSON。
要求：
1. 严格输出 JSON，不要输出任何解释、markdown 代码块围栏（``` 或 ```json）之外的文字。
2. 镜头数量：根据文本长度与目标镜头数确定，每个镜头必须有独立的 Scene 与清晰画面。
3. 每个镜头最多 2-3 句对白，旁白（narration）用于交代转折/氛围，可缺省为 null。
4. emotion 必须从以下枚举中选择一个：{emotions}
5. camera_angle 必须从以下枚举中选择一个：{camera_angles}
6. character_prompts 中每个出场角色写一条完整提示词（外貌+服装+表情+动作），角色名必须与对白 speaker 一致，保证多镜头间角色一致性。
7. bg_prompt 用描述性语言写清场景、构图、光影、氛围，方便文生图模型直接使用。
8. 时长：普通镜头 4-6 秒，情绪高潮/爆点镜头 3-4 秒。"""

    USER_PROMPT = """作品标题（没有则根据内容拟一个）：{title}
目标画风：{style}
目标镜头数：{target_shots}

以下是小说原文：
\"\"\"
{novel}
\"\"\"

请输出符合上述要求的分镜 JSON。"""

    def build_chat_messages(self, novel: str, title: str = "", style: str = "", target_shots: Optional[int] = None) -> List[dict]:
        """构建 OpenAI 兼容的 chat messages"""
        resolved_title = title or "未命名漫剧"
        resolved_style = style or "国漫水彩"
        resolved_shots = target_shots or self._auto_shot_count(novel)
        system = self.SYSTEM_PROMPT.format(
            emotions="/".join(self.EMOTIONS),
            camera_angles="/".join(self.CAMERA_ANGLES),
        )
        user = self.USER_PROMPT.format(
            title=resolved_title,
            style=resolved_style,
            target_shots=resolved_shots,
            novel=novel,
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def _auto_shot_count(novel: str) -> int:
        """按文本长度估算镜头数：每 250 字 ≈ 1 镜，区间 [6, 18]"""
        length = len(novel or "")
        count = max(6, min(18, round(length / 250)))
        return count
