"""
False-Positive and Silent-Clutch Filter.
Discriminates between true gameplay highlights and misleading spikes:
- Loading screen screams
- Lobby / menu music
- Blank / black screens
- Silent high-skill clutch plays
"""
from typing import Dict, Any, List, Tuple


class FalsePositiveFilter:
    def evaluate_candidate(
        self,
        event_candidate: Dict[str, Any],
        black_frames: List[Dict[str, Any]],
        freeze_frames: List[Dict[str, Any]],
        audio_excitement: float,
        visual_activity: float,
        chat_velocity: float = 0.0,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Evaluates candidate validity.
        Returns: (is_valid, reason, metrics)
        """
        start_ms = event_candidate.get("window_start_ms", 0)
        end_ms = event_candidate.get("window_end_ms", 0)
        duration_ms = end_ms - start_ms

        # 1. Check for Black Screen Overlap during peak
        for bf in black_frames:
            overlap_start = max(start_ms, bf["start_ms"])
            overlap_end = min(end_ms, bf["end_ms"])
            if overlap_end > overlap_start:
                overlap_dur = overlap_end - overlap_start
                if overlap_dur > 1500:  # More than 1.5s black screen
                    return False, "REJECTED_BLACK_SCREEN_OVERLAP", {
                        "black_duration_ms": overlap_dur,
                        "type": "black_screen_false_positive"
                    }

        # 2. Check for Loading Screen Scream (High audio excitement + Frozen visual)
        for ff in freeze_frames:
            overlap_start = max(start_ms, ff["start_ms"])
            overlap_end = min(end_ms, ff["end_ms"])
            if overlap_end > overlap_start:
                overlap_dur = overlap_end - overlap_start
                if overlap_dur > 2000 and audio_excitement > 0.7:
                    return False, "REJECTED_LOADING_SCREEN_SCREAM", {
                        "freeze_duration_ms": overlap_dur,
                        "audio_excitement": audio_excitement,
                        "type": "loading_screen_scream"
                    }

        # 3. Detect Silent Clutch (Quiet audio, but intense visual action)
        if audio_excitement < 0.35 and visual_activity > 0.65:
            return True, "ACCEPTED_SILENT_CLUTCH", {
                "audio_excitement": audio_excitement,
                "visual_activity": visual_activity,
                "classification": "silent_clutch"
            }

        # 4. Check for Troll Chat Spike with no actual audio or visual activity
        if chat_velocity > 0.8 and audio_excitement < 0.25 and visual_activity < 0.25:
            return False, "REJECTED_TROLL_CHAT_SPIKE", {
                "chat_velocity": chat_velocity,
                "audio_excitement": audio_excitement,
                "visual_activity": visual_activity,
                "type": "troll_chat_spike"
            }

        # 5. General low-signal rejection
        if audio_excitement < 0.3 and visual_activity < 0.3:
            return False, "REJECTED_LOW_SIGNAL_INTENSITY", {
                "audio_excitement": audio_excitement,
                "visual_activity": visual_activity,
            }

        return True, "ACCEPTED_GAMEPLAY_HIGHLIGHT", {
            "audio_excitement": audio_excitement,
            "visual_activity": visual_activity,
        }
