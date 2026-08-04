"""小说 → 分镜脚本 转换接口"""

from fastapi import APIRouter, HTTPException

from app.schemas.script import ScriptConvertRequest, ShotScript
from app.services.script_generator import ScriptGeneratorService

router = APIRouter(prefix="/script-generator", tags=["小说转分镜"])

service = ScriptGeneratorService()


@router.get("/mock", summary="获取示例分镜脚本（前端UI对接用）")
def get_mock_script(title: str = "都市赘婿·三年之约") -> dict:
    """返回标准分镜 JSON，前端可直接用于 UI 对接与样式开发"""
    return service.generate_script_mock(title=title)


@router.post("/convert", summary="小说转分镜脚本（LLM可用走真实转换，否则返回mock）")
def convert_script(req: ScriptConvertRequest) -> dict:
    try:
        return service.generate_script(
            novel=req.novel,
            title=req.title or "",
            style=req.style or "",
            target_shots=req.target_shots,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分镜转换失败: {e}")
