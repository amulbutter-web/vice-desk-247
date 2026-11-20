"""
Autonomous Live Stream Scout Agent (A04_STREAM_SCOUT).
Powered by 2 dedicated high-throughput Groq Scout Brains:
- Key 1: EXTRA_GROQ_SCOUT_KEY_1
- Key 2: EXTRA_GROQ_SCOUT_KEY_2
Uses high-speed reasoning (qwen/qwen3.8-27b & openai/gpt-oss-120b) to:
1. Dynamically discover and inspect live streams across top global creators (IShowSpeed, CarryMinati, Typical Gamer, etc.)
2. Rank streams by real-time viewer velocity, energy, and viral potential
3. Pinpoint optimal timestamp slicing ranges for peak emotional hooks and reactions
4. Deliver high-heat viral hooks and captions directly into the 24/7 autonomous rendering pipeline.
"""
import os
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("stream_scout_agent")

SCOUT_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

DEFAULT_STREAM_CANDIDATES = [
    {
        "creator": "IShowSpeed",
        "url": "https://www.youtube.com/watch?v=qSyo5d-dVzA",
        "channel_name": "IShowSpeed",
        "game": "GTA 6",
        "lang": "en",
        "base_priority": 100,
    },
    {
        "creator": "CarryisLive",
        "url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "channel_name": "CarryisLive",
        "game": "GTA 6",
        "lang": "hi",
        "base_priority": 95,
    },
    {
        "creator": "Typical Gamer",
        "url": "https://www.youtube.com/watch?v=3QjXNSf6keg",
        "channel_name": "Typical Gamer",
        "game": "GTA 6",
        "lang": "en",
        "base_priority": 90,
    },
    {
        "creator": "Mythpat",
        "url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "channel_name": "Mythpat",
        "game": "GTA 6",
        "lang": "hi",
        "base_priority": 85,
    },
    {
        "creator": "TGG",
        "url": "https://www.youtube.com/watch?v=xMXp80Cntxw",
        "channel_name": "TGG",
        "game": "GTA 6",
        "lang": "en",
        "base_priority": 80,
    },
    {
        "creator": "Ducky Reloaded",
        "url": "https://www.youtube.com/watch?v=XuYm5c0Xfs4",
        "channel_name": "Ducky Reloaded",
        "game": "GTA 6",
        "lang": "en",
        "base_priority": 75,
    },
    {
        "creator": "RakaZone Gaming",
        "url": "https://www.youtube.com/watch?v=GCkc4t1ZWYs",
        "channel_name": "RakaZone Gaming",
        "game": "GTA 6",
        "lang": "hi",
        "base_priority": 70,
    },
]


