"""
Creative Editorial Planner.
Transforms detected narrative events into a rich, typed EditPlan.
Determines 9:16 layout (Split, Crop, PiP), motion dynamics (kinetic zoom, slow-mo),
audio leveling, and subtitle placements.
"""
from typing import Dict, Any, List, Optional
from src.config import settings
from src.core.contracts import EditPlan, Segment, Canvas, EditOperation


class EditorialPlanner:
    def __init__(
        self,
        canvas_width: int = 1080,
        canvas_height: int = 1920,
        fps: float = 60.0,
    ):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.fps = fps

    def create_edit_plan(
        self,
        plan_id: str,
        trace_id: str,
        event_revision_id: str,
        media_asset_id: str,
        event_candidate: Dict[str, Any],
        platform: str = "instagram",
        layout_mode: str = "split_cam_game",  # split_cam_game, center_crop, pip
    ) -> EditPlan:
        """
        Generates a validated EditPlan matching contracts/edit_plan.json.
        """
        start_ms = event_candidate["window_start_ms"]
        end_ms = event_candidate["window_end_ms"]
        stages = event_candidate.get("narrative_stages", {})
        peak_ms = stages.get("peak_ms", start_ms + (end_ms - start_ms) // 2)

        duration_ms = end_ms - start_ms

        # 1. Base segment definition
        segments = [
            Segment(
                source_start_ms=start_ms,
                source_end_ms=end_ms,
                time_epoch=0,
                reason="narrative_highlight_full_window",
            )
        ]

        # 2. Canvas definition
        canvas = Canvas(
            width=self.canvas_width,
            height=self.canvas_height,
            fps=self.fps,
        )

        operations: List[EditOperation] = []

        # 3. Layout operation
        if layout_mode == "split_cam_game":
            operations.append(
                EditOperation(
                    type="crop",
                    start_ms=0,
                    end_ms=duration_ms,
                    parameters={
                        "mode": "split",
                        "top_facecam_pct": 0.35,
                        "bottom_game_pct": 0.65,
                    },
                )
            )
        elif layout_mode == "pip":
            operations.append(
                EditOperation(
                    type="pip",
                    start_ms=0,
                    end_ms=duration_ms,
                    parameters={
                        "pip_x": 60,
                        "pip_y": 300,
                        "pip_w": 320,
                        "pip_h": 240,
                    },
                )
            )
        else:
            # Centered 9:16 crop from 16:9
            operations.append(
                EditOperation(
                    type="crop",
                    start_ms=0,
                    end_ms=duration_ms,
                    parameters={
                        "mode": "center_roi",
                        "crop_w": 1080,
                        "crop_h": 1920,
                    },
                )
            )

        # 4. Kinetic Zoom during Peak / Climax
        climax_start = max(0, peak_ms - start_ms - 1000)
        climax_end = min(duration_ms, peak_ms - start_ms + 1500)
        if climax_end > climax_start:
            operations.append(
                EditOperation(
                    type="zoom",
                    start_ms=climax_start,
                    end_ms=climax_end,
                    parameters={"zoom_factor": 1.15, "easing": "ease_in_out"},
                )
            )

        # 5. Audio Normalization (LUFS target)
        operations.append(
            EditOperation(
                type="audio_gain",
                start_ms=0,
                end_ms=duration_ms,
                parameters={
                    "target_lufs": settings.lufs_target_integrated,
                    "true_peak_dbtp": settings.max_true_peak_dbtp,
                },
            )
        )

        
        return EditPlan(
            id=plan_id,
            trace_id=trace_id,
            event_revision_id=event_revision_id,
            media_asset_id=media_asset_id,
            platform=platform,
            segments=segments,
            canvas=canvas,
            operations=operations,
            evidence_refs=[event_candidate.get("id", "event-ref-0")],
        )
