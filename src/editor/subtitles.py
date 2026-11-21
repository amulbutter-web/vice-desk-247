"""
Advanced Subtitle & Kinetic Typography Generator.
Generates word-level animated captions (Hormozi/Viral-Gold style) and
platform-safe top hook banners using Advanced SubStation Alpha (ASS) format.
Supports exact vertical safe-zone placement for Instagram Reels, YouTube Shorts, and TikTok.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.core.security import validate_safe_zone


class SubtitleGenerator:
    def __init__(self, canvas_width: int = 1080, canvas_height: int = 1920):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

    def generate_srt(self, words: List[Dict[str, Any]]) -> str:
        """Converts word-timed transcript into standard SRT format."""
        srt_lines = []
        for idx, w in enumerate(words, 1):
            s_time = self._format_srt_time(w["start_ms"])
            e_time = self._format_srt_time(w["end_ms"])
            srt_lines.append(f"{idx}\n{s_time} --> {e_time}\n{w['word']}\n")
        return "\n".join(srt_lines)

    @staticmethod
    def _format_srt_time(ms: int) -> str:
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        milliseconds = ms % 1000
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    @staticmethod
    def _format_ass_time(ms: int) -> str:
        """Formats milliseconds into ASS timestamp format: H:MM:SS.cs"""
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        centiseconds = (ms % 1000) // 10
        return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"

    def generate_ass(
        self,
        words: List[Dict[str, Any]],
        output_ass_path: str,
        hook_text: Optional[str] = None,
        style_preset: str = "viral_gold",
        words_per_group: int = 3,
        hook_duration_ms: int = 7000,
        fallback_cues: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generates production-grade ASS subtitles with word-by-word active pop/highlight.
        Enforces vertical safe margins so IG Reels bottom UI & right buttons never overlap.
        Features seamless continuous timing between words (zero flicker).
        """
        out_p = Path(output_ass_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        # Style colors in ASS BGR format (&H00BBGGRR)
        if style_preset == "neon_cyan":
            active_color = "&H00FFA300"  # Cyan/teal
        elif style_preset == "neon_green":
            active_color = "&H0000FF55"  # Bright green
        else:
            active_color = "&H0025B3E6"  # Signature Viral Gold (#E6B325)

        ass_lines = [
            "[Script Info]",
            "ScriptType: v4.00+",
            f"PlayResX: {self.canvas_width}",
            f"PlayResY: {self.canvas_height}",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            # ViralMain: Clean white base font, bold black border
            f"Style: ViralMain,DejaVu Sans,Arial Black,80,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,7,3,2,60,60,420,1",
            # ViralActive: Golden popped highlight
            f"Style: ViralActive,DejaVu Sans,Arial Black,88,{active_color},&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,118,118,2,0,1,8,4,2,60,60,420,1",
            # HookBanner: Clean, non-overlapping top curiosity banner (high CTR, never overlaps gameplay HUD or subtitles)
            f"Style: HookBanner,DejaVu Sans,Arial Black,54,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,8,60,60,180,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]

        # 1. Top Hook Banner (Stays visible during hook window, auto-clamped to 5 words to prevent multi-line clutter)
        if hook_text and hook_text.strip():
            raw_words = hook_text.strip().upper().split()
            # Enforce max 6 words so banner never overflows or overlaps screen action
            clean_hook = " ".join(raw_words[:6]) if len(raw_words) > 6 else " ".join(raw_words)
            hook_end_time = self._format_ass_time(hook_duration_ms)
            ass_lines.append(
                f"Dialogue: 1,0:00:00.00,{hook_end_time},HookBanner,,0,0,0,,{clean_hook}"
            )

        # 2. Word Groups with Active Highlight (Karaoke Hormozi style)
        if words:
            # Group words intelligently, breaking on silence pauses > 1.2s
            groups = []
            curr_group = []
            for w in words:
                if curr_group:
                    gap_ms = w["start_ms"] - curr_group[-1]["end_ms"]
                    if gap_ms > 1200 or len(curr_group) >= words_per_group:
                        groups.append(curr_group)
                        curr_group = [w]
                    else:
                        curr_group.append(w)
                else:
                    curr_group.append(w)
            if curr_group:
                groups.append(curr_group)

            for g_idx, group in enumerate(groups):
                next_group_start = groups[g_idx + 1][0]["start_ms"] if g_idx < len(groups) - 1 else None
                for w_idx, current_word in enumerate(group):
                    w_start_ms = current_word["start_ms"]
                    if w_idx < len(group) - 1:
                        # Seamless transition to next word in group — zero blackout/flicker
                        w_end_ms = group[w_idx + 1]["start_ms"]
                    else:
                        # Last word stays visible for reading grace (350ms) or until next group begins
                        target_end = current_word["end_ms"] + 350
                        w_end_ms = min(target_end, next_group_start) if next_group_start else target_end

                    if w_end_ms <= w_start_ms:
                        w_end_ms = w_start_ms + 120

                    w_start = self._format_ass_time(w_start_ms)
                    w_end = self._format_ass_time(w_end_ms)

                    rendered_parts = []
                    for idx, w in enumerate(group):
                        word_str = w["word"].strip().upper().replace("{", "").replace("}", "").replace("\\", "")
                        if idx == w_idx:
                            rendered_parts.append(f"{{\\c{active_color}\\fscx112\\fscy112}}{word_str}{{\\r}}")
                        else:
                            rendered_parts.append(f"{{\\c&H00FFFFFF&}}{word_str}{{\\r}}")

                    line_text = " ".join(rendered_parts)
                    ass_lines.append(
                        f"Dialogue: 0,{w_start},{w_end},ViralMain,,0,0,0,,{line_text}"
                    )
        elif fallback_cues:
            # Dynamic kinetic action callouts when no spoken words are detected
            for cue in fallback_cues:
                c_start = self._format_ass_time(cue.get("start_ms", 0))
                c_end = self._format_ass_time(cue.get("end_ms", 3000))
                c_text = cue.get("text", "").strip().upper()
                if c_text:
                    ass_lines.append(
                        f"Dialogue: 0,{c_start},{c_end},ViralActive,,0,0,0,,{c_text}"
                    )

        content = "\n".join(ass_lines)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(content)

        return str(out_p.resolve())

    def build_safe_drawtext_filter(
        self, text: str, start_sec: float, end_sec: float, y_pos: int = 1500, font_size: int = 48
    ) -> str:
        """Legacy fallback drawtext filter."""
        is_safe, _ = validate_safe_zone(
            x=int(self.canvas_width * 0.15),
            y=y_pos,
            width=int(self.canvas_width * 0.70),
            height=font_size + 20,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
        )
        if not is_safe:
            y_pos = int(self.canvas_height * 0.75)

        clean_text = text.replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")
        return (
            f"drawtext=text='{clean_text}':fontcolor=yellow:fontsize={font_size}:"
            f"box=1:boxcolor=black@0.65:boxborderw=10:x=(w-text_w)/2:y={y_pos}:"
            f"enable='between(t,{start_sec},{end_sec})'"
        )
