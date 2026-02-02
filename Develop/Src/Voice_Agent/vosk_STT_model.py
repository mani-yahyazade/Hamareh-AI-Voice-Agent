import os
import sys
import json
import queue
import threading
import sounddevice as sd

from dotenv import load_dotenv
from vosk import Model, KaldiRecognizer, SetLogLevel

load_dotenv(override=True)

PERSIAN_VOSK_PATH = r"vosk-model-fa-0.42"
TARGET_SAMPLE_RATE = 16000
CHANNELS = 1

SetLogLevel(-1)

# Load the Vosk model once (slow step done only once)
print("Loading Vosk Persian model once at startup...")
if not os.path.isdir(PERSIAN_VOSK_PATH):
    raise FileNotFoundError(f"Vosk model not found: {PERSIAN_VOSK_PATH}")

PERSIAN_MODEL = Model(PERSIAN_VOSK_PATH)

# Shared queue for audio chunks
audio_queue = queue.Queue()
stop_flag = threading.Event()


def audio_callback(indata, frames, time_info, status):
    """Callback for sounddevice which pushes audio into the queue."""
    if status:
        print(f"[Audio status] {status}", file=sys.stderr)
    audio_queue.put(bytes(indata))


def wait_for_enter(prompt=""):
    """Wait for user to press Enter."""
    try:
        input(prompt)
    except KeyboardInterrupt:
        pass


def transcribe_user_voice(show_partial: bool = False) -> str:
    """
    Starts recording when user presses Enter.
    Stops recording when user presses Enter again.
    Streams audio chunks to Vosk for real-time ASR.
    Returns final transcribed text.
    """
    recognizer = KaldiRecognizer(PERSIAN_MODEL, TARGET_SAMPLE_RATE)
    recognizer.SetWords(True)
    stop_flag.clear()

    print("Press Enter to START recording...")
    wait_for_enter()

    print("Recording... Press Enter again to STOP.")
    listener_thread = threading.Thread(target=wait_for_enter)
    listener_thread.start()

    with sd.RawInputStream(
        samplerate=TARGET_SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=CHANNELS,
        callback=audio_callback
    ):
        while listener_thread.is_alive():
            try:
                data = audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                txt = result.get("text", "").strip()
                if txt:
                    if show_partial:
                        print(f"[Partial] {txt}")

        # After stop, get final result
        final = json.loads(recognizer.FinalResult()).get("text", "").strip()
        return final

# use_sample
# text = transcribe_user_voice(show_partial=True)
# print(text)