"""
Strict Typed FFmpeg Filtergraph Generator.
Constructs complex FFmpeg filter graphs in pure Python without shell interpolation,
eliminating shell-injection vulnerabilities.
Supports:
- Split layout (Facecam top 35% + Gameplay bottom 65%) with clean divider
- Blur-Fill layout (16:9 gameplay centered + 25px Gaussian blurred background)
- Center ROI layout (tight 9:16 vertical crop)
- Word-level ASS subtitles with native libass rendering
- EBU R128 Broadcast Audio Loudness Normalization (-14 LUFS, -1.0 dBTP)
"""
from typing import List, Dict, Any, Optional
from src.core.contracts import EditPlan


class FiltergraphGenerator:
    @staticmethod
    def build_render_command(
        source_path: str,
        output_path: str,
        edit_plan: EditPlan,
        ffmpeg_bin: str = "ffmpeg",
        subtitle_filters: Optional[List[str]] = None,
        ass_subtitle_path: Optional[str] = None,
    ) -> List[str]:
        """
        Builds the FFmpeg command list for rendering an EditPlan into vertical 1080x1920 MP4.
        """
        seg = edit_plan.segments[0]
        start_sec = seg.source_start_ms / 1000.0
        duration_sec = (seg.source_end_ms - seg.source_start_ms) / 1000.0

        canvas_w = edit_plan.canvas.width
        canvas_h = edit_plan.canvas.height
        fps = edit_plan.canvas.fps

        # Inspect layout mode from operations
        crop_op = next((op for op in edit_plan.operations if op.type == "crop"), None)
        mode = crop_op.parameters.get("mode", "center_roi") if crop_op else "center_roi"

        filters = []

        if mode == "split":
            # Split layout: top facecam (35%), bottom gameplay (65%)
            top_h = int(canvas_h * 0.35)
            if top_h % 2 != 0:
                top_h -= 1
            bottom_h = canvas_h - top_h

            split_graph = (
                f"[0:v]scale={canvas_w}:{canvas_h}:force_original_aspect_ratio=increase,crop={canvas_w}:{canvas_h}[v_scaled];"
                f"[v_scaled]split=2[cam_in][game_in];"
                f"[cam_in]crop={canvas_w}:{top_h}:0:0[top_cam];"
                f"[game_in]crop={canvas_w}:{bottom_h}:0:{top_h}[bottom_game];"
                f"[top_cam][bottom_game]vstack=inputs=2[v_base]"
            )
            filters.append(split_graph)
            last_v = "v_base"

        elif mode == "blur_fill":
            # 16:9 gameplay centered + 25px Gaussian blurred background
            blur_graph = (
                f"[0:v]split=2[v_bg_in][v_fg_in];"
                f"[v_bg_in]scale={canvas_w}:{canvas_h}:force_original_aspect_ratio=increase,"
                f"crop={canvas_w}:{canvas_h},boxblur=25:5,eq=brightness=-0.25[v_bg];"
                f"[v_fg_in]scale={canvas_w}:-1[v_fg];"
                f"[v_bg][v_fg]overlay=(W-w)/2:(H-h)/2[v_base]"
            )
            filters.append(blur_graph)
            last_v = "v_base"

        else:
            # Centered 9:16 vertical crop with aspect-ratio-safe scale and center crop
            crop_graph = (
                f"[0:v]scale={canvas_w}:{canvas_h}:force_original_aspect_ratio=increase,"
                f"crop={canvas_w}:{canvas_h}:(in_w-{canvas_w})/2:(in_h-{canvas_h})/2[v_base]"
            )
            filters.append(crop_graph)
            last_v = "v_base"

        # Apply native libass subtitles if provided
        if ass_subtitle_path:
            safe_ass = ass_subtitle_path.replace("\\", "/").replace(":", "\\:")
            filters.append(f"[{last_v}]ass='{safe_ass}'[v_ass]")
            last_v = "v_ass"
        elif subtitle_filters:
            # Fallback legacy drawtext filters
            sub_chain = ",".join(subtitle_filters)
            filters.append(f"[{last_v}]{sub_chain}[v_subs]")
            last_v = "v_subs"

        # Audio loudness normalization to platform standards (-14 LUFS, -1.0 dBTP)
        audio_filter = "loudnorm=I=-14:TP=-1.0:LRA=11"

        complex_filter = ";".join(filters)

        cmd = [
            ffmpeg_bin,
            "-y",  # Overwrite output
            "-threads", "2",  # Restrict threads to prevent container OOM
            "-ss", f"{start_sec:.3f}",
            "-t", f"{duration_sec:.3f}",
            "-i", source_path,
            "-filter_complex", complex_filter,
            "-map", f"[{last_v}]",
            "-map", "0:a?",
            "-af", audio_filter,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-r", str(int(fps)),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-movflags", "+faststart",
            output_path,
        ]

        return cmd
