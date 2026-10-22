import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_tts
import anim_script_landscape as S
OUT = Path(__file__).resolve().parents[1] / "out" / "landscape_anim" / "voice"

async def main():
    for i, sc in enumerate(S.SCENES, 1):
        for attempt in range(8):
            try:
                ev = []
                c = edge_tts.Communicate(sc["text"], S.VOICE, rate=S.RATE, pitch=S.PITCH)
                async for ch in c.stream():
                    if ch["type"] == "SentenceBoundary":
                        ev.append({"offset": ch["offset"] / 1e7, "duration": ch["duration"] / 1e7,
                                   "text": ch.get("text", "")})
                p = OUT / f"{i:02d}_{sc['key']}.bounds.json"
                p.write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
                print(p.name, len(ev))
                break
            except Exception as e:
                print("retry", i, attempt + 1, e)
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