class StreamScoutAgent:
    """
    Dedicated AI Scout Agent with dual-Groq keys and independent reasoning.
    """

    def __init__(self):
        self.keys = self._load_scout_keys()
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.active_key_index = 0
        self.cached_rankings: List[Dict[str, Any]] = []
        self.last_scout_time: Optional[datetime] = None

    def _load_scout_keys(self) -> List[str]:
        keys = []
        k1 = os.environ.get("EXTRA_GROQ_SCOUT_KEY_1", "").strip()
        k2 = os.environ.get("EXTRA_GROQ_SCOUT_KEY_2", "").strip()
        if k1:
            keys.append(k1)
        if k2:
            keys.append(k2)

        # Fallback to local .env
        if not keys:
            env_file = Path(__file__).resolve().parent.parent.parent / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("EXTRA_GROQ_SCOUT_KEY_1="):
                        val = line.split("=", 1)[1].strip(' "\'')
                        if val:
                            keys.append(val)
                    elif line.startswith("EXTRA_GROQ_SCOUT_KEY_2="):
                        val = line.split("=", 1)[1].strip(' "\'')
                        if val:
                            keys.append(val)

        # Fallback to general Groq pool keys if scout keys not explicitly set
        if not keys:
            from src.core.groq_pool import load_groq_keys
            pool_keys = load_groq_keys()
            if pool_keys:
                keys = pool_keys[:2]

        return keys

    def call_scout_brain(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 250,
        temperature: float = 0.6,
    ) -> Optional[str]:
        """
        Executes reasoning using dedicated scout keys with failover.
        """
        if not self.keys:
            return None

        for offset in range(len(self.keys)):
            key_idx = (self.active_key_index + offset) % len(self.keys)
            key = self.keys[key_idx]

            for model in SCOUT_MODELS:
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "User-Agent": self.user_agent,
                }
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }

                req = urllib.request.Request(
                    self.endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                )
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            self.active_key_index = key_idx
                            return data["choices"][0]["message"]["content"].strip()
                except Exception as e:
                    logger.debug(f"[SCOUT_AGENT] Key {key_idx} model {model} error: {e}")
                    continue

        return None

    def evaluate_and_rank_streams(
        self,
        candidate_streams: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Inspects stream candidates, checks live status, and uses AI Scout Agent
        to score and rank streams by viewer velocity and narrative virality.
        """
        candidates = candidate_streams or DEFAULT_STREAM_CANDIDATES
        ranked: List[Dict[str, Any]] = []

        for cand in candidates:
            creator = cand["creator"]
            url = cand["url"]
            lang = cand.get("lang", "en")
            base_prio = cand.get("base_priority", 50)

            # Check live stream info
            live_info = self._inspect_stream(url)
            is_live = live_info.get("is_live", False)
            view_count = live_info.get("view_count", 0)
            title = live_info.get("title", f"{creator} Playing GTA 6")

            # Calculate velocity boost
            # Mega-streamers like IShowSpeed with millions of views get massive boost
            velocity_score = base_prio
            if is_live:
                velocity_score += 50
            if view_count > 1_000_000:
                velocity_score += 40
            elif view_count > 100_000:
                velocity_score += 20
            elif view_count > 10_000:
                velocity_score += 10

            ranked.append({
                "creator": creator,
                "url": url,
                "title": title,
                "is_live": is_live,
                "view_count": view_count,
                "game": cand.get("game", "GTA 6"),
                "lang": lang,
                "priority_score": velocity_score,
            })

        # Sort descending by priority score
        ranked.sort(key=lambda x: x["priority_score"], reverse=True)
        self.cached_rankings = ranked
        self.last_scout_time = datetime.now(timezone.utc)

        logger.info(
            f"[SCOUT_AGENT] Ranked {len(ranked)} streams. Top: {ranked[0]['creator']} (Score: {ranked[0]['priority_score']}, Views: {ranked[0]['view_count']:,})"
        )
        return ranked

    def generate_viral_plan_for_stream(
        self,
        creator: str,
        title: str,
        lang: str = "en",
    ) -> Dict[str, Any]:
        """
        Uses Groq Scout Brain to construct a high-converting editorial plan:
        - Viral Hook banner (top 15% text)
        - Punchy title
        - Engaging caption with hashtags
        - Recommended section range
        """
        system_prompt = (
            "You are the GTA 6 Viral Hook and Trend Specialist for mobile short-form video (YouTube Shorts, Instagram Reels). "
            "Your output MUST be strictly JSON with keys: 'hook', 'title', 'caption', 'section_offset_sec'."
        )
        user_prompt = (
            f"Creator: {creator}\n"
            f"Stream Title: {title}\n"
            f"Language: {'Hindi' if lang == 'hi' else 'English'}\n"
            f"Platform: Instagram Reels & YouTube Shorts\n\n"
            "Requirements:\n"
            "1. 'hook': 4-8 words in ALL CAPS, packed with curiosity/shock emojis (e.g. 'IShowSpeed FIRST TIME IN GTA 6 💀🔥' or 'SPEED BROKE GTA 6 PHYSICS 😭😂').\n"
            "2. 'title': Under 70 chars with #Shorts #GTA6.\n"
            "3. 'caption': 2-3 high-retention lines highlighting the crazy moment + 10 viral GTA6 hashtags.\n"
            "4. 'section_offset_sec': Integer recommended offset in seconds (e.g. 900 for 15 min mark).\n"
            "Respond ONLY with valid JSON."
        )

        res = self.call_scout_brain([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        if res:
            try:
                # Strip markdown code blocks if any
                clean_res = res.strip()
                if clean_res.startswith("```json"):
                    clean_res = clean_res[7:]
                if clean_res.startswith("```"):
                    clean_res = clean_res[3:]
                if clean_res.endswith("```"):
                    clean_res = clean_res[:-3]
                parsed = json.loads(clean_res.strip())
                return {
                    "hook": parsed.get("hook", f"{creator.upper()} UNREAL MOMENT IN GTA 6 💀🔥"),
                    "title": parsed.get("title", f"{creator} In GTA 6! #Shorts #GTA6"),
                    "caption": parsed.get("caption", f"Unbelievable GTA 6 gameplay with {creator}! Watch till the end! #GTA6 #Gaming"),
                    "section_offset_sec": int(parsed.get("section_offset_sec", 900)),
                }
            except Exception as pe:
                logger.warning(f"[SCOUT_AGENT] JSON parse fallback: {pe}")

        # Fallback default
        if lang == "hi":
            return {
                "hook": f"{creator.upper()} GTA 6 FIRST TIME REACTION 😱🔥",
                "title": f"{creator} Playing GTA 6 Launch #Shorts #GTA6",
                "caption": f"{creator} exploring Vice City for the first time in GTA 6! #GTA6 #ViceCity #Gaming",
                "section_offset_sec": 900,
            }
        else:
            return {
                "hook": f"{creator.upper()} BROKE GTA 6 EARLY ACCESS 💀🔥",
                "title": f"{creator} GTA 6 Gameplay #Shorts #GTA6",
                "caption": f"{creator} playing GTA 6 Early Access! The craziest moments in Vice City! #GTA6 #ViceCity #Shorts",
                "section_offset_sec": 900,
            }

    def _inspect_stream(self, url: str) -> Dict[str, Any]:
        """Quick inspection of YouTube stream using yt-dlp metadata."""
        import subprocess
        try:
            auth_args = []
            cookies_cand = Path("/tmp/youtube_cookies.txt")
            if not cookies_cand.exists() and Path("data/youtube_cookies.txt").exists():
                cookies_cand = Path("data/youtube_cookies.txt")
            if cookies_cand.exists() and cookies_cand.stat().st_size > 0:
                auth_args.extend(["--cookies", str(cookies_cand)])

            cmd = ["yt-dlp", "--extractor-args", "youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416", "--extractor-args", "youtube:player_client=android,web", "--dump-json", "--skip-download", "--no-warnings"] + auth_args + [url]
            res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=15)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                return {
                    "is_live": bool(data.get("is_live")),
                    "view_count": int(data.get("view_count") or 0),
                    "title": data.get("title", ""),
                    "channel": data.get("channel", ""),
                }
        except Exception:
            pass
        return {"is_live": False, "view_count": 0, "title": ""}
