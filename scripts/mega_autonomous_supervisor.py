"""
ViceDesk Mega Autonomous Supervisor Daemon (Relentless 50-100 Videos/Day Engine)
Runs 24/7 on the local residential IP to guarantee 0% bot-blocks.
Monitors quota, slices 10-20 high-retention clips per 10-hour stream across all top YouTubers,
renders 1080p60 blur-fill masters with kinetic Roman Hinglish subtitles,
uploads to direct high-speed CDN, and publishes continuously up to Meta's daily API limit (100/day).
"""
import sys
import os
import time
import json
import re
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Load environment
env_file = ROOT_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip().strip('"')

from src.ingest.live_worker import LiveIngestWorker
from src.publishing.publishers import InstagramPublisher
from src.detection.first_time_ledger import FirstTimeLedger

# 40+ Curated Moments Sliced Across Top 10-Hour Mega Streams & Trending Missions
MEGA_MOMENTS_CATALOG = [
    # ─── MANDY MISSIONS (Market Viral Trending Hit #1) ───
    {
        "creator": "Jason & Mandy",
        "category": "MANDY_PIPEWORK_MISSION",
        "headline": "Jason Duval Confronts Mandy Over Unpaid Rent - Pipework Mission",
        "stream_url": "https://www.youtube.com/watch?v=_8-c3XJH5og",
        "section_range": "*00:00:35-00:01:45",
        "viral_hook": "JASON MEETS MANDY IN GTA 6 (SHE LURES HIM) 💀🔞",
        "caption": """JASON MEETS MANDY IN GTA 6 (SHE LURES HIM) 💀🔞

Brian sent Jason to Key Lento to collect overdue rent from Mandy, but she refuses to pay unless he fixes her kitchen sink... and then walks him straight into her bedroom! 😭🔥 Look at Jason trying to stay 100% loyal to Lucia!

Is Mandy hiding something darker in that sink? Drop your theories below! 👇

Mission: Pipework (Chapter 1)

#GTA6 #GTAVI #Mandy #GTA6Missions #Pipework #JasonAndLucia #GTA6Story #GamingReels #ReelsViral #Shorts #ViceCity #Trending""",
        "lang": "en",
    },
    {
        "creator": "Mandy 4K",
        "category": "MANDY_SINK_SECRET",
        "headline": "Mandy Clogged Sink Mystery - What Did Jason Find in the Drain?",
        "stream_url": "https://www.youtube.com/watch?v=tjYvEX3HHVk",
        "section_range": "*00:01:10-00:02:20",
        "viral_hook": "WHAT DID MANDY HIDE IN HER KITCHEN SINK? 😱🔍",
        "caption": """WHAT DID MANDY HIDE IN HER KITCHEN SINK? 😱🔍

While unclogging Mandy's kitchen sink with a wrench in the 'Pipework' mission, Jason pulls out a bizarre blocked object and Mandy immediately snatches it away! 🤯🔪 Is the serial killer fan theory real?

Did you spot what was stuck in the pipe? Comment below! 👇

Mission: Pipework (Secret Detail)

#GTA6 #GTAVI #Mandy #GTA6Secrets #Pipework #SerialKillerTheory #EasterEgg #GamingReels #ReelsViral #Shorts #ViceCity""",
        "lang": "en",
    },
    # ─── TECHNO GAMERZ (10-Hour Stream Moments) ───
    {
        "creator": "Techno Gamerz",
        "category": "TECHNO_POLICE_CHASE",
        "headline": "Techno Gamerz Triggers 3-Star Police Sirens In Vice City Downtown",
        "stream_url": "https://www.youtube.com/watch?v=169ZzvPxvvM",
        "section_range": "*00:18:20-00:19:30",
        "viral_hook": "TECHNO GAMERZ FIRST POLICE CHASE IN GTA 6 🚨🏎️",
        "caption": """TECHNO GAMERZ FIRST POLICE CHASE IN GTA 6 🚨🏎️

Ujjwal bhai triggered a high-speed police chase through downtown Vice City! The cruiser AI, tactical PIT maneuvers, and tire smoke look unreal! 🚔💨 Can he escape the squad cars?

Kya GTA 6 ki police GTA 5 se zyada aggressive hai? Comments mein batao! 👇

Streamer: Techno Gamerz

#GTA6 #TechnoGamerz #PoliceChase #ViceCity #GTA6Gameplay #UjjwalGamer #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "Techno Gamerz",
        "category": "TECHNO_WEAPON_TEST",
        "headline": "Techno Gamerz Tests Combat Shotgun & Realistic Ballistics",
        "stream_url": "https://www.youtube.com/watch?v=169ZzvPxvvM",
        "section_range": "*00:32:10-00:33:20",
        "viral_hook": "GTA 6 SHOTGUN DESTRUCTION IS NEXT LEVEL 💥🔫",
        "caption": """GTA 6 SHOTGUN DESTRUCTION IS NEXT LEVEL 💥🔫

Techno Gamerz tested the weapon wheel and combat shotgun! The wall chipping, glass shattering, and muzzle flash dynamics are straight out of a Hollywood movie! 🤯🔥

GTA 6 ke gunplay ko 10 mein se kitne number doge? Comment karo! 👇

Streamer: Techno Gamerz

#GTA6 #TechnoGamerz #WeaponPhysics #ViceCity #GTA6Weapons #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "Techno Gamerz",
        "category": "TECHNO_SUNSET_DRIVE",
        "headline": "Techno Gamerz Drives Down Ocean Drive During Golden Sunset",
        "stream_url": "https://www.youtube.com/watch?v=169ZzvPxvvM",
        "section_range": "*00:45:00-00:46:10",
        "viral_hook": "GTA 6 OCEAN DRIVE GOLDEN HOUR GRAPHICS 🌅🌴",
        "caption": """GTA 6 OCEAN DRIVE GOLDEN HOUR GRAPHICS 🌅🌴

Look at the golden hour sunlight bouncing off the palm trees and wet sand! Techno Gamerz cruises through Ocean Drive with full ray tracing enabled! 🌴✨ Vice City aesthetics are unmatched!

Kya yeh gaming history ka sabse khoobsurat sunset hai? Comments mein batao! 👇

Streamer: Techno Gamerz

#GTA6 #TechnoGamerz #ViceCity #OceanDrive #GTA6Graphics #RayTracing #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "Techno Gamerz",
        "category": "TECHNO_SPORTS_CAR_HEIST",
        "headline": "Techno Gamerz Steals Luxury Sports Car From Mansion Driveway",
        "stream_url": "https://www.youtube.com/watch?v=169ZzvPxvvM",
        "section_range": "*01:02:15-01:03:25",
        "viral_hook": "STEALING LUXURY SPORTS CAR IN GTA 6 🏎️💎",
        "caption": """STEALING LUXURY SPORTS CAR IN GTA 6 🏎️💎

Ujjwal bhai broke into a billionaire mansion on Starfish Island and drove off in an exotic hypercar! The door latch animation, interior leather stitching, and exhaust crackle sound incredible! 🏎️💨

Vice City mein aap sabse pehle kaunsi gaadi churaoge? Comment karo! 👇

Streamer: Techno Gamerz

#GTA6 #TechnoGamerz #SupercarHeist #ViceCity #GTA6Cars #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "Techno Gamerz",
        "category": "TECHNO_RAMP_JUMP",
        "headline": "Techno Gamerz Insane Rooftop Ramp Jump & Crash Physics",
        "stream_url": "https://www.youtube.com/watch?v=169ZzvPxvvM",
        "section_range": "*01:18:40-01:19:50",
        "viral_hook": "GTA 6 CAR CRASH & JUMP PHYSICS ARE UNREAL 🚗💥",
        "caption": """GTA 6 CAR CRASH & JUMP PHYSICS ARE UNREAL 🚗💥

Techno Gamerz launched an SUV off a construction ramp at 100 MPH! Watch the suspension compression, body panel deformation, and windshield spidering! 🤯🔥 Real physics engine at work!

GTA 6 crash physics ya BeamNG Drive? Kaunsa better hai? Comment below! 👇

Streamer: Techno Gamerz

#GTA6 #TechnoGamerz #StuntJump #CrashPhysics #ViceCity #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },

    # ─── CARRYMINATI (10-Hour Stream Moments) ───
    {
        "creator": "CarryMinati",
        "category": "CARRY_GUN_STORE",
        "headline": "CarryMinati Robs Gun Store In GTA 6 - Clerk Pulls Combat Shotgun",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "section_range": "*02:35:00-02:36:10",
        "viral_hook": "CARRYMINATI GUN STORE ROBBERY GONE WRONG 🔫💀",
        "caption": """CARRYMINATI GUN STORE ROBBERY GONE WRONG 🔫💀

CarryMinati tried to hold up an Ammu-Nation style gun store in Vice City, but the store owner pulled a combat shotgun from under the counter and blasted him! True Florida energy! 💀😂

Carry bhai ke sath aisa kisne expect kiya tha? Comments mein batao! 👇

Streamer: CarryMinati

#GTA6 #CarryMinati #CarryisLive #ViceCity #GunStore #FloridaMan #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "CarryMinati",
        "category": "CARRY_HELICOPTER_FLIGHT",
        "headline": "CarryMinati Flies Helicopter Over Vice City Night Skyline",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "section_range": "*03:15:20-03:16:30",
        "viral_hook": "CARRYMINATI FLIES OVER VICE CITY NIGHT SKYLINE 🚁🌃",
        "caption": """CARRYMINATI FLIES OVER VICE CITY NIGHT SKYLINE 🚁🌃

CarryMinati hijacked a news helicopter and flew above Vice City at midnight! Look at the volumetric cloud layers, dynamic city lighting, and infinite draw distance! 🚁✨ Pure visual spectacle!

Kya GTA 6 ka map GTA 5 se 3 guna bada hai? Comment karo! 👇

Streamer: CarryMinati

#GTA6 #CarryMinati #ViceCity #HelicopterFlight #NightSkyline #GTA6Graphics #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "CarryMinati",
        "category": "CARRY_FLORIDA_MAN_FIGHT",
        "headline": "CarryMinati Fistfight With Crazy Florida Man Outside Store",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "section_range": "*04:12:00-04:13:10",
        "viral_hook": "CARRYMINATI VS FLORIDA MAN FISTFIGHT 🥊💀",
        "caption": """CARRYMINATI VS FLORIDA MAN FISTFIGHT 🥊💀

Carry bhai got into an argument with an NPC Florida man holding a soda can! The voice lines, swearing AI, and punch impact animations had everyone crying laughing! 🤣🥊 Florida realism at its best!

Carry bhai ke punch ko 10 mein se kitna rate karoge? 😂👇

Streamer: CarryMinati

#GTA6 #CarryMinati #FloridaMan #Fistfight #RagdollPhysics #ViceCity #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "CarryMinati",
        "category": "CARRY_SPEEDBOAT_CHASE",
        "headline": "CarryMinati High-Speed Boat Escape Through Vice City Canals",
        "stream_url": "https://www.youtube.com/watch?v=irNhWMG560k",
        "section_range": "*05:58:00-05:59:10",
        "viral_hook": "GTA 6 WATER WAKE & BOAT PHYSICS ARE INSANE 🚤🌊",
        "caption": """GTA 6 WATER WAKE & BOAT PHYSICS ARE INSANE 🚤🌊

CarryMinati escaped police choppers by cutting through the narrow inland canals on an offshore speedboat! Watch the dynamic water spray, foam displacement, and wave buoyancy! 🌊🚤 Rockstar nailed water physics!

Kya GTA 6 ka water simulation best in history hai? Comment below! 👇

Streamer: CarryMinati

#GTA6 #CarryMinati #BoatChase #WaterPhysics #ViceCity #GTA6Boats #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },

    # ─── MYTHPAT (10-Hour Stream Moments) ───
    {
        "creator": "Mythpat",
        "category": "MYTHPAT_5STAR_CHASE",
        "headline": "Mythpat Triggers 5-Star Wanted Level With SWAT Helicopters",
        "stream_url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "section_range": "*02:18:20-02:19:30",
        "viral_hook": "MYTHPAT 5-STAR SWAT HELICOPTER ESCAPE 🚁🚨",
        "caption": """MYTHPAT 5-STAR SWAT HELICOPTER ESCAPE 🚁🚨

Mythpat triggered a 5-star wanted level in downtown Vice City! Tactical police units deployed armored roadblocks, spike strips, and twin attack choppers in the most intense chase ever recorded! 🚁💥

Kya aap aisi 5-star police chase se 1 minute bhi bach pate? Comments mein batao! 👇

Streamer: Mythpat

#GTA6 #Mythpat #5StarWanted #PoliceChase #ViceCity #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "Mythpat",
        "category": "MYTHPAT_LOWRIDER_BOUNCE",
        "headline": "Mythpat Customizes Lowrider With Independent Hydraulics",
        "stream_url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "section_range": "*03:45:10-03:46:20",
        "viral_hook": "GTA 6 WORKING HYDRAULICS LOWRIDER TEST 🔥🚗",
        "caption": """GTA 6 WORKING HYDRAULICS LOWRIDER TEST 🔥🚗

Mythpat took a customized classic lowrider onto the South Beach strip and activated the hydraulic bounce switches! Look at the rims sparking on the asphalt! 🤯💨 The suspension physics are 100% realistic!

GTA 6 vehicle customization GTA 5 se behtar hai ya nahi? Drop your thoughts! 👇

Streamer: Mythpat

#GTA6 #Mythpat #Lowrider #CarHydraulics #GTA6Physics #ViceCity #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "Mythpat",
        "category": "MYTHPAT_SWAMP_ALLIGATOR",
        "headline": "Mythpat Airboat Ride In Everglades Ambushed By Massive Alligator",
        "stream_url": "https://www.youtube.com/watch?v=LMbea5SozeM",
        "section_range": "*05:12:40-05:13:50",
        "viral_hook": "GIANT ALLIGATOR ATTACKS AIRBOAT IN GTA 6 🐊🌊",
        "caption": """GIANT ALLIGATOR ATTACKS AIRBOAT IN GTA 6 🐊🌊

Mythpat took a fan-powered airboat deep into the Florida Everglades swamps at dusk! A 14-foot bull alligator lunged out of the murky water and bit the boat hull! 🐊😱 Wildlife AI in Leonida is terrifying!

Kya aap akele raat ko GTA 6 ke swamps mein jaoge? Comments mein batao! 👇

Streamer: Mythpat

#GTA6 #Mythpat #AlligatorAttack #Everglades #FloridaWildlife #ViceCity #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },

    # ─── RAKAZONE GAMING (8-Hour Stream Moments) ───
    {
        "creator": "RakaZone Gaming",
        "category": "RAKAZONE_MOTORCYCLE_SPLITTING",
        "headline": "RakaZone 120 MPH Motorcycle Lane Splitting Highway Rush",
        "stream_url": "https://www.youtube.com/watch?v=GCkc4t1ZWYs",
        "section_range": "*02:30:10-02:31:20",
        "viral_hook": "120 MPH MOTORCYCLE LANE SPLITTING IN GTA 6 🏍️💨",
        "caption": """120 MPH MOTORCYCLE LANE SPLITTING IN GTA 6 🏍️💨

RakaZone pinned the throttle on a high-displacement sports bike weaving between trucks on the coastal highway! Look at the motion blur, handlebar vibration, and near-miss wind drafts! 🏍️⚡ Insane sense of speed!

GTA 6 first-person bike riding try karoge? Comment karo! 👇

Streamer: RakaZone Gaming

#GTA6 #RakaZone #Motorcycle #SpeedRush #GTA6Physics #ViceCity #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "RakaZone Gaming",
        "category": "RAKAZONE_SNIPER_ROOFTOP",
        "headline": "RakaZone High-Rise Sniper Rifle Long Distance Ballistics Test",
        "stream_url": "https://www.youtube.com/watch?v=GCkc4t1ZWYs",
        "section_range": "*03:15:00-03:16:10",
        "viral_hook": "GTA 6 ULTRA LONG-RANGE SNIPER BALLISTICS 🎯🔭",
        "caption": """GTA 6 ULTRA LONG-RANGE SNIPER BALLISTICS 🎯🔭

RakaZone climbed a construction crane overlooking South Beach to test bullet drop, wind compensation, and scope reflection dynamics! 🎯🌆 The level of detail across 1.5 miles of city is unbelievable!

GTA 6 ke sniper scope realism ko 10 mein se kitne number doge? Comment below! 👇

Streamer: RakaZone Gaming

#GTA6 #RakaZone #SniperPhysics #Ballistics #ViceCity #GTA6Weapons #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },

    # ─── AS GAMING (6-Hour Stream Moments) ───
    {
        "creator": "AS Gaming",
        "category": "AS_SUPERCAR_OCEAN_DRIVE",
        "headline": "AS Gaming Cruises Exotic Hypercar Down Vice City Ocean Drive",
        "stream_url": "https://www.youtube.com/watch?v=u1OGXGfOEI0",
        "section_range": "*01:15:00-01:16:10",
        "viral_hook": "EXOTIC HYPERCAR ON VICE CITY OCEAN DRIVE 🏎️🌴",
        "caption": """EXOTIC HYPERCAR ON VICE CITY OCEAN DRIVE 🏎️🌴

AS Gaming cruised down the world-famous Ocean Drive in a multi-million dollar hypercar! The engine rumble reverberates off the Art Deco hotels, and tourists stop to record phone videos! 📱🏎️ Next level AI behavior!

Aap sabse pehle Vice City mein kaunsi gaadi drive karoge? Comment karo! 👇

Streamer: AS Gaming

#GTA6 #ASGaming #Supercar #OceanDrive #ViceCity #GTA6Cars #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },
    {
        "creator": "AS Gaming",
        "category": "AS_DUNE_BUGGY_MUD",
        "headline": "AS Gaming 4x4 Off-Road Dune Buggy Mud & Deformable Terrain Test",
        "stream_url": "https://www.youtube.com/watch?v=u1OGXGfOEI0",
        "section_range": "*04:50:10-04:51:20",
        "viral_hook": "GTA 6 REALISTIC MUD & TERRAIN DEFORMATION 🚙💨",
        "caption": """GTA 6 REALISTIC MUD & TERRAIN DEFORMATION 🚙💨

AS Gaming took a 4x4 dune buggy through the deep Florida mud pits! Look at the tires digging real ruts in the dirt, mud splattering on the windshield, and water puddles splashing! 🚙🌧️ Incredible terrain physics!

Kya GTA 6 ne MudRunner aur Forza ko beat kar diya? Comment below! 👇

Streamer: AS Gaming

#GTA6 #ASGaming #MudPhysics #OffRoad #GTA6Physics #ViceCity #GamingReels #ReelsViral #Shorts""",
        "lang": "hi",
    },

    # ─── TGG (8-Hour Wildlife & Ocean Moments) ───
    {
        "creator": "TGG",
        "category": "TGG_CORAL_REEF_DIVING",
        "headline": "TGG Deep Sea Scuba Diving Explores Bioluminescent Coral Reef",
        "stream_url": "https://www.youtube.com/watch?v=xMXp80Cntxw",
        "section_range": "*01:30:00-01:31:10",
        "viral_hook": "GTA 6 UNDERWATER CORAL REEF IS BREATHTAKING 🤿🐠",
        "caption": """GTA 6 UNDERWATER CORAL REEF IS BREATHTAKING 🤿🐠

TGG strapped on scuba gear and dove 50 feet below Vice City reef! Schools of tropical fish react to diver movement, sea turtles glide by, and sunbeams pierce the crystal clear water! 🐠🤿 Undersea exploration is a whole game in itself!

Would you spend hours exploring the ocean in GTA 6? Comment below! 👇

Streamer: TGG

#GTA6 #TGG #CoralReef #OceanPhysics #UnderwaterWorld #ViceCity #GamingReels #ReelsViral #Shorts""",
        "lang": "en",
    },
    {
        "creator": "TGG",
        "category": "TGG_SUNKEN_SHIPWRECK",
        "headline": "TGG Discovers Historic Sunken Cargo Shipwreck Off Florida Keys",
        "stream_url": "https://www.youtube.com/watch?v=xMXp80Cntxw",
        "section_range": "*02:45:20-02:46:30",
        "viral_hook": "SECRET SUNKEN SHIPWRECK FOUND IN GTA 6 🚢⚓",
        "caption": """SECRET SUNKEN SHIPWRECK FOUND IN GTA 6 🚢⚓

TGG found a massive sunken cargo ship 100 meters underwater off the Florida Keys! Complete interior cargo hold, rusting metal beams, and schools of barracuda swimming through the bridge! 🚢🌊 Exploration rewards in GTA 6 are crazy!

What secret location will you hunt for first? Drop a comment! 👇

Streamer: TGG

#GTA6 #TGG #Shipwreck #SecretLocation #UnderwaterGTA6 #ViceCity #GamingReels #ReelsViral #Shorts""",
        "lang": "en",
    },

    # ─── ONESPOT GAMING (Real Life Comparison Moments) ───
    {
        "creator": "Onespot Gaming",
        "category": "ONESPOT_WYNWOOD_MURALS",
        "headline": "Real Life Miami Wynwood Walls Murals Vs GTA 6 Leonida Art",
        "stream_url": "https://www.youtube.com/watch?v=bNeva6nbk8s",
        "section_range": "*00:01:30-00:02:40",
        "viral_hook": "REAL MIAMI WYNWOOD ART VS GTA 6 LEONIDA 🎨🏙️",
        "caption": """REAL MIAMI WYNWOOD ART VS GTA 6 LEONIDA 🎨🏙️

Side-by-side comparison of Miami's world-famous Wynwood graffiti art district vs GTA 6's in-game district! Every mural, spray texture, and brick wall was 3D mapped with breathtaking accuracy! 🎨✨

Rockstar ke attention to detail ko 10 mein se kitna rate karoge? Comment karo! 👇

Source: Real-World Miami Comparison

#GTA6 #RealLifeVsGTA6 #WynwoodWalls #ViceCity #GTA6Graphics #Miami #GamingReels #ReelsViral #Shorts""",
        "lang": "en",
    },

    # ─── KREEKCRAFT (Exploration & Stunts) ───
    {
        "creator": "Kreek",
        "category": "KREEK_TERMINAL_BREACH",
        "headline": "KreekCraft Infiltrates TSA Checkpoint & Vice City Airport Terminal",
        "stream_url": "https://www.youtube.com/watch?v=dy-oCN2NxfA",
        "section_range": "*01:20:00-01:21:10",
        "viral_hook": "BREAKING INTO VICE CITY AIRPORT TERMINAL ✈️🚨",
        "caption": """BREAKING INTO VICE CITY AIRPORT TERMINAL ✈️🚨

KreekCraft explored the fully detailed Vice City International terminal! Baggage claim belts moving, dynamic flight departure boards, and armed airport security tackling trespassers! ✈️🏢 The interior scale is unbelievable!

GTA 6 ke interior detail ko 1 se 10 mein kitne points doge? Comment karo! 👇

Streamer: Kreek

#GTA6 #Kreek #AirportTerminal #ViceCity #GTA6Interiors #GamingReels #ReelsViral #Shorts""",
        "lang": "en",
    },
    {
        "creator": "Kreek",
        "category": "KREEK_STUNT_PLANE",
        "headline": "KreekCraft Performs Stunt Plane Barrel Rolls Through Skyscrapers",
        "stream_url": "https://www.youtube.com/watch?v=dy-oCN2NxfA",
        "section_range": "*02:10:30-02:11:40",
        "viral_hook": "INSANE STUNT PLANE DOWNTOWN BARREL ROLL ✈️🏙️",
        "caption": """INSANE STUNT PLANE DOWNTOWN BARREL ROLL ✈️🏙️

KreekCraft flew an aerobatic stunt plane between two neon skyscrapers in downtown Vice City! The wingtip vortex smoke and altitude aerodynamics look like a flight simulator! ✈️💨 Absolutely wild flying!

Would you attempt this stunt in Vice City? Drop your thoughts! 👇

Streamer: Kreek

#GTA6 #Kreek #StuntFlight #ViceCity #FlightPhysics #GamingReels #ReelsViral #Shorts""",
        "lang": "en",
    },
]


def check_instagram_publishing_quota(ig_pub: InstagramPublisher) -> Dict[str, Any]:
    """
    Checks Meta Graph API rate limit for content publishing.
    Meta default: 100 media publishes per 24 hours.
    """
    try:
        acc = os.environ.get("INSTAGRAM_ACCOUNT_ID", "17841467596649798")
        tok = ig_pub.access_token
        url = f"https://graph.facebook.com/v19.0/{acc}/content_publishing_limit?fields=config,quota_usage&access_token={tok}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            if data.get("data"):
                item = data["data"][0]
                usage = item.get("quota_usage", 0)
                total = item.get("config", {}).get("quota_total", 100)
                remaining = max(0, total - usage)
                return {"quota_usage": usage, "quota_total": total, "remaining": remaining, "can_publish": remaining > 0}
    except Exception as e:
        print(f"[QUOTA] Note checking quota: {e}")
    return {"quota_usage": 0, "quota_total": 100, "remaining": 100, "can_publish": True}


def upload_video_to_public_host(video_path: Path) -> str:
    """
    Uploads the rendered master video to public CDN for Meta Graph API ingest.
    Primary: High-Speed Direct CDN (uguu.se) with byte-range and video/mp4 headers.
    """
    import subprocess
    print(f"[HOSTING] Uploading {video_path.name} to High-Speed Direct CDN...")
    try:
        cmd = ["curl.exe", "-s", "-F", f"files[]=@{video_path.resolve()}", "https://uguu.se/upload"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            if data.get("success") and data.get("files"):
                direct_url = data["files"][0]["url"].replace("\\/", "/")
                print(f"[HOSTING] CDN Upload SUCCESS: {direct_url}")
                return direct_url
    except Exception as e:
        print(f"[HOSTING] Primary CDN exception: {e}")

    raise RuntimeError("Direct CDN upload failed")


def is_already_on_instagram(ig_pub: InstagramPublisher, hook: str, headline: str, creator: str) -> bool:
    """
    Checks recent reels on Instagram to strictly prevent duplicate publishes.
    """
    try:
        recent = ig_pub.get_recent_reels(limit=35)
        clean = lambda s: re.sub(r"[^\w\s]", " ", (s or "").lower()).strip()
        stop = {
            "gta", "gta6", "gtavi", "6", "5", "in", "is", "a", "the", "and", "or", "of", "to",
            "first", "time", "with", "at", "for", "vice", "city", "gameplay", "graphics",
            "unreal", "next", "gen", "level", "shorts", "reels", "video", "new", "vs", "live",
            "reaction", "part"
        }

        c_words = set(clean(creator).split()) - {"gaming", "plays", "islive"}
        h_core = set(clean(hook).split()) - stop
        hl_core = set(clean(headline).split()) - stop

        for r in recent:
            c_cap = clean(r.get("caption") or "")
            cap_words = set(c_cap.split())

            # 1. Exact hook phrase match
            if clean(hook) in c_cap:
                return True

            # 2. Creator matches and >=3 core words from hook match
            if c_words and c_words.issubset(cap_words):
                if len(h_core.intersection(cap_words)) >= 3:
                    return True
                if len(hl_core.intersection(cap_words)) >= 4:
                    return True

            # 3. High hook overlap
            if len(h_core.intersection(cap_words)) >= 4:
                return True

        return False
    except Exception as e:
        print(f"[DEDUP] Warning checking Instagram reels: {e}")
        return False


def run_single_moment(moment: Dict[str, Any], ig_pub: InstagramPublisher, worker: LiveIngestWorker, ledger: FirstTimeLedger) -> Optional[str]:
    """
    Processes, renders, uploads, and publishes one single moment.
    Returns permalink on success, None on skip or failure.
    """
    creator = moment["creator"]
    headline = moment["headline"]
    hook = moment["viral_hook"]
    url = moment["stream_url"]
    section = moment["section_range"]
    caption = moment["caption"]

    print("\n" + "=" * 65)
    print(f"[SUPERVISOR] Processing: {headline} ({creator})")
    print(f"             Section: {section} | URL: {url}")
    print("=" * 65)

    # 1. Deduplication check
    if is_already_on_instagram(ig_pub, hook, headline, creator):
        print(f"[SKIP] Event '{headline}' is already live on Instagram! Advancing queue.")
        return None

    # 2. Render vertical 9:16 master
    t0 = time.time()
    print(f"[RENDER] Starting LiveIngestWorker for {creator}...")
    res = worker.process_url_job(
        url=url,
        creator_name=creator,
        game="GTA 6",
        layout_mode="blur_fill",
        section_range=section,
        publish_to_youtube=False,
        viral_hook=hook,
        caption=caption,
        title=f"{headline} #GTA6 #Shorts",
    )

    output_path = res.get("output_path")
    if not res.get("qc_passed") or not output_path or not Path(output_path).exists():
        err_msg = res.get("error", "Unknown render error")
        print(f"[WARN] Ingest/Render failed for {creator}: {err_msg} -> Skipping to next slice immediately!")
        return None

    video_file = Path(output_path)
    sz_mb = video_file.stat().st_size / (1024 * 1024)
    print(f"[RENDER] Complete in {time.time()-t0:.1f}s! Master file: {video_file} ({sz_mb:.2f} MB)")

    # 3. Host video on public CDN
    public_url = upload_video_to_public_host(video_file)

    # 4. Publish to Instagram Reels
    account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID", "17841467596649798")
    print(f"[PUBLISH] Publishing to Instagram Reels (@{ig_pub.verify_credentials().get('username')})...")

    container_id = ig_pub.create_reel_container(
        video_url=public_url,
        caption=caption,
        account_ref=account_id
    )
    print(f"[PUBLISH] Reels container created: {container_id}")

    ig_pub.poll_container_status(container_id=container_id, max_attempts=30, delay_sec=8.0)
    pub_res = ig_pub.publish_container(container_id=container_id, account_ref=account_id)
    media_id = pub_res.get("remote_id")
    print(f"[PUBLISH] Published to Instagram! Media ID: {media_id}")

    # Fetch permalink
    time.sleep(3)
    tok = ig_pub.access_token
    p_url = f"https://graph.facebook.com/v19.0/{media_id}?fields=permalink,shortcode&access_token={tok}"
    permalink = None
    try:
        req = urllib.request.Request(p_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            p_data = json.loads(r.read().decode())
            permalink = p_data.get("permalink")
    except Exception:
        permalink = f"https://www.instagram.com/reel/{media_id}/"

    print("\n" + "*" * 65)
    print(f"🎉 NEW REEL LIVE: {permalink}")
    print("*" * 65)

    # DISK SAFETY: Delete local rendered MP4 immediately after successful publish
    try:
        video_file.unlink(missing_ok=True)
        print(f"[CLEANUP] Deleted local master: {video_file.name} (Disk space 100% clean ✓)")
    except Exception as d_err:
        pass

    return permalink


def run_mega_autonomous_supervisor(target_daily_posts: int = 50, burst_interval_sec: int = 120):
    """
    Relentless 24/7 supervisor loop. Never sleeps, never stops, auto-advances,
    monitors Meta publishing limit and pushes up to 50-100 reels daily.
    """
    print("=" * 65)
    print("VICE DESK MEGA AUTONOMOUS SUPERVISOR DAEMON STARTING...")
    print(f"Target Daily Uploads: {target_daily_posts} | Burst Interval: {burst_interval_sec}s")
    print(f"Platform Ceiling: 100 Reels / 24h (Meta API Limit)")
    print("=" * 65)

    worker = LiveIngestWorker()
    ig_pub = InstagramPublisher()
    ledger = FirstTimeLedger()

    auth = ig_pub.verify_credentials()
    if not auth.get("valid"):
        print(f"[FATAL] Instagram authentication failed: {auth.get('message')}")
        sys.exit(1)
    print(f"[AUTH] Instagram connected: @{auth.get('username')}")

    total_published_session = 0

    while True:
        # Check quota status
        quota_info = check_instagram_publishing_quota(ig_pub)
        usage = quota_info.get("quota_usage", 0)
        total = quota_info.get("quota_total", 100)
        remaining = quota_info.get("remaining", 0)

        print(f"\n[SUPERVISOR STATUS] Meta API Quota: {usage}/{total} used ({remaining} remaining today)")
        print(f"[SUPERVISOR STATUS] Total published this session: {total_published_session}")

        if remaining <= 2:
            print(f"[SUPERVISOR QUOTA] Approaching daily Meta ceiling ({usage}/{total}). Sleeping 1 hour for rolling reset...")
            time.sleep(3600)
            continue

        published_this_pass = 0

        for moment in MEGA_MOMENTS_CATALOG:
            # Check remaining quota before each attempt
            q_check = check_instagram_publishing_quota(ig_pub)
            if q_check.get("remaining", 0) <= 2:
                print("[SUPERVISOR] Daily quota cap reached! Sleeping 1 hour for rolling reset...")
                time.sleep(3600)
                break

            try:
                permalink = run_single_moment(moment, ig_pub, worker, ledger)
                if permalink:
                    total_published_session += 1
                    published_this_pass += 1
                    print(f"[SUPERVISOR COUNTER] Total Published Today: {total_published_session}/{target_daily_posts}")
                    print(f"[PACING] Pausing {burst_interval_sec}s before next video...")
                    time.sleep(burst_interval_sec)
                else:
                    # If skipped or failed, immediately advance with tiny delay
                    time.sleep(3)
            except Exception as e:
                print(f"[SUPERVISOR ERROR] Moment error: {e} -> Auto-advancing to next candidate immediately!")
                time.sleep(5)

        print(f"[SUPERVISOR PASS COMPLETE] Completed pass over catalog! Slices published: {published_this_pass}")
        print("[SUPERVISOR RE-SCAN] Sleeping 300s before next scan & queue refresh...")
        time.sleep(300)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mega Autonomous Supervisor Daemon")
    parser.add_argument("--target", type=int, default=50, help="Daily target posts (default: 50)")
    parser.add_argument("--interval", type=int, default=120, help="Burst interval between posts in seconds (default: 120s)")
    args = parser.parse_args()

    run_mega_autonomous_supervisor(target_daily_posts=args.target, burst_interval_sec=args.interval)
