"""小红书爆款笔记项目的领域服务。

负责：
- 解析上传的图片文件并落盘到临时目录；
- 组装领域请求模型 XhsNoteIdeaRequest；
- 调用 Crew Flow 执行多 Agent 编排；
- 返回最终的 XhsNoteFinalReport。
"""

from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.image_utils import compress_image_to_standard
from app.crews.xhs_note.flows import run_xhs_note_flow
from app.observability.logging import get_logger
from app.schemas.xhs_note import (
    XhsImageInput,
    XhsNoteIdeaRequest,
)


logger = get_logger(__name__)


def _sanitize_filename(filename: str, fallback_name: str, max_length: int = 255) -> str:
    """对上传文件名做安全处理，防止路径穿越和特殊字符导致的问题。

    Args:
        filename: 原始文件名（可能为空）
        fallback_name: 当原始文件名为空时使用的后备名称（如 img_0.jpg）
        max_length: 允许的最大文件名长度
    """
    name = filename or fallback_name
    # 去掉路径分隔符，避免路径穿越
    name = name.replace("/", "_").replace("\\", "_")
    # 过滤常见危险字符
    name = re.sub(r'[<>:"|?*]', "_", name)
    name = name.strip() or fallback_name

    if len(name) <= max_length:
        return name

    # 超长时截断主文件名，保留扩展名
    path = Path(name)
    stem, suffix = path.stem, path.suffix
    remain = max_length - len(suffix)
    if remain <= 0:
        # 极端情况：连扩展名都放不下，直接截断
        return (stem + suffix)[:max_length]
    return stem[:remain] + suffix


async def _save_uploaded_images(
    files: List[UploadFile],
    base_dir: Path,
    max_size: int,
    quality: int,
) -> List[XhsImageInput]:
    """将上传的图片保存到临时目录，按标准分辨率统一压缩后返回 XhsImageInput 列表。"""
    # 存放所有图片元信息（供后续多模态 Agent 使用）
    images: List[XhsImageInput] = []
    # 确保目标临时目录存在（不存在则递归创建）
    base_dir.mkdir(parents=True, exist_ok=True)

    for idx, f in enumerate(files):
        # 使用递增序号作为 image_id，保证在本次请求中唯一
        image_id = f"img_{idx}"
        # 文件名优先使用上传名，缺失时退化为 image_id
        raw_name = f.filename
        fallback_name = f"{image_id}.jpg"
        safe_name = _sanitize_filename(raw_name or "", fallback_name=fallback_name)
        target_path = base_dir / safe_name
        
        # 使用异步方式读取文件内容，确保文件句柄正确关闭
        content = await f.read()
        # 直接将二进制内容落盘到临时目录
        target_path.write_bytes(content)

        # 默认认为压缩前后的路径相同；压缩成功后会被覆盖
        local_path = target_path
        try:
            local_path = compress_image_to_standard(
                target_path,
                max_size=max_size,
                quality=quality,
            )
        except Exception as exc:  # noqa: BLE001
            # 压缩失败只打日志，不中断整个请求，继续使用原图路径
            logger.warning(
                "xhs_image_compress_skipped",
                path=str(target_path),
                error=str(exc),
            )

        images.append(
            XhsImageInput(
                image_id=image_id,
                file_name=safe_name,
                local_path=str(local_path),
            )
        )

    return images


def _cleanup_temp_directory(base_dir: Path) -> None:
    """清理临时目录及其所有内容。
    
    Args:
        base_dir: 要清理的目录路径
    """
    try:
        # 仅当目录真实存在且为文件夹时才尝试删除
        if base_dir.exists() and base_dir.is_dir():
            shutil.rmtree(base_dir)
            logger.debug("temp_directory_cleaned", base_dir=str(base_dir))
    except Exception as exc:  # noqa: BLE001
        # 清理失败不应该影响主流程，只记录警告
        logger.warning(
            "temp_directory_cleanup_failed",
            base_dir=str(base_dir),
            error=str(exc),
        )


async def generate_xhs_note_report(
    idea_text: str,
    files: List[UploadFile],
) -> Tuple[Optional[str], str]:
    """对外主入口：执行小红书爆款笔记生成流程。

    Returns:
        (final_report, error_message)
    
    注意：无论成功还是失败，都会自动清理临时文件目录。
    """
    # 1. 基础校验：至少需要一张图片，否则无需进入后续多模态处理
    if not files:
        return None, "至少需要上传一张图片"

    # 2. 从全局配置中读取运行所需参数（输出目录、图片压缩规格等）
    settings = get_settings()

    # 2.1 校验图片数量上限，避免单次请求过大
    if len(files) > settings.xhs_max_images:
        return None, f"最多支持上传 {settings.xhs_max_images} 张图片"

    # 3. 每次调用生成一个简短 run_id，用于区分不同请求和日志追踪
    run_id = uuid.uuid4().hex[:8]
    # 4. 构造本次调用专属的临时工作目录：<output_root>/xhs_note/<run_id>
    base_dir = Path(settings.data_output_dir).resolve() / "xhs_note" / run_id

    # 记录服务入口日志，便于定位线上问题（截断 idea_text 避免日志过长）
    logger.info(
        "xhs_note_service_start",
        idea_text=idea_text[:100],
        image_count=len(files),
        run_id=run_id,
        base_dir=str(base_dir),
    )

    try:
        # 5. 保存并压缩上传图片，统一输出为 XhsImageInput 列表
        images = await _save_uploaded_images(
            files,
            base_dir,
            max_size=settings.xhs_image_max_size,
            quality=settings.xhs_image_quality,
        )
        # 7. 组装领域请求模型，作为 Crew Flow 的输入
        idea_request = XhsNoteIdeaRequest(
            idea_text=idea_text,
            images=images,
        )

        # run_xhs_note_flow 现在是异步函数，需要使用 await
        # 8. 调用多 Agent 编排流程，执行完整的小红书爆款笔记生成链路
        final_report, error = await run_xhs_note_flow(idea_request)
        
        # 任务完成后才清理临时文件目录
        # 注意：必须在CrewAI流程完全结束后清理，因为多模态Agent需要读取图片文件
        _cleanup_temp_directory(base_dir)
        
        if error:
            logger.warning("xhs_note_service_failed", error=error, run_id=run_id)
        else:
            logger.info("xhs_note_service_success", run_id=run_id)
        return final_report, error
    except Exception as exc:  # noqa: BLE001
        # 发生异常时也要清理临时文件，避免临时目录不断堆积
        _cleanup_temp_directory(base_dir)
        logger.exception("xhs_note_service_exception", error=str(exc), run_id=run_id)
        return None, f"服务异常: {str(exc)}"

