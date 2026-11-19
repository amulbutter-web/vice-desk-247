"""
High-Speed Audio Transcription Engine for Stream Highlights.
Powered by Groq Whisper API (whisper-large-v3-turbo) with word-level timestamps.
Features multi-key rotation, automatic failover, and fallback handling.
"""
import os
import sys
import uuid
import json
import logging
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.core.groq_pool import load_groq_keys
from src.config import settings

logger = logging.getLogger("transcription_engine")


class GroqTranscriptionEngine:
    """
    Extracts audio from video intervals and transcribes them with
    word-level millisecond precision using Groq's high-speed Whisper LPU inference.
    """

    def __init__(self, ffmpeg_bin: Optional[str] = None):
        self.ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_binary
        self.keys = load_groq_keys()
        self.current_key_idx = 0

    def _get_next_key(self) -> Optional[str]:
        if not self.keys:
            self.keys = load_groq_keys()
        if not self.keys:
            return None
        key = self.keys[self.current_key_idx % len(self.keys)]
        self.current_key_idx += 1
        return key

    def extract_audio_slice(
        self,
        video_path: str,
        start_sec: float,
        duration_sec: float,
        output_audio_path: str,
    ) -> bool:
        """Extracts mono 16kHz lightweight AAC audio for Whisper transcription."""
        out_p = Path(output_audio_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-ss", f"{start_sec:.3f}",
            "-t", f"{duration_sec:.3f}",
            "-i", str(video_path),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "aac",
            "-b:a", "48k",
            str(out_p.resolve()),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return res.returncode == 0 and out_p.exists() and out_p.stat().st_size > 500
        except Exception as e:
            logger.warning("[TRANSCRIPTION] FFmpeg audio extraction failed: %s", e)
            return False

    def transcribe_audio_file(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends audio file to Groq Whisper API and returns words with exact timestamps.
        """
        p = Path(audio_path)
        if not p.exists() or p.stat().st_size < 500:
            return {"text": "", "words": []}

        audio_bytes = p.read_bytes()

        # Try up to 3 keys from the pool
        attempts = min(3, max(1, len(self.keys)))
        for attempt in range(attempts):
            key = self._get_next_key()
            if not key:
                logger.warning("[TRANSCRIPTION] No Groq API key available")
                break

            boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
            body = bytearray()

            def add_field(name: str, value: str):
                body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode("utf-8"))

            def add_file(name: str, filename: str, content: bytes):
                body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{filename}\"\r\nContent-Type: audio/m4a\r\n\r\n".encode("utf-8"))
                body.extend(content)
                body.extend(b"\r\n")

            add_field("model", "whisper-large-v3-turbo")
            add_field("response_format", "verbose_json")
            add_field("timestamp_granularities[]", "word")
            if language:
                add_field("language", language)
            add_file("file", "audio.m4a", audio_bytes)
            body.extend(f"--{boundary}--\r\n".encode("utf-8"))

            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                data=bytes(body),
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ViceDesk/1.0",
                },
            )

            try:
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = json.loads(resp.read().decode())
                    text = data.get("text", "").strip()
                    raw_words = data.get("words", [])

                    words = []
                    for w in raw_words:
                        word_str = w.get("word", "").strip()
                        if word_str:
                            start_ms = max(0, int(w.get("start", 0.0) * 1000))
                            end_ms = max(start_ms + 100, int(w.get("end", 0.0) * 1000))
                            words.append({
                                "word": word_str,
                                "start_ms": start_ms,
                                "end_ms": end_ms,
                            })

                    logger.info(
                        "[TRANSCRIPTION] Transcribed %d words (length: %.1fs). Snippet: '%s'",
                        len(words),
                        (words[-1]["end_ms"] / 1000.0) if words else 0.0,
                        text[:60],
                    )

                    has_devanagari = any(
                        any("\u0900" <= c <= "\u097F" for c in w["word"])
                        for w in words
                    )
                    if has_devanagari:
                        words = self.transliterate_to_hinglish(words)
                        text = " ".join(w["word"] for w in words)

                    return {"text": text, "words": words}

            except urllib.error.HTTPError as he:
                logger.warning(
                    "[TRANSCRIPTION] Groq Whisper HTTP %s (Key #%d): %s",
                    he.code, self.current_key_idx, str(he)[:150]
                )
            except Exception as e:
                logger.warning(
                    "[TRANSCRIPTION] Groq Whisper error (Key #%d): %s",
                    self.current_key_idx, str(e)[:150]
                )

        return {"text": "", "words": []}

    def transliterate_to_hinglish(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transliterates Hindi/Devanagari word list into high-impact Roman Hinglish,
        preserving exact 1:1 timestamps for synchronized mobile subtitles.
        """
        if not words:
            return words
        try:
            from src.core.groq_pool import GroqPool
            import re
            pool = GroqPool(self.keys)
            raw_list = [w["word"] for w in words]
            prompt = (
                "You are an elite subtitle transliterator for Indian gaming Reels (CarryMinati, Mythpat).\n"
                "Transliterate the following list of spoken Hindi words into high-energy Roman Hinglish.\n"
                "STRICT RULES:\n"
                "1. Convert EVERY Hindi/Devanagari word into uppercase Roman Hinglish (e.g. 'BHAI', 'STRIP CLUB', 'POLICE', 'BHAGO').\n"
                "2. Output MUST be 100% standard English ASCII characters (A-Z, 0-9). NEVER output any Devanagari characters or unicode accents.\n"
                "3. Preserve EXACT 1:1 word count and array order matching the input array.\n"
                f"Input words: {json.dumps(raw_list, ensure_ascii=False)}\n"
                "Return ONLY a valid JSON array of strings in UPPERCASE, nothing else."
            )
            ans = pool.generate_chat(
                [{"role": "user", "content": prompt}],
                agent_role="A07_SUBTITLE_STYLIST",
                max_tokens=len(words) * 6 + 100,
                temperature=0.1,
            )
            m = re.search(r"\[.*\]", ans, re.DOTALL)
            if m:
                transliterated = json.loads(m.group(0))
                if len(transliterated) == len(words):
                    for i, tw in enumerate(transliterated):
                        clean_w = re.sub(r"[^\x00-\x7F]+", "", str(tw)).strip().upper()
                        words[i]["word"] = clean_w if clean_w else words[i]["word"]
                    logger.info("[TRANSCRIPTION] Successfully transliterated %d words to Roman Hinglish", len(words))
                    return words
        except Exception as e:
            logger.warning("[TRANSCRIPTION] Groq Hinglish transliteration note: %s", e)

        # Fallback rule-based transliterator to ensure zero raw Devanagari in ASS
        res = self._fallback_transliterate(words)
        import re
        for w in res:
            w["word"] = re.sub(r"[^\x00-\x7F]+", "", w["word"]).strip().upper()
        return res

    @staticmethod
    def _fallback_transliterate(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deterministic fallback transliterator for Devanagari characters."""
        d_map = {
            'अ': 'A', 'आ': 'AA', 'इ': 'I', 'ई': 'EE', 'उ': 'U', 'ऊ': 'OO', 'ऋ': 'RI',
            'ए': 'E', 'ऐ': 'AI', 'ओ': 'O', 'औ': 'AU', 'अं': 'AN', 'अः': 'AH',
            'क': 'K', 'ख': 'KH', 'ग': 'G', 'घ': 'GH', 'ङ': 'NG',
            'च': 'CH', 'छ': 'CHH', 'ज': 'J', 'झ': 'JH', 'ञ': 'NY',
            'ट': 'T', 'ठ': 'TH', 'ड': 'D', 'ढ': 'DH', 'ण': 'N',
            'त': 'T', 'थ': 'TH', 'द': 'D', 'ध': 'DH', 'न': 'N',
            'प': 'P', 'फ': 'PH', 'ब': 'B', 'भ': 'BH', 'म': 'M',
            'य': 'Y', 'र': 'R', 'ल': 'L', 'व': 'V', 'श': 'SH', 'ष': 'SH', 'स': 'S', 'ह': 'H',
            'ा': 'A', 'ि': 'I', 'ी': 'EE', 'ु': 'U', 'ू': 'OO', 'ृ': 'RI',
            'े': 'E', 'ै': 'AI', 'ो': 'O', 'ौ': 'AU', 'ं': 'N', 'ँ': 'N', '्': '',
            '़': '', '।': '.', '॥': '.',
            'ड़': 'R', 'ड़': 'R', 'ढ़': 'RH', 'फ़': 'F', 'ज़': 'Z', 'ख़': 'KH', 'ग़': 'GH', 'क़': 'Q',
        }
        for w in words:
            word_str = w["word"]
            if any("\u0900" <= c <= "\u097F" for c in word_str):
                converted = "".join(d_map.get(c, c) for c in word_str)
                w["word"] = converted.strip().upper()
        return words

    def transcribe_video_interval(
        self,
        video_path: str,
        start_sec: float,
        duration_sec: float,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convenience method: extracts slice audio, transcribes, and cleans up."""
        temp_audio = Path(settings.media_dir) / "temp" / f"audio_{uuid.uuid4().hex[:8]}.m4a"
        try:
            ok = self.extract_audio_slice(video_path, start_sec, duration_sec, str(temp_audio))
            if not ok:
                return {"text": "", "words": []}
            return self.transcribe_audio_file(str(temp_audio), language=language)
        finally:
            temp_audio.unlink(missing_ok=True)
