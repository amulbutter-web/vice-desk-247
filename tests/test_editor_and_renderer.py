"""
Tests for EditorialPlanner, SubtitleGenerator, FiltergraphGenerator, and VideoRenderer.
Renders real vertical 1080x1920 MP4 clips using FFmpeg.
"""
from pathlib import Path
from src.editor.planner import EditorialPlanner
from src.editor.subtitles import SubtitleGenerator
from src.editor.filtergraph import FiltergraphGenerator
from src.editor.renderer import VideoRenderer
from src.ingest.probe import MediaProbe


def test_editorial_planner_creates_valid_plan():
    planner = EditorialPlanner(canvas_width=1080, canvas_height=1920, fps=60.0)
    candidate = {
        "id": "cand-001",
        "window_start_ms": 2000,
        "window_end_ms": 14000,
        "narrative_stages": {"peak_ms": 8000},
    }
    plan = planner.create_edit_plan(
        plan_id="plan-001",
        trace_id="tr-001",
        event_revision_id="rev-001",
        media_asset_id="asset-001",
        event_candidate=candidate,
        platform="youtube",
        layout_mode="split_cam_game",
    )
    assert plan.canvas.width == 1080
    assert plan.canvas.height == 1920
    assert len(plan.segments) == 1
    assert plan.segments[0].source_start_ms == 2000
    assert any(op.type == "crop" for op in plan.operations)


def test_subtitle_safe_zone_positioning():
    subs = SubtitleGenerator(canvas_width=1080, canvas_height=1920)
    # y=1500 is within safe zone (between top 15% / y=288 and bottom 20% / y=1536)
    drawtext = subs.build_safe_drawtext_filter("HEADSHOT!", start_sec=1.0, end_sec=3.0, y_pos=1400)
    assert "drawtext=" in drawtext
    assert "HEADSHOT!" in drawtext


def test_video_renderer_real_mp4(sample_video, tmp_path):
    planner = EditorialPlanner(canvas_width=1080, canvas_height=1920, fps=30.0)
    candidate = {
        "id": "cand-001",
        "window_start_ms": 1000,
        "window_end_ms": 11000,  # 10s clip
        "narrative_stages": {"peak_ms": 5000},
    }
    plan = planner.create_edit_plan(
        plan_id="plan-render-01",
        trace_id="tr-render-01",
        event_revision_id="rev-render-01",
        media_asset_id="asset-render-01",
        event_candidate=candidate,
        platform="youtube",
        layout_mode="split_cam_game",
    )

    out_file = tmp_path / "rendered_vertical.mp4"
    renderer = VideoRenderer()
    meta = renderer.render_clip(
        source_path=sample_video,
        output_path=str(out_file),
        edit_plan=plan,
        timeout_sec=60,
    )

    assert out_file.exists()
    assert meta["width"] == 1080
    assert meta["height"] == 1920
    assert meta["video_codec"] == "h264"
    assert meta["has_audio"] is True
    assert meta["duration_ms"] >= 9500


def test_kinetic_ass_subtitles_generation(tmp_path):
    subs = SubtitleGenerator(canvas_width=1080, canvas_height=1920)
    words = [
        {"word": "CAR", "start_ms": 100, "end_ms": 500},
        {"word": "CLEARS", "start_ms": 500, "end_ms": 900},
        {"word": "THE", "start_ms": 900, "end_ms": 1200},
        {"word": "RAMP", "start_ms": 1200, "end_ms": 1800},
    ]
    ass_path = tmp_path / "test.ass"
    out = subs.generate_ass(
        words=words,
        output_ass_path=str(ass_path),
        hook_text="INSANE LANDING",
        style_preset="viral_gold",
    )
    assert Path(out).exists()
    content = Path(out).read_text(encoding="utf-8")
    assert "[Script Info]" in content
    assert "PlayResX: 1080" in content
    assert "PlayResY: 1920" in content
    assert "INSANE LANDING" in content
    assert "ViralActive" in content
    assert "&H0025B3E6" in content  # Gold color


def test_video_renderer_with_blur_fill_and_ass(sample_video, tmp_path):
    planner = EditorialPlanner(canvas_width=1080, canvas_height=1920, fps=30.0)
    candidate = {
        "id": "cand-blur-01",
        "window_start_ms": 1000,
        "window_end_ms": 4000,  # 3s clip
        "narrative_stages": {"peak_ms": 2500},
    }
    plan = planner.create_edit_plan(
        plan_id="plan-blur-01",
        trace_id="tr-blur-01",
        event_revision_id="rev-blur-01",
        media_asset_id="asset-blur-01",
        event_candidate=candidate,
        platform="instagram",
        layout_mode="blur_fill",
    )
    # Manually set operation mode to blur_fill
    for op in plan.operations:
        if op.type == "crop":
            op.parameters["mode"] = "blur_fill"

    subs = SubtitleGenerator(canvas_width=1080, canvas_height=1920)
    words = [
        {"word": "NO", "start_ms": 1200, "end_ms": 1800},
        {"word": "WAY", "start_ms": 1800, "end_ms": 2500},
    ]
    ass_path = tmp_path / "test_blur.ass"
    subs.generate_ass(words=words, output_ass_path=str(ass_path), hook_text="WATCH THIS")

    out_file = tmp_path / "rendered_blur_fill.mp4"
    renderer = VideoRenderer()
    meta = renderer.render_clip(
        source_path=sample_video,
        output_path=str(out_file),
        edit_plan=plan,
        ass_subtitle_path=str(ass_path),
        timeout_sec=60,
    )

    assert out_file.exists()
    assert meta["width"] == 1080
    assert meta["height"] == 1920
    assert meta["video_codec"] == "h264"
    assert meta["duration_ms"] >= 2800
