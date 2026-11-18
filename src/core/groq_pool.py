"""
Groq Multi-Agent LLM Pool & Key Rotator.
Distributes requests across 4 high-speed Groq API keys with automatic failover,
model fallback, and role specialization (Scout, Hook Writer, Copywriter, Editorial Judge).
"""
import urllib.request
import json
import logging
from typing import List, Dict, Any, Optional

import os
from pathlib import Path

logger = logging.getLogger("groq_pool")


def load_groq_keys() -> List[str]:
    """Loads Groq API keys from environment variables or .env file."""
    keys_env = os.environ.get("GROQ_API_KEYS", "")
    if keys_env:
        return [k.strip() for k in keys_env.split(",") if k.strip()]

    # Fallback to .env in project root
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("GROQ_API_KEYS="):
                val = line.split("=", 1)[1].strip(' "\'')
                return [k.strip() for k in val.split(",") if k.strip()]

    return []


# Dedicated 14-agent-to-key affinity with automatic failover
AGENT_KEY_MAP = {
    "A04_SCOUT": 0,
    "A04_SCOUT_BURST": 1,
    "A05_NARRATIVE_ARCHITECT": 2,
    "A06_HOOK": 3,
    "A06_HOOK_ALT": 4,
    "A07_SUBTITLE_STYLIST": 5,
    "A07_KINETIC_ANIMATOR": 6,
    "A08_COPYWRITER": 7,
    "A08_METADATA_ENGINEER": 8,
    "A08_HASHTAG_SPECIALIST": 9,
    "A09_JUDGE": 10,
    "A09_RUBRIC_AUDITOR": 11,
    "A10_VIRAL_OPTIMIZER": 12,
    "A11_FEEDBACK_LEARNER": 13,
}

PREFERRED_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]


class GroqPool:
    def __init__(self, keys: Optional[List[str]] = None):
        self.keys = keys or load_groq_keys()
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self._user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        agent_role: str = "A06_HOOK",
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> str:
        """
        Executes chat completion with role-affinity key routing and automatic failover.
        """
        start_key_idx = AGENT_KEY_MAP.get(agent_role, 0) % len(self.keys)
        
        # Try preferred key first, then rotate through others on failure
        for offset in range(len(self.keys)):
            k_idx = (start_key_idx + offset) % len(self.keys)
            key = self.keys[k_idx]
            
            for model in PREFERRED_MODELS:
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "User-Agent": self._user_agent,
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
                    method="POST",
                )

                try:
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        content = data["choices"][0]["message"]["content"].strip()
                        if content:
                            return content
                except Exception as e:
                    logger.warning(f"Groq call failed on key {k_idx+1} with model {model}: {e}")
                    continue

        raise RuntimeError("All Groq keys and models failed or timed out.")

    def generate_viral_hook(self, creator_name: str, game: str, context_notes: str = "", agent_role: str = "A06_HOOK") -> str:
        """A06 Agent: Generates ultra-punchy 3-5 word scroll-stopping ASS subtitle hook."""
        system_prompt = (
            "You are an elite short-form video editor for TikTok and Instagram Reels. "
            "Your job is to generate a single 3 to 5 word, ALL-CAPS, high-contrast viral hook text. "
            "Never use punctuation except exclamation marks. Return ONLY the hook text, nothing else."
        )
        user_prompt = (
            f"Creator: {creator_name}\n"
            f"Game: {game}\n"
            f"Context: {context_notes or 'Intense clutch moment with massive streamer reaction'}\n"
            "Generate the viral hook:"
        )
        try:
            res = self.generate_chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                agent_role=agent_role,
                max_tokens=20,
                temperature=0.8,
            )
            # Clean up quotes or markdown
            cleaned = res.replace('"', '').replace("'", "").replace("*", "").strip().upper()
            return cleaned.split("\n")[0][:40]
        except Exception:
            return f"{creator_name.upper()} UNBELIEVABLE PLAY"

    def generate_reels_metadata(self, creator_name: str, game: str, hook: str) -> Dict[str, str]:
        """A08 Agent: Generates high-converting Instagram caption, viral hashtags, and Shorts title."""
        system_prompt = (
            "You are a social media manager for top gaming creators. "
            "Generate an engaging 1-sentence Instagram Reel caption, 5 viral hashtags, and a 50-character YouTube Shorts title. "
            "Respond in JSON format: {\"caption\": \"...\", \"hashtags\": \"...\", \"title\": \"...\"}"
        )
        user_prompt = f"Creator: {creator_name}, Game: {game}, Hook: {hook}"
        try:
            res = self.generate_chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                agent_role="A08_COPYWRITER",
                max_tokens=150,
                temperature=0.7,
            )
            # Find JSON in response
            start = res.find("{")
            end = res.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(res[start:end])
        except Exception:
            pass

        return {
            "title": f"{creator_name} - {hook}",
            "caption": f"Watch {creator_name} pull this off live! Did he really just do that? Drop a comment below.",
            "hashtags": f"#{game.replace(' ', '')} #{creator_name.replace(' ', '')} #GamingClips #GamingMoments #Reels",
        }
