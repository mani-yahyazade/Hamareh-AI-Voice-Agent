"""
Gemini 2.5 Preview TTS (Python, google-genai SDK)
- Choose any prebuilt voice (e.g., 'Kore', 'Puck', ...).
- Generates 24kHz, 16-bit, mono audio from the inline PCM returned by the API.
- Saves the final TTS result into a WAV file (no playback).
"""
import os
import wave
from typing import Optional

from google import genai
from google.genai import types 
from dotenv import load_dotenv

load_dotenv()
if not os.environ.get("GEMINI_API_KEY"):
    print("Not found GEMINI_API_KEY in env")
else:
    print("found GEMINI api key")

# -----------------------------
# Config — edit as needed
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
MODEL_ID = "gemini-2.5-flash-preview-tts"   # or: "gemini-2.5-pro-preview-tts"
DEFAULT_VOICE_NAME = "Enceladus"  # default voice

# Output file: final TTS result will be stored here
OUTPUT_WAV = "gemini_tts_output.wav"

# Gemini TTS returns 24kHz, 16-bit PCM mono
WAV_RATE = 24000
WAV_CHANNELS = 1
WAV_SAMPLE_WIDTH = 2  # bytes (16-bit)

# Optional: the 30 prebuilt voice names from Google's docs
PREBUILT_VOICES = [
    "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede",
    "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba",
    "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
    "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi",
    "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat",
]


def save_wav_from_pcm16(filename: str, pcm_bytes: bytes,
                        channels: int = WAV_CHANNELS,
                        rate: int = WAV_RATE,
                        sample_width: int = WAV_SAMPLE_WIDTH) -> None:
    """Wrap raw PCM (S16LE) in a WAV container and save to file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_bytes)


def synthesize_tts(text: str,
                   voice_name: str = DEFAULT_VOICE_NAME,
                   model: str = MODEL_ID) -> bytes:
    """Call Gemini TTS and return raw PCM bytes (no playback, no file yet)."""
    if GEMINI_API_KEY in (None, "", "YOUR_GEMINI_API_KEY"):
        raise RuntimeError("Set GEMINI_API_KEY env var or pass a real key in code.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    resp = client.models.generate_content(
        model=model,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
        ),
    )

    # raw PCM bytes (s16le @ 24kHz)
    pcm_bytes = resp.candidates[0].content.parts[0].inline_data.data
    return pcm_bytes


def tts_to_wav(response: str,
               voice_name: str = DEFAULT_VOICE_NAME,
               output_path: Optional[str] = OUTPUT_WAV) -> str:
    """
    Generate speech from `response` using Gemini TTS with `voice_name`
    and save the result as a WAV file. No audio is played.
    Returns the path of the created WAV file.
    """
    if not output_path:
        raise ValueError("output_path must be provided to save WAV file.")

    print(f"Using model={MODEL_ID}, voice={voice_name}")
    print(f"Generating TTS and saving to WAV file: {output_path}")

    # 1) Get PCM bytes from Gemini
    pcm_bytes = synthesize_tts(
        response,
        voice_name=voice_name,
        model=MODEL_ID,
    )

    # 2) Save directly as WAV
    save_wav_from_pcm16(output_path, pcm_bytes)
    print(f"WAV saved to: {output_path}")

    return output_path


# --- Example usage ---
# if __name__ == "__main__":
#     sample_text = (
#         "سَلام، مَن رَپتور هَستَم، مُدِلِ هُوشِ مَصنُوعیِ پِیش‌رَفتِه."
#     )
#     tts_to_wav(sample_text, voice_name="Callirrhoe", output_path="response.wav")
