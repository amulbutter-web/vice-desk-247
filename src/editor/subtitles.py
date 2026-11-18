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
        words_per_group: int = 4,
    ) -> str:
        """
        Generates production-grade ASS subtitles with word-by-word active pop/highlight.
        Enforces vertical safe margins so IG Reels bottom UI & right buttons never overlap.
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
            f"Style: ViralMain,Impact,80,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,7,3,2,60,60,420,1",
            # ViralActive: Golden popped highlight
            f"Style: ViralActive,Impact,88,{active_color},&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,118,118,2,0,1,8,4,2,60,60,420,1",
            # HookBanner: Persistent top banner, bold vibrant uppercase, high CTR
            f"Style: HookBanner,Impact,74,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,3,0,1,8,4,8,40,40,240,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]

        # 1. Top Hook Banner (stays persistent across entire clip for maximum retention)
        if hook_text and hook_text.strip():
            clean_hook = hook_text.strip().upper()
            ass_lines.append(
                f"Dialogue: 1,0:00:00.00,0:01:00.00,HookBanner,,0,0,0,,{clean_hook}"
            )

        # 2. Word Groups with Active Highlight
        # We group words into chunks of `words_per_group` (e.g. 3-4 words)
        if words:
            for i in range(0, len(words), words_per_group):
                group = words[i : i + words_per_group]
                if not group:
                    continue

                group_start = group[0]["start_ms"]
                group_end = group[-1]["end_ms"]

                # For each word in the group, create an event where that word is highlighted
                for w_idx, current_word in enumerate(group):
                    w_start = self._format_ass_time(current_word["start_ms"])
                    w_end = self._format_ass_time(current_word["end_ms"])

                    # Construct text line where current_word has active styling
                    rendered_parts = []
                    for idx, w in enumerate(group):
                        word_str = w["word"].strip().upper()
                        if idx == w_idx:
                            # Popped word in Gold
                            rendered_parts.append(f"{{\\c{active_color}\\fscx112\\fscy112}}{word_str}{{\\r}}")
                        else:
                            # Regular white word
                            rendered_parts.append(f"{{\\c&H00FFFFFF&}}{word_str}{{\\r}}")

                    line_text = " ".join(rendered_parts)
                    ass_lines.append(
                        f"Dialogue: 0,{w_start},{w_end},ViralMain,,0,0,0,,{line_text}"
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
