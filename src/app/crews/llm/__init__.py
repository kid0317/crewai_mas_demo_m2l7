"""LLM 模型参数与 Provider 配置。支持阿里云通义千问等。"""

from app.core.config import get_settings
from app.crews.llm.aliyun_llm import AliyunLLM

__all__ = ["AliyunLLM", "get_llm"]


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    **kwargs: object,
) -> AliyunLLM:
    """
    根据配置返回 LLM 实例。当前仅支持 aliyun。

    Args:
        provider: 不传则用 APP_LLM_PROVIDER
        model: 不传则用 APP_LLM_MODEL
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
        )
    raise ValueError(f"不支持的 LLM provider: {provider}，当前支持: aliyun")
