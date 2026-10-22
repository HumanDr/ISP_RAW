import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_tts
import anim_script as S

OUT = Path(__file__).resolve().parents[1] / "out" / "anim" / "voice"
OUT.mkdir(parents=True, exist_ok=True)

async def one(i, sc):
    mp3 = OUT / f"{i:02d}_{sc['key']}.mp3"
    txt = OUT / f"{i:02d}_{sc['key']}.txt"
    sig = f"{S.VOICE}|{S.RATE}|{S.PITCH}\n{sc['text']}"
    if mp3.exists() and txt.exists() and txt.read_text(encoding="utf-8") == sig:
        return mp3
    for attempt in range(8):
        try:
            await edge_tts.Communicate(sc["text"], S.VOICE, rate=S.RATE,
                                       pitch=S.PITCH).save(str(mp3))
            txt.write_text(sig, encoding="utf-8")
            print("tts", mp3.name, "ok")
            return mp3
        except Exception as e:
            print("tts retry", i, attempt + 1, e)
            await asyncio.sleep(3)
    raise RuntimeError(f"TTS failed: {mp3}")

async def main():
    for i, sc in enumerate(S.SCENES, 1):
        await one(i, sc)

if __name__ == "__main__":
    asyncio.run(main())
