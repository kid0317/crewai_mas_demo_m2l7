"""小红书爆款笔记撰写报告 API。

POST /api/v1/xhs/notes/report
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import get_request_id, require_api_key
from app.observability.logging import get_logger
from app.schemas.common import ApiResponse
from app.schemas.xhs_note import XhsNoteReportResponse
from app.services.xhs_note_service import generate_xhs_note_report


router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/notes/report",
    response_model=ApiResponse[XhsNoteReportResponse],
    summary="生成小红书爆款笔记撰写报告",
    description=(
        "通过 form-data 上传创作意图与多张图片，"
        "由多 Agent 协同完成视觉分析、图片编辑方案、内容策略、文案撰写与 SEO 优化，"
        "最终返回结构化的小红书笔记撰写报告。"
    ),
    status_code=status.HTTP_200_OK,
)
async def create_xhs_note_report(
    idea_text: str = Form(..., description="笔记创作意图 / 思路"),
    images: List[UploadFile] = File(
        ..., description="多张图片，同一字段名 images 下上传多文件"
    ),
    request_id: str = Depends(get_request_id),
    _api_key: str = Depends(require_api_key),
) -> ApiResponse[XhsNoteReportResponse]:
    """生成小红书爆款笔记撰写报告。"""
    try:
        final_report, error = await generate_xhs_note_report(
            idea_text=idea_text,
            files=images,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("xhs_note_api_failed", error=str(exc), request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"小红书笔记生成异常: {exc}",
        ) from exc

    if error or final_report is None:
        return ApiResponse(
            code=1,
            message=f"小红书笔记生成失败: {error}",
            data=None,
            request_id=request_id,
        )

    response_payload = XhsNoteReportResponse(report=final_report)
    return ApiResponse(
        code=0,
        message="ok",
        data=response_payload,
        request_id=request_id,
    )

