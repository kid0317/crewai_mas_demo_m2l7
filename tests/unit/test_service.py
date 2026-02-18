"""Service 层（xhs_note_service.py）的单元测试。"""

from __future__ import annotations

import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from app.services.xhs_note_service import (
    _sanitize_filename,
    _save_uploaded_images,
    _cleanup_temp_directory,
    generate_xhs_note_report,
)


# ---------------------------------------------------------------------------
# _sanitize_filename
# ---------------------------------------------------------------------------


class TestSanitizeFilename:
    def test_normal_name(self):
        assert _sanitize_filename("photo.jpg", "fallback.jpg") == "photo.jpg"

    def test_empty_name(self):
        assert _sanitize_filename("", "fallback.jpg") == "fallback.jpg"

    def test_none_name(self):
        assert _sanitize_filename(None, "fallback.jpg") == "fallback.jpg"

    def test_path_traversal(self):
        result = _sanitize_filename("../../etc/passwd", "fallback.jpg")
        assert "/" not in result
        assert "\\" not in result

    def test_special_chars(self):
        result = _sanitize_filename('file<>:"|?*.jpg', "fallback.jpg")
        assert "<" not in result
        assert ">" not in result

    def test_long_name(self):
        long_name = "a" * 300 + ".jpg"
        result = _sanitize_filename(long_name, "fallback.jpg", max_length=255)
        assert len(result) <= 255
        assert result.endswith(".jpg")

    def test_whitespace_only(self):
        result = _sanitize_filename("   ", "fallback.jpg")
        assert result == "fallback.jpg"


# ---------------------------------------------------------------------------
# _cleanup_temp_directory
# ---------------------------------------------------------------------------


class TestCleanupTempDirectory:
    def test_cleanup_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "subdir"
            p.mkdir()
            (p / "file.txt").write_text("data")
            _cleanup_temp_directory(p)
            assert not p.exists()

    def test_cleanup_nonexistent(self):
        # Should not raise
        _cleanup_temp_directory(Path("/nonexistent/path"))


# ---------------------------------------------------------------------------
# _save_uploaded_images
# ---------------------------------------------------------------------------


def _make_upload_file(filename: str = "test.jpg", content: bytes = b"\xff\xd8\xff"):
    """创建模拟 UploadFile 对象。"""
    f = MagicMock()
    f.filename = filename
    f.read = AsyncMock(return_value=content)
    return f


class TestSaveUploadedImages:
    @pytest.mark.asyncio
    async def test_basic_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "test_run"
            files = [_make_upload_file("image.jpg")]

            with patch("app.services.xhs_note_service.compress_image_to_standard") as mock_compress:
                mock_compress.return_value = base_dir / "image.jpg"
                images = await _save_uploaded_images(files, base_dir, max_size=1024, quality=85)

            assert len(images) == 1
            assert images[0].image_id == "img_0"
            assert images[0].file_name == "image.jpg"

    @pytest.mark.asyncio
    async def test_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "test_run"
            files = [
                _make_upload_file("a.jpg"),
                _make_upload_file("b.jpg"),
                _make_upload_file("c.jpg"),
            ]

            with patch("app.services.xhs_note_service.compress_image_to_standard") as mock_compress:
                mock_compress.side_effect = lambda p, **kw: p
                images = await _save_uploaded_images(files, base_dir, max_size=0, quality=85)

            assert len(images) == 3
            assert images[2].image_id == "img_2"

    @pytest.mark.asyncio
    async def test_compress_failure_uses_original(self):
        """压缩失败时应降级使用原图。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir) / "test_run"
            files = [_make_upload_file("fail.jpg")]

            with patch("app.services.xhs_note_service.compress_image_to_standard") as mock_compress:
                mock_compress.side_effect = ValueError("压缩失败")
                images = await _save_uploaded_images(files, base_dir, max_size=1024, quality=85)

            assert len(images) == 1
            # 即使压缩失败，也应返回原始路径
            assert "fail.jpg" in images[0].file_name


# ---------------------------------------------------------------------------
# generate_xhs_note_report
# ---------------------------------------------------------------------------


class TestGenerateXhsNoteReport:
    @pytest.mark.asyncio
    async def test_no_files(self):
        report, error = await generate_xhs_note_report("test", [])
        assert report is None
        assert "至少" in error

    @pytest.mark.asyncio
    async def test_too_many_files(self):
        with patch("app.services.xhs_note_service.get_settings") as mock_settings:
            s = MagicMock()
            s.xhs_max_images = 2
            s.data_output_dir = "/tmp"
            s.xhs_image_max_size = 1024
            s.xhs_image_quality = 85
            mock_settings.return_value = s

            files = [_make_upload_file(f"img_{i}.jpg") for i in range(5)]
            report, error = await generate_xhs_note_report("test", files)
            assert report is None
            assert "最多" in error

    @pytest.mark.asyncio
    @patch("app.services.xhs_note_service.run_xhs_note_flow")
    @patch("app.services.xhs_note_service._save_uploaded_images")
    @patch("app.services.xhs_note_service._cleanup_temp_directory")
    async def test_success(self, mock_cleanup, mock_save, mock_flow):
        from tests.conftest import make_image_input
        mock_save.return_value = [make_image_input(0)]
        mock_flow.return_value = ("最终报告文本", "")

        with patch("app.services.xhs_note_service.get_settings") as mock_settings:
            s = MagicMock()
            s.xhs_max_images = 20
            s.data_output_dir = "/tmp"
            s.xhs_image_max_size = 1024
            s.xhs_image_quality = 85
            mock_settings.return_value = s

            files = [_make_upload_file()]
            report, error = await generate_xhs_note_report("测试意图", files)

        assert report == "最终报告文本"
        assert error == ""
        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.xhs_note_service.run_xhs_note_flow")
    @patch("app.services.xhs_note_service._save_uploaded_images")
    @patch("app.services.xhs_note_service._cleanup_temp_directory")
    async def test_flow_error(self, mock_cleanup, mock_save, mock_flow):
        from tests.conftest import make_image_input
        mock_save.return_value = [make_image_input(0)]
        mock_flow.return_value = (None, "LLM 超时")

        with patch("app.services.xhs_note_service.get_settings") as mock_settings:
            s = MagicMock()
            s.xhs_max_images = 20
            s.data_output_dir = "/tmp"
            s.xhs_image_max_size = 1024
            s.xhs_image_quality = 85
            mock_settings.return_value = s

            files = [_make_upload_file()]
            report, error = await generate_xhs_note_report("test", files)

        assert report is None
        assert "超时" in error
        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.xhs_note_service._save_uploaded_images")
    @patch("app.services.xhs_note_service._cleanup_temp_directory")
    async def test_exception_cleanup(self, mock_cleanup, mock_save):
        """即使发生异常，也应清理临时目录。"""
        mock_save.side_effect = RuntimeError("磁盘满了")

        with patch("app.services.xhs_note_service.get_settings") as mock_settings:
            s = MagicMock()
            s.xhs_max_images = 20
            s.data_output_dir = "/tmp"
            s.xhs_image_max_size = 1024
            s.xhs_image_quality = 85
            mock_settings.return_value = s

            files = [_make_upload_file()]
            report, error = await generate_xhs_note_report("test", files)

        assert report is None
        assert "异常" in error
        mock_cleanup.assert_called_once()
