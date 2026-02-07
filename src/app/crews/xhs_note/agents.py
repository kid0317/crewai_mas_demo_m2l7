"""小红书爆款笔记项目的 Agent 定义。

Agent 的角色文案（role/goal/backstory 等）配置在 `app/crews/config/agents.yaml` 中，
本模块只负责两类“结构化信息”：
- 绑定使用的 LLM（如 qwen3-max-2026-01-23、qwen3-vl-plus）
- 绑定 tools（如 IntermediateTool）与 output_pydantic、多模态标记等

即：**除了 llm 和 tools（以及结构化输出模型、多模态开关），其余全部走 config。**
"""

from __future__ import annotations

from pathlib import Path

import yaml
from crewai import Agent

from app.crews.llm import get_llm
from app.crews.tools import IntermediateTool, AddImageToolLocal
from app.schemas.xhs_note import (
    XhsContentStrategyBrief,
    XhsCopywritingOutput,
    XhsImageEditPlan,
    XhsImageVisualAnalysis,
    XhsSEOOptimizedNote,
)


_INTERMEDIATE_TOOLS = [IntermediateTool()]

_CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


def _load_agents_config() -> dict:
    """从 agents.yaml 读取全部 Agent 文案与通用配置。"""
    try:
        with (_CONFIG_DIR / "agents.yaml").open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}


_AGENTS_CFG = _load_agents_config()


def _agent_cfg(name: str) -> dict:
    return _AGENTS_CFG.get(name, {}) if isinstance(_AGENTS_CFG, dict) else {}


# 多模态视觉分析 Agent：除 llm/tools/multimodal 外全部走 config
def get_xhs_visual_analyst() -> Agent:
    """每次调用创建一个新的视觉分析 Agent 实例。"""
    cfg_visual = _agent_cfg("xhs_visual_analyst")
    return Agent(
        config=cfg_visual,
        multimodal=True,
        llm=get_llm(image_model="qwen3-vl-plus", model="qwen3-max-2026-01-23"),
        tools=[AddImageToolLocal()],
    )


# 多模态图片编辑 / P 图方案 Agent
def get_xhs_image_editor() -> Agent:
    """每次调用创建一个新的图片编辑 Agent 实例。"""
    cfg_editor = _agent_cfg("xhs_image_editor")
    return Agent(
        config=cfg_editor,
        multimodal=True,
        llm=get_llm(image_model="qwen3-vl-plus", model="qwen3-max-2026-01-23"),
        tools=[AddImageToolLocal()],
    )


def get_xhs_growth_strategist() -> Agent:
    """每次调用创建一个新的增长策略 Agent 实例。"""
    cfg_growth = _agent_cfg("xhs_growth_strategist")
    return Agent(
        config=cfg_growth,
        tools=_INTERMEDIATE_TOOLS,
        llm=get_llm(model="qwen3-max-2026-01-23"),
    )


def get_xhs_content_writer() -> Agent:
    """每次调用创建一个新的内容撰写 Agent 实例。"""
    cfg_writer = _agent_cfg("xhs_content_writer")
    return Agent(
        config=cfg_writer,
        tools=_INTERMEDIATE_TOOLS,
        llm=get_llm(model="qwen3-max-2026-01-23"),
    )


def get_xhs_seo_expert() -> Agent:
    """每次调用创建一个新的 SEO 优化 Agent 实例。"""
    cfg_seo = _agent_cfg("xhs_seo_expert")
    return Agent(
        config=cfg_seo,
        tools=_INTERMEDIATE_TOOLS,
        llm=get_llm(model="qwen3-max-2026-01-23"),
    )

