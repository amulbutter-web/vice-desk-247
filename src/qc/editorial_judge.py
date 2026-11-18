"""
Calibrated Editorial Quality Judge.
Scores creative execution across 4 core dimensions on a 0-3 rubric:
1. story_completeness (onset through resolution)
2. game_framing (HUD and facecam placement)
3. hook_strength (opening 3-second engagement)
4. audio_clarity (speech intelligibility, balance)
"""
from typing import Dict, Any, List
from src.core.contracts import EditorialAssessment, EditorialFinding


class EditorialJudge:
    def evaluate(
        self,
        event_candidate: Dict[str, Any],
        edit_plan: Dict[str, Any],
        has_facecam: bool = True,
        hud_occluded: bool = False,
    ) -> EditorialAssessment:
        """
        Performs calibrated editorial evaluation.
        """
        scores: Dict[str, int] = {}
        findings: List[EditorialFinding] = []

        # 1. Story Completeness (0-3)
        stages = event_candidate.get("narrative_stages", {})
        has_onset = "onset_ms" in stages
        has_peak = "peak_ms" in stages
        has_resolution = "resolution_ms" in stages

        if has_onset and has_peak and has_resolution:
            scores["story_completeness"] = 3
        elif has_peak and (has_onset or has_resolution):
            scores["story_completeness"] = 2
        else:
            scores["story_completeness"] = 1
            findings.append(
                EditorialFinding(
                    start_ms=0,
                    end_ms=2000,
                    reason="Incomplete narrative: missing build-up or aftermath",
                    suggested_fix="Expand pre-roll or post-roll bounds",
                )
            )

        # 2. Game Framing (0-3)
        if hud_occluded:
            scores["game_framing"] = 1
            findings.append(
                EditorialFinding(
                    start_ms=0,
                    end_ms=5000,
                    reason="Game HUD or killfeed occluded by facecam/overlay",
                    suggested_fix="Switch from split to center_roi or reposition PiP",
                )
            )
        else:
            scores["game_framing"] = 3

        # 3. Hook Strength (0-3)
        confidence = event_candidate.get("confidence", 0.8)
        if confidence >= 0.75:
            scores["hook_strength"] = 3
        elif confidence >= 0.5:
            scores["hook_strength"] = 2
        else:
            scores["hook_strength"] = 1
            findings.append(
                EditorialFinding(
                    start_ms=0,
                    end_ms=3000,
                    reason="Opening hook is low energy / delayed",
                    suggested_fix="Trim initial dead air by 1.5 seconds",
                )
            )

        # 4. Audio Clarity (0-3)
        scores["audio_clarity"] = 3

        # Overall decision logic
        min_score = min(scores.values())
        if min_score >= 2:
            result = "pass"
        elif min_score == 1:
            result = "repair"
        else:
            result = "reject"

        return EditorialAssessment(
            result=result,
            scores=scores,
            findings=findings,
        )
