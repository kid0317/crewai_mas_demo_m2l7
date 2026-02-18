"""所有 Pydantic 数据模型的单元测试。"""

import pytest
from pydantic import ValidationError

from app.schemas.common import ErrorDetail, ApiResponse
from app.schemas.xhs_note import (
    XhsContentStrategyBrief,
    XhsCopywritingOutput,
    XhsImageEditBatchReport,
    XhsImageEditPlan,
    XhsImageInput,
    XhsImageVisualAnalysis,
    XhsImageWithPlans,
    XhsNoteFinalReport,
    XhsNoteIdeaRequest,
    XhsNoteReportResponse,
    XhsSEOOptimizedNote,
    XhsVisualBatchReport,
)


# ---------------------------------------------------------------------------
# common schemas
# ---------------------------------------------------------------------------


class TestErrorDetail:
    def test_basic(self):
        e = ErrorDetail(code=500, message="Internal server error")
        assert e.code == 500
        assert e.message == "Internal server error"
        assert e.request_id == ""

    def test_with_request_id(self):
        e = ErrorDetail(code=401, message="Unauthorized", request_id="rid-123")
        assert e.request_id == "rid-123"

    def test_model_dump(self):
        e = ErrorDetail(code=404, message="Not found", request_id="r1")
        d = e.model_dump()
        assert d == {"code": 404, "message": "Not found", "request_id": "r1"}


class TestApiResponse:
    def test_defaults(self):
        r = ApiResponse()
        assert r.code == 0
        assert r.message == "ok"
        assert r.data is None
        assert r.request_id == ""

    def test_with_data(self):
        r = ApiResponse(code=0, message="ok", data={"key": "value"}, request_id="r1")
        assert r.data == {"key": "value"}
        assert r.request_id == "r1"

    def test_error_response(self):
        r = ApiResponse(code=1, message="失败", data=None, request_id="r2")
        assert r.code == 1
        assert r.data is None

    def test_generic_typed(self):
        r = ApiResponse[XhsNoteReportResponse](
            code=0,
            message="ok",
            data=XhsNoteReportResponse(report="test report"),
            request_id="r3",
        )
        assert r.data.report == "test report"


# ---------------------------------------------------------------------------
# xhs_note schemas
# ---------------------------------------------------------------------------


class TestXhsImageInput:
    def test_basic(self):
        img = XhsImageInput(image_id="img_0", file_name="test.jpg", local_path="/tmp/test.jpg")
        assert img.image_id == "img_0"
        assert img.file_name == "test.jpg"
        assert img.local_path == "/tmp/test.jpg"

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            XhsImageInput(image_id="img_0", file_name="test.jpg")  # missing local_path


class TestXhsNoteIdeaRequest:
    def test_basic(self):
        req = XhsNoteIdeaRequest(
            idea_text="测试意图",
            images=[XhsImageInput(image_id="img_0", file_name="a.jpg", local_path="/a.jpg")],
        )
        assert req.idea_text == "测试意图"
        assert len(req.images) == 1

    def test_empty_images(self):
        req = XhsNoteIdeaRequest(idea_text="测试", images=[])
        assert len(req.images) == 0

    def test_missing_idea_text(self):
        with pytest.raises(ValidationError):
            XhsNoteIdeaRequest(images=[])


class TestXhsImageVisualAnalysis:
    def test_basic(self):
        v = XhsImageVisualAnalysis(
            image_id="img_0",
            file_name="test.jpg",
            subject_description="主体描述",
            atmosphere_vibe="氛围",
            visual_details=["细节1", "细节2", "细节3"],
            image_quality_score="8分",
            highlight_feature="视觉锚点",
        )
        assert v.image_id == "img_0"
        assert len(v.visual_details) == 3

    def test_missing_visual_details(self):
        with pytest.raises(ValidationError):
            XhsImageVisualAnalysis(
                image_id="img_0",
                file_name="test.jpg",
                subject_description="主体",
                atmosphere_vibe="氛围",
                # visual_details missing
                image_quality_score="8分",
                highlight_feature="锚点",
            )

    def test_json_serialization(self):
        v = XhsImageVisualAnalysis(
            image_id="img_0",
            file_name="test.jpg",
            subject_description="描述",
            atmosphere_vibe="氛围",
            visual_details=["a", "b", "c"],
            image_quality_score="8分",
            highlight_feature="锚点",
        )
        json_str = v.model_dump_json()
        assert "img_0" in json_str


class TestXhsImageEditPlan:
    def test_basic(self):
        p = XhsImageEditPlan(
            image_id="img_0",
            file_name="test.jpg",
            overall_edit_strategy="整体策略",
            crop_suggestion="裁剪建议",
            light_color_adjustment="亮度调整",
            filter_suggestion="滤镜建议",
            text_overlay_suggestion="文字建议",
            beauty_adjustment_suggestion="美颜建议",
            is_recommended_as_cover=True,
            risk_and_pitfall_notes="风险提示",
        )
        assert p.is_recommended_as_cover is True
        assert p.image_id == "img_0"

    def test_bool_field(self):
        p = XhsImageEditPlan(
            image_id="img_0",
            file_name="test.jpg",
            overall_edit_strategy="策略",
            crop_suggestion="裁剪",
            light_color_adjustment="调整",
            filter_suggestion="滤镜",
            text_overlay_suggestion="文字",
            beauty_adjustment_suggestion="美颜",
            is_recommended_as_cover=False,
            risk_and_pitfall_notes="风险",
        )
        assert p.is_recommended_as_cover is False


class TestXhsVisualBatchReport:
    def test_basic(self):
        v = XhsImageVisualAnalysis(
            image_id="img_0", file_name="a.jpg",
            subject_description="描述", atmosphere_vibe="氛围",
            visual_details=["a", "b", "c"], image_quality_score="8",
            highlight_feature="锚点",
        )
        batch = XhsVisualBatchReport(
            user_raw_intent="测试意图",
            images_visual=[v],
            summary="整体总结",
        )
        assert len(batch.images_visual) == 1
        assert batch.summary == "整体总结"


class TestXhsImageEditBatchReport:
    def test_basic(self):
        p = XhsImageEditPlan(
            image_id="img_0", file_name="a.jpg",
            overall_edit_strategy="策略", crop_suggestion="裁剪",
            light_color_adjustment="调整", filter_suggestion="滤镜",
            text_overlay_suggestion="文字", beauty_adjustment_suggestion="美颜",
            is_recommended_as_cover=True, risk_and_pitfall_notes="风险",
        )
        batch = XhsImageEditBatchReport(
            images_edit_plan=[p],
            summary="编辑方案总结",
        )
        assert len(batch.images_edit_plan) == 1


class TestXhsContentStrategyBrief:
    def test_basic(self):
        brief = XhsContentStrategyBrief(
            input_evaluation="评估",
            target_audience_persona="画像",
            core_pain_point="痛点",
            suggested_title="标题",
            content_outline=["大纲1", "大纲2"],
            engagement_strategy="互动策略",
            retention_strategy="留存策略",
            seo_keywords=["关键词1", "关键词2"],
        )
        assert len(brief.content_outline) == 2
        assert len(brief.seo_keywords) == 2


class TestXhsCopywritingOutput:
    def test_basic(self):
        copy = XhsCopywritingOutput(
            title="🥗 标题",
            content="正文内容",
            picture_order=["img_0", "img_1"],
            highlight_hooks=["钩子1"],
        )
        assert copy.title.startswith("🥗")
        assert len(copy.picture_order) == 2


class TestXhsSEOOptimizedNote:
    def test_basic(self):
        seo = XhsSEOOptimizedNote(
            optimization_summary="优化说明",
            optimized_title="优化标题",
            optimized_content="优化正文",
            optimized_picture_order=["img_0"],
            tags=["标签1", "标签2", "标签3", "标签4", "标签5"],
        )
        assert len(seo.tags) == 5


class TestXhsImageWithPlans:
    def test_basic(self):
        img = XhsImageInput(image_id="img_0", file_name="a.jpg", local_path="/a.jpg")
        visual = XhsImageVisualAnalysis(
            image_id="img_0", file_name="a.jpg",
            subject_description="描述", atmosphere_vibe="氛围",
            visual_details=["a", "b", "c"], image_quality_score="8",
            highlight_feature="锚点",
        )
        plan = XhsImageEditPlan(
            image_id="img_0", file_name="a.jpg",
            overall_edit_strategy="策略", crop_suggestion="裁剪",
            light_color_adjustment="调整", filter_suggestion="滤镜",
            text_overlay_suggestion="文字", beauty_adjustment_suggestion="美颜",
            is_recommended_as_cover=True, risk_and_pitfall_notes="风险",
        )
        combined = XhsImageWithPlans(base_info=img, visual_analysis=visual, edit_plan=plan)
        assert combined.base_info.image_id == "img_0"
        assert combined.visual_analysis.image_id == "img_0"


class TestXhsNoteFinalReport:
    def test_basic(self):
        from tests.conftest import (
            make_strategy_brief, make_copywriting, make_seo_note,
            make_image_input, make_visual_analysis, make_edit_plan,
        )
        report = XhsNoteFinalReport(
            idea_text="测试",
            strategy_brief=make_strategy_brief(),
            raw_copywriting=make_copywriting(),
            seo_optimized_note=make_seo_note(),
            images=[
                XhsImageWithPlans(
                    base_info=make_image_input(0),
                    visual_analysis=make_visual_analysis(0),
                    edit_plan=make_edit_plan(0),
                )
            ],
        )
        assert report.idea_text == "测试"
        assert len(report.images) == 1


class TestXhsNoteReportResponse:
    def test_basic(self):
        resp = XhsNoteReportResponse(report="完整报告文本")
        assert resp.report == "完整报告文本"

    def test_missing_report(self):
        with pytest.raises(ValidationError):
            XhsNoteReportResponse()
