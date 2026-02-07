# Just starts, but doesn't do anything else
import asyncio
import os
from dotenv import load_dotenv
import pyaudio

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask

from pipecat.transports.local.audio import (
    LocalAudioInputTransport,
    LocalAudioOutputTransport,
    LocalAudioTransportParams,
)

from pipecat.frames.frames import EndFrame

from pipecat.services.google.stt import GoogleSTTService
from pipecat.services.google.tts import GoogleTTSService
from pipecat.services.google.llm import GoogleLLMService


load_dotenv()


async def main():
    # ✅ Create PyAudio instance
    py_audio = pyaudio.PyAudio()
    
    # ✅ Audio parameters
    audio_params = LocalAudioTransportParams(
        audio_in_sample_rate=16000,
        audio_out_sample_rate=16000,
    )

    # ✅ Pass py_audio as positional argument
    audio_input = LocalAudioInputTransport(py_audio, params=audio_params)
    audio_output = LocalAudioOutputTransport(py_audio, params=audio_params)

    stt = GoogleSTTService(
        credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
        language="en-US",
        sample_rate=16000,
    )

    llm = GoogleLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.0-flash-exp",
        system_instruction="You are a concise, helpful voice assistant.",
    )

    tts = GoogleTTSService(
        credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        language="en-US",
        voice_id="en-US-Journey-D",
        sample_rate=16000,
    )

    pipeline = Pipeline(
        [
            audio_input,
            stt,
            llm,
            tts,
            audio_output,
        ]
    )

    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    print("🎙️ Continuous listening active")
    print("🗣️ Silence (~1.5s) triggers response")
    print("🛑 Ctrl+C to stop\n")

    try:
        await runner.run(task)
    except KeyboardInterrupt:
        await task.queue_frame(EndFrame())
    finally:
        await runner.stop()
        py_audio.terminate()  # ✅ Clean up PyAudio
        print("✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())


