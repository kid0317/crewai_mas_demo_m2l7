"""小红书爆款笔记集成测试：多图 + 表单上传."""

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

LIVE_URL = os.environ.get("LIVE_URL", "").strip()


def _make_client() -> AsyncClient:
    if LIVE_URL:
        return AsyncClient(base_url=LIVE_URL)
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
    )


@pytest.mark.asyncio
async def test_xhs_note_report_with_images() -> None:
    """使用 4 张测试图片和固定 idea_text 调用 /api/v1/xhs/notes/report。"""
    tests_dir = Path(__file__).resolve().parent
    image_files = [
        tests_dir / "20260202161329_150_6.jpg",
        tests_dir / "20260202161331_151_6.jpg",
        tests_dir / "20260202161332_152_6.jpg",
        tests_dir / "20260202161333_153_6.jpg",
    ]

    for p in image_files:
        assert p.is_file(), f"测试图片不存在: {p}"

    idea_text = "我想分享最近开始用地中海饮食减脂"

    files = [
        ("images", (p.name, p.open("rb"), "image/jpeg")) for p in image_files
    ]

    async with _make_client() as client:
        resp = await client.post(
            "/api/v1/xhs/notes/report",
            data={
                "idea_text": idea_text,
            },
            files=files,
            headers={"X-API-Key": os.environ.get("APP_TEST_API_KEY", "test-key")},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()

    # 顶层统一响应契约
    assert body.get("code") == 0
    assert body.get("message") == "ok"
    assert "request_id" in body
    assert body.get("data") is not None

    data = body["data"]
    assert "report" in data
    report = data["report"]

    # 报告关键字段检查
    assert report.get("idea_text") == idea_text
    assert "strategy_brief" in report
    assert "raw_copywriting" in report
    assert "seo_optimized_note" in report
    assert "images" in report

    images = report["images"]
    assert isinstance(images, list)
    # 至少包含上传的 4 张图片信息
    assert len(images) >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

