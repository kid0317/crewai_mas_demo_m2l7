"""全局测试 fixtures：共享 mock 对象、测试数据工厂等。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from app.schemas.xhs_note import (
    XhsContentStrategyBrief,
    XhsCopywritingOutput,
    XhsImageEditBatchReport,
    XhsImageEditPlan,
    XhsImageInput,
    XhsImageVisualAnalysis,
    XhsNoteIdeaRequest,
    XhsSEOOptimizedNote,
    XhsVisualBatchReport,
)


# ---------------------------------------------------------------------------
# 测试数据工厂
# ---------------------------------------------------------------------------

def make_image_input(idx: int = 0) -> XhsImageInput:
    return XhsImageInput(
        image_id=f"img_{idx}",
        file_name=f"test_{idx}.jpg",
        local_path=f"/tmp/test_{idx}.jpg",
    )


def make_visual_analysis(idx: int = 0) -> XhsImageVisualAnalysis:
    return XhsImageVisualAnalysis(
        image_id=f"img_{idx}",
        file_name=f"test_{idx}.jpg",
        subject_description="一盘色彩丰富的地中海沙拉",
        atmosphere_vibe="健康、清新、阳光",
        visual_details=["新鲜蔬菜", "橄榄油光泽", "木质餐盘纹理"],
        image_quality_score="8分，构图清晰光线充足",
        highlight_feature="色彩对比鲜明的蔬菜组合",
    )


def make_edit_plan(idx: int = 0) -> XhsImageEditPlan:
    return XhsImageEditPlan(
        image_id=f"img_{idx}",
        file_name=f"test_{idx}.jpg",
        overall_edit_strategy="提升整体明亮度，突出食物色彩",
        crop_suggestion="保持原构图，适当收紧边缘",
        light_color_adjustment="略微提升亮度和饱和度",
        filter_suggestion="清新日系滤镜",
        text_overlay_suggestion="不需要加文字",
        beauty_adjustment_suggestion="无人像，不需要美颜",
        is_recommended_as_cover=True,
        risk_and_pitfall_notes="避免过度饱和导致食物失真",
    )


def make_idea_request(image_count: int = 2) -> XhsNoteIdeaRequest:
    return XhsNoteIdeaRequest(
        idea_text="我想分享最近开始用地中海饮食减脂",
        images=[make_image_input(i) for i in range(image_count)],
    )


def make_strategy_brief() -> XhsContentStrategyBrief:
    return XhsContentStrategyBrief(
        input_evaluation="用户有清晰的减脂主题，图片素材丰富",
        target_audience_persona="25-35岁都市白领女性",
        core_pain_point="减脂难以坚持，饮食选择困难",
        suggested_title="🥗 地中海饮食一周瘦3斤，懒人也能坚持的减脂餐！",
        content_outline=["场景引入", "饮食分享", "效果展示", "互动引导"],
        engagement_strategy="设置评论区打卡挑战",
        retention_strategy="提供可收藏的一周食谱清单",
        seo_keywords=["地中海饮食", "减脂餐", "健康饮食"],
    )


def make_copywriting() -> XhsCopywritingOutput:
    return XhsCopywritingOutput(
        title="🥗 地中海饮食一周瘦3斤！",
        content="最近开始尝试地中海饮食...",
        picture_order=["img_0", "img_1"],
        highlight_hooks=["一周瘦3斤", "懒人也能坚持"],
    )


def make_seo_note() -> XhsSEOOptimizedNote:
    return XhsSEOOptimizedNote(
        optimization_summary="优化了标题和标签的关键词覆盖",
        optimized_title="🥗 地中海饮食减脂｜一周瘦3斤的懒人食谱",
        optimized_content="最近开始尝试地中海饮食减脂...",
        optimized_picture_order=["img_0", "img_1"],
        tags=["地中海饮食", "减脂餐", "健康饮食", "减肥食谱", "懒人减脂"],
    )


def make_visual_batch(image_count: int = 2) -> XhsVisualBatchReport:
    return XhsVisualBatchReport(
        user_raw_intent="我想分享最近开始用地中海饮食减脂",
        images_visual=[make_visual_analysis(i) for i in range(image_count)],
        summary="整体图片色彩丰富，适合美食类笔记",
    )


def make_edit_batch(image_count: int = 2) -> XhsImageEditBatchReport:
    return XhsImageEditBatchReport(
        images_edit_plan=[make_edit_plan(i) for i in range(image_count)],
        summary="统一提升明亮度和饱和度，保持清新风格",
    )


# ---------------------------------------------------------------------------
# Mock CrewAI 结果
# ---------------------------------------------------------------------------

class MockTaskOutput:
    """模拟 CrewAI TaskOutput 对象。"""
    def __init__(self, pydantic: Any = None, raw: str = ""):
        self.pydantic = pydantic
        self.raw = raw


class MockCrewResult:
    """模拟 CrewAI akickoff 返回的结果。"""
    def __init__(self, tasks_output: list | None = None):
        self.tasks_output = tasks_output or []


# ---------------------------------------------------------------------------
# Settings fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_settings():
    """返回一个不依赖 .env 的 Settings mock。"""
    from app.core.config import Settings
    return Settings(
        llm_api_key="test-api-key-12345",
        baidu_api_key="test-baidu-key",
        api_keys="test-key-1,test-key-2",
        env="development",
    )
