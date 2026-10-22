import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_tts
import isp_overview_script as S

OUT = Path(__file__).resolve().parents[1] / "out" / "overview" / "voice"

async def one(i, sc):
    events = []
    c = edge_tts.Communicate(sc["text"].replace("卷积", "捲积"), S.VOICE, rate=S.RATE, pitch=S.PITCH)
    async for ch in c.stream():
        if ch["type"] == "SentenceBoundary":
            events.append({"offset": ch["offset"] / 1e7, "duration": ch["duration"] / 1e7,
                           "text": ch.get("text", "")})
    p = OUT / f"{i:02d}_{sc['key']}.bounds.json"
    p.write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")
    print(p.name, len(events))

async def main():
    for i, sc in enumerate(S.SCENES, 1):
        for attempt in range(8):
            try:
                await one(i, sc); break
            except Exception as e:
                print("retry", i, attempt + 1, e)
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
