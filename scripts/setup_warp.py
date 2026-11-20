"""
Setup Cloudflare WARP with wireproxy for 24/7 unlimited residential proxy.
Directly communicates with api.cloudflareclient.com to generate keys, register,
and explicitly PATCH `warp_enabled: true` to ensure outbound traffic flows.
"""
import os
import json
import base64
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

try:
    from cryptography.hazmat.primitives.asymmetric import x25519
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("[WARP_SETUP] cryptography module not installed")
    exit(1)

def setup_warp_profile(conf_path: Path):
    if conf_path.exists() and conf_path.stat().st_size > 100:
        content = conf_path.read_text(encoding="utf-8")
        if "[http]" in content and "PersistentKeepalive" in content and "PrivateKey" in content:
            print(f"[WARP_SETUP] Valid WARP profile already exists at {conf_path}")
            return

    print("[WARP_SETUP] Generating fresh X25519 WireGuard keypair...")
    priv = x25519.X25519PrivateKey.generate()
    pub = priv.public_key()
    priv_b64 = base64.b64encode(priv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())).decode()
    pub_b64 = base64.b64encode(pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()

    url = "https://api.cloudflareclient.com/v0a2158/reg"
    headers = {
        "CF-Client-Version": "a-6.3-2288",
        "Host": "api.cloudflareclient.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "identity",
        "User-Agent": "okhttp/3.12.1",
        "Content-Type": "application/json; charset=UTF-8",
    }
    payload = {
        "install_id": "",
        "tos": datetime.now(timezone.utc).isoformat(),
        "key": pub_b64,
        "fcm_token": "",
        "type": "Android",
        "locale": "en_US",
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode())
            reg_id = res["id"]
            token = res["token"]
            print(f"[WARP_SETUP] Registered device ID: {reg_id}")
    except Exception as e:
        print(f"[WARP_SETUP] Device registration failed: {e}")
        return

    # Critical Step: Enable WARP on Cloudflare's backend
    patch_url = f"https://api.cloudflareclient.com/v0a2158/reg/{reg_id}"
    patch_headers = dict(headers)
    patch_headers["Authorization"] = f"Bearer {token}"
    req_patch = urllib.request.Request(patch_url, data=json.dumps({"warp_enabled": True}).encode(), headers=patch_headers, method="PATCH")
    try:
        with urllib.request.urlopen(req_patch, timeout=15) as resp2:
            res2 = json.loads(resp2.read().decode())
            is_enabled = res2.get("warp_enabled", False)
            print(f"[WARP_SETUP] Cloudflare WARP enabled status: {is_enabled}")
    except Exception as pe:
        print(f"[WARP_SETUP] Failed to patch warp_enabled: {pe}")

    peer_info = res.get("config", {}).get("peers", [{}])[0]
    peer_pub = peer_info.get("public_key", "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=")

    conf = f"""[Interface]
PrivateKey = {priv_b64}
Address = 172.16.0.2/32
DNS = 1.1.1.1, 8.8.8.8
MTU = 1280

[Peer]
PublicKey = {peer_pub}
Endpoint = 162.159.192.1:2408
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25

[Socks5]
BindAddress = 127.0.0.1:1080

[http]
BindAddress = 127.0.0.1:8080
"""
    conf_path.parent.mkdir(parents=True, exist_ok=True)
    conf_path.write_text(conf, encoding="utf-8")
    print(f"[WARP_SETUP] Successfully generated active WARP WireGuard profile at {conf_path}")

if __name__ == "__main__":
    target = Path("/app/data/warp/wgcf-profile.conf")
    if not target.parent.exists():
        target = Path("data/warp/wgcf-profile.conf")
    setup_warp_profile(target)
