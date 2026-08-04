"""ScriptGeneratorService：小说 → 分镜脚本 转换服务。

- generate_script_mock()：返回标准分镜 JSON，供前端直接进行 UI 对接。
- generate_script()：配置了 LLM API Key 时调用真实 LLM 转换；否则降级返回 mock。
"""

import json
import re
from typing import List, Optional

from app.schemas.script import Dialogue, Scene, Shot, ShotScript
from app.services.llm_client import LLMClient
from app.services.prompt_templates import PromptTemplateManager


class ScriptGeneratorService:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.prompts = PromptTemplateManager()

    # ────────────────────────── Mock ──────────────────────────

    def generate_script_mock(self, title: str = "都市赘婿·三年之约") -> dict:
        """返回一段标准分镜 JSON（示例：6 镜都市赘婿），供前端 UI 对接"""
        mock = ShotScript(
            title=title,
            style="国漫水彩",
            total_shots=6,
            shots=[
                Shot(
                    shot_id="S001",
                    scene=Scene(
                        scene_id="S001",
                        location="豪华酒店宴会厅",
                        time_of_day="夜",
                        description="觥筹交错，宾客云集，女主父亲正当众羞辱赘婿男主",
                        bg_prompt="金碧辉煌的五星酒店宴会厅，水晶吊灯，长桌酒席，觥筹交错，暖黄灯光，宾客们窃窃私语，微醺喧闹的氛围，国漫水彩风格，细腻光影",
                        character_prompts=[
                            "萧战，25岁都市青年，面容清秀隐忍，身着廉价黑色西装，站在宴会厅中央，低头紧握双拳，神情压抑",
                            "苏沐雪，23岁豪门千金，气质清冷，身着白色晚礼服，站在萧战身旁，神色复杂带着心疼",
                        ],
                        camera_angle="平视全景",
                    ),
                    dialogues=[
                        Dialogue(speaker="苏父", line="萧战！三年了，你一个上门女婿，吃我苏家的、用我苏家的，今天也该滚了！", emotion="愤怒"),
                        Dialogue(speaker="苏沐雪", line="爸！你少说两句……", emotion="紧张"),
                    ],
                    narration="那一夜，全场的目光都钉在这个被羞辱了整整三年的男人身上。",
                    duration_sec=6.0,
                    mood="冲突升级",
                ),
                Shot(
                    shot_id="S002",
                    scene=Scene(
                        scene_id="S002",
                        location="豪华酒店宴会厅",
                        time_of_day="夜",
                        description="男主猛然抬头，眼神骤变，宾客们噤声",
                        bg_prompt="宴会厅中心，宾客围成一圈，气氛骤然凝固，冷白顶光打在男主脸上，周围宾客模糊虚化，国漫水彩风格，强明暗对比",
                        character_prompts=[
                            "萧战，抬头直视前方，眼神由隐忍骤变为锐利如刀，嘴角勾起一抹冷笑，廉价西装被气场撑起",
                        ],
                        camera_angle="特写",
                    ),
                    dialogues=[],
                    narration=None,
                    duration_sec=3.5,
                    mood="反转爆发",
                ),
                Shot(
                    shot_id="S003",
                    scene=Scene(
                        scene_id="S003",
                        location="豪华酒店宴会厅",
                        time_of_day="夜",
                        description="男主掷地有声说出金句，全场震惊",
                        bg_prompt="宴会厅全景，宾客们瞪大眼睛，酒杯悬在半空，定格瞬间，顶光如聚光灯般打在男主身上，国漫水彩风格，画面张力十足",
                        character_prompts=[
                            "萧战，昂首挺胸，单手解开西装扣子，神情冷峻而自信，说出宣言",
                        ],
                        camera_angle="低机位仰拍",
                    ),
                    dialogues=[
                        Dialogue(speaker="萧战", line="三年之期已满，龙神归位！从今往后，你苏家，高攀不起！", emotion="嘲讽"),
                    ],
                    narration="忍了三年，他等的就是这一天。",
                    duration_sec=5.0,
                    mood="爽感爆发",
                ),
                Shot(
                    shot_id="S004",
                    scene=Scene(
                        scene_id="S004",
                        location="宴会厅门口",
                        time_of_day="夜",
                        description="门外数十名黑衣保镖列队跪迎，场面震撼",
                        bg_prompt="宴会厅大门敞开，门外夜色中数十名黑衣保镖整齐单膝跪地，红毯铺路，车灯明灭，肃杀而震撼，国漫水彩风格，大气构图",
                        character_prompts=[
                            "萧战，大步走向门口，身形挺拔，气场全开，夜色灯光勾勒出剪影",
                        ],
                        camera_angle="平视全景",
                    ),
                    dialogues=[
                        Dialogue(speaker="黑衣首领", line="恭迎龙神大人！属下接驾来迟！", emotion="平静"),
                    ],
                    narration="门外跪下的，是整个城市的黑暗秩序。",
                    duration_sec=5.0,
                    mood="震撼",
                ),
                Shot(
                    shot_id="S005",
                    scene=Scene(
                        scene_id="S005",
                        location="豪华酒店宴会厅",
                        time_of_day="夜",
                        description="苏父瘫坐在地，苏沐雪追出，两人对视",
                        bg_prompt="宴会厅内，苏父瘫坐在地面如死灰，宾客散开，苏沐雪站在门口回望萧战背影，一明一暗的光影分隔两人，国漫水彩风格，情绪浓度高",
                        character_prompts=[
                            "苏父，瘫坐在地，脸色惨白，额头冷汗，双眼失神",
                            "苏沐雪，白裙被风吹动，望着门口萧战的背影，眼眶微红，欲言又止",
                        ],
                        camera_angle="过肩中景",
                    ),
                    dialogues=[
                        Dialogue(speaker="苏沐雪", line="萧战……你还会回来吗？", emotion="悲伤"),
                    ],
                    narration=None,
                    duration_sec=5.0,
                    mood="怅然",
                ),
                Shot(
                    shot_id="S006",
                    scene=Scene(
                        scene_id="S006",
                        location="城市夜空",
                        time_of_day="夜",
                        description="男主坐进顶级豪车，俯瞰城市，故事钩子收尾",
                        bg_prompt="城市夜景航拍，霓虹灯火如星河，黑色顶级豪车行驶在跨江大桥上，车窗内男主侧脸冷峻，国漫水彩风格，电影感收尾构图",
                        character_prompts=[
                            "萧战，坐在豪车后座，侧脸望向窗外灯火，眼神深邃，嘴角微扬",
                        ],
                        camera_angle="俯拍全景",
                    ),
                    dialogues=[],
                    narration="三年隐忍，一朝扬名。可这座城市，才刚刚开始记得他的名字。",
                    duration_sec=4.0,
                    mood="悬念钩子",
                ),
            ],
        )
        return mock.model_dump()

    # ────────────────────────── 真实 LLM 转换 ──────────────────────────

    def generate_script(
        self,
        novel: str,
        title: str = "",
        style: str = "",
        target_shots: Optional[int] = None,
    ) -> dict:
        """小说 → 分镜。LLM 可用时走真实转换；否则降级为 mock（meta.source 标注来源）"""
        if not novel or not novel.strip():
            raise ValueError("小说内容不能为空")

        if self.llm.is_available():
            messages = self.prompts.build_chat_messages(
                novel=novel,
                title=title,
                style=style,
                target_shots=target_shots,
            )
            raw = self.llm.chat_json(messages)
            script = self.parse_llm_response(raw)
            result = script.model_dump()
            result["meta"] = {"source": "llm", "model": self.llm.model}
            return result

        mock = self.generate_script_mock(title=title or "未命名漫剧")
        mock["meta"] = {"source": "mock", "reason": "LLM_API_KEY 未配置，返回示例分镜"}
        return mock

    # ────────────────────────── 容错解析 ──────────────────────────

    @staticmethod
    def parse_llm_response(raw_text: str) -> ShotScript:
        """解析 LLM 输出：去除 markdown 围栏 → 提取 JSON → Pydantic 校验"""
        text = raw_text.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        else:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end > start:
                text = text[start : end + 1]
        data = json.loads(text)
        return ShotScript.model_validate(data)
