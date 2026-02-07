import asyncio
import pyaudio
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.local.audio import (
    LocalAudioInputTransport,
    LocalAudioTransportParams
)
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.frames.frames import AudioRawFrame, StartFrame, InputAudioRawFrame

# ============================================
# Custom Frame Logger
# ============================================
class AudioFrameLogger(FrameProcessor):
    """Logs every AudioRawFrame that passes through"""
    
    def __init__(self):
        super().__init__()
        self.frame_count = 0
    
    async def process_frame(self, frame, direction):
        # CRITICAL: Call parent first to handle StartFrame initialization
        await super().process_frame(frame, direction)
        
        # Log audio frames (only after StartFrame has been processed by parent)
        if isinstance(frame, InputAudioRawFrame):
            self.frame_count += 1
            if self.frame_count % 50 == 0:
                print(f"✅ Frame #{self.frame_count} | size: {len(frame.audio)} bytes | rate: {frame.sample_rate}Hz")
        
        # Always pass frames downstream
        await self.push_frame(frame, direction)

# ============================================
# Main Pipeline
# ============================================
async def main():
    py_audio = pyaudio.PyAudio()
    
    audio_params = LocalAudioTransportParams(
        audio_in_enabled=True,
        audio_out_enabled=False,
        rate=16000,
        channels=1,
        format=pyaudio.paInt16
    )
    
    audio_input = LocalAudioInputTransport(py_audio, params=audio_params)
    logger = AudioFrameLogger()
    pipeline = Pipeline([audio_input, logger])
    
    # PipelineParams contains StartFrame configuration
    params = PipelineParams(
        audio_in_sample_rate=16000,
        audio_out_sample_rate=16000
    )
    
    task = PipelineTask(pipeline, params=params)
    runner = PipelineRunner()
    
    print("🎤 Initializing pipeline...")
    print("=" * 50)
    
    try:
        # The runner automatically sends StartFrame with params to the pipeline
        await runner.run(task)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping recording...")
    finally:
        py_audio.terminate()
        print(f"\n✅ Recording stopped - Total frames: {logger.frame_count}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
