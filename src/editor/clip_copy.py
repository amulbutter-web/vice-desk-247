"""Write the opening hook and post copy from cues inside the selected edit."""


def clip_copy(creator, game, window, cuts, peak_ms):
    start, end = window["window_start_ms"], window["window_end_ms"]
    hindi = creator.casefold() in {"carryislive", "carryminati", "mythpat", "gamerfleet", "techno gamerz", "two-side gamers", "dattrax plays", "rakazone gaming", "as gaming", "8bit goldy"}
    cut = next((t for t in cuts if start + 1000 <= t < end - 1000), None)
    if cut is not None:
        sec = (cut - start) // 1000
        hook = f"{sec}s par nazar rakhna" if hindi else f"Keep an eye on {sec}s"
        caption = f"{creator} ke clip mein {sec}s par scene badalta hai. Pehli baar mein kya notice kiya?" if hindi else f"The scene changes {sec}s into {creator}'s clip. What caught your eye first?"
    elif peak_ms is not None and start <= peak_ms < end:
        sec = (peak_ms - start) // 1000
        hook = f"{sec}s par sunna" if hindi else f"Listen at {sec}s"
        caption = f"{creator} ke clip mein {sec}s par audio peak hai. Headphones mein kya sunai diya?" if hindi else f"Listen at {sec}s in {creator}'s clip. What can you pick out in the mix?"
    else:
        hook = "Tumhara agla move?" if hindi else "Your next move?"
        caption = f"{creator} ka POV. Controller tumhare haath mein hota toh agla move kya hota?" if hindi else f"You're holding the controller. What's your next move in {creator}'s place?"
    hashtag = "#GTA6" if game.casefold().replace(" ", "") in {"gta6", "gtavi"} else "#Gaming"
    return {"title": f"{creator[:45]} | {hook} #Shorts", "hook": hook, "caption": caption, "hashtags": hashtag}
