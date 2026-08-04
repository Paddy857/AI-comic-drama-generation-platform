"""OpenAI 兼容的 LLM 客户端（标准库实现，零第三方依赖）。

兼容国内主流大模型（DeepSeek/通义千问/Kimi/智谱 等均提供 OpenAI 兼容接口）。
未配置 API Key 时 is_available() 返回 False，由上层服务降级为 mock。
"""

import json
import urllib.request
from typing import List, Optional

from app.core.config import settings


class LLMClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120,
    ):
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.timeout = timeout

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat_json(self, messages: List[dict], temperature: float = 0.7) -> str:
        """发送 chat 请求，返回模型输出的原始文本（期望是 JSON 字符串）"""
        if not self.is_available():
            raise RuntimeError("LLM API Key 未配置")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
