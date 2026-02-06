"""LLM 模型参数与 Provider 配置。支持阿里云通义千问等。"""

from app.core.config import get_settings
from app.crews.llm.aliyun_llm import AliyunLLM

__all__ = ["AliyunLLM", "get_llm"]


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    image_model: str | None = None, # 专门的多模态模型；优先使用显式入参，其次尝试从配置读取，最后使用默认值。
    **kwargs: object,
) -> AliyunLLM:
    """
    根据配置返回 LLM 实例。当前仅支持 aliyun。

    Args:
        provider: 不传则用 APP_LLM_PROVIDER
        model: 不传则用 APP_LLM_MODEL
        image_model: 专门的多模态模型；优先使用显式入参，其次尝试从配置读取，最后使用默认值。  qwen3-vl-plus
        **kwargs: 透传给 AliyunLLM（如 api_key、region、temperature、timeout、retry_count）

    Returns:
        AliyunLLM 实例（其他 provider 可在此扩展）
    """
    settings = get_settings()
    provider = (provider or settings.llm_provider).lower()
    if provider == "aliyun":
        return AliyunLLM(
            model=model or settings.llm_model,
            api_key=kwargs.get("api_key"),
            region=kwargs.get("region") or settings.llm_region,
            temperature=kwargs.get("temperature"),
            timeout=kwargs.get("timeout"),
            retry_count=kwargs.get("retry_count"),
            image_model=image_model or settings.llm_image_model,
        )
    raise ValueError(f"不支持的 LLM provider: {provider}，当前支持: aliyun")
