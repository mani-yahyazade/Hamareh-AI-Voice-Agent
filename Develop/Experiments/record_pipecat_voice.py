import asyncio
import pyaudio
import wave
from pipecat.frames.frames import InputAudioRawFrame, StartFrame, EndFrame, CancelFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.local.audio import (
    LocalAudioInputTransport,
    LocalAudioTransportParams,
)

# Audio file saver processor
class AudioFileSaver(FrameProcessor):
    def __init__(self, output_filename: str, sample_rate: int = 16000):
        super().__init__()
        self.output_filename = output_filename
        self.sample_rate = sample_rate
        self.audio_frames = []
        self.frame_count = 0
        
    async def process_frame(self, frame, direction):
        # Let parent handle initialization first
        await super().process_frame(frame, direction)
        
        # Collect audio frames
        if isinstance(frame, InputAudioRawFrame):
            self.frame_count += 1
            self.audio_frames.append(frame.audio)
            
            # Print progress every 50 frames (~1 second at 16kHz with 20ms frames)
            if self.frame_count % 50 == 0:
                print(f"📼 Recorded {self.frame_count} frames ({self.frame_count * 0.02:.1f}s)")
        
        # On pipeline end, save the file
        elif isinstance(frame, (EndFrame, CancelFrame)):
            await self._save_audio_file()
        
        # Pass frame downstream
        await self.push_frame(frame, direction)
    
    async def _save_audio_file(self):
        if not self.audio_frames:
            print("⚠️  No audio frames captured!")
            return
        
        print(f"\n💾 Saving {self.frame_count} frames to {self.output_filename}...")
        
        try:
            # Combine all audio data
            audio_data = b''.join(self.audio_frames)
            
            # Write WAV file
            with wave.open(self.output_filename, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            
            duration = self.frame_count * 0.02  # 20ms per frame
            file_size = len(audio_data) / 1024  # KB
            
            print(f"✅ Audio saved successfully!")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   File size: {file_size:.1f} KB")
            print(f"   Sample rate: {self.sample_rate} Hz")
            print(f"   Format: 16-bit mono WAV")
            
        except Exception as e:
            print(f"❌ Error saving audio: {e}")


async def main():
    py_audio = None
    
    try:
        # Initialize PyAudio
        py_audio = pyaudio.PyAudio()
        print("🎤 Initializing microphone recording...")
        print("   Press Ctrl+C to stop recording and save the file\n")
        
        # Create transport parameters
        transport_params = LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=False,
            sample_rate=16000,
        )
        
        # Create audio input transport
        audio_input = LocalAudioInputTransport(
            py_audio,
            transport_params
        )
        
        # Create audio file saver
        file_saver = AudioFileSaver(
            output_filename="recorded_voice.wav",
            sample_rate=16000
        )
        
        # Build the pipeline
        pipeline = Pipeline([
            audio_input,  # Capture from microphone
            file_saver,   # Save to file
        ])
        
        # Create task and runner (FIXED: only pass pipeline)
        task = PipelineTask(pipeline)
        runner = PipelineRunner()
        
        # Queue the start frame
        await task.queue_frame(StartFrame())
        
        # Small delay to let initialization complete
        await asyncio.sleep(0.1)
        
        print("🔴 Recording started! Speak into your microphone...")
        print("   (Press Ctrl+C when done)\n")
        
        # Run the pipeline
        await runner.run(task)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Recording stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if py_audio:
            py_audio.terminate()
            print("🔌 PyAudio terminated")


if __name__ == "__main__":
    asyncio.run(main())
