import asyncio
import pyaudio
import wave
import numpy as np
from pipecat.frames.frames import InputAudioRawFrame, StartFrame, EndFrame, CancelFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.local.audio import (
    LocalAudioInputTransport,
    LocalAudioTransportParams,
)


# Voice Activity Detector - Only alerts for amplitude > 2000
class VoiceActivityDetector(FrameProcessor):
    def __init__(self, threshold: float = 2000, cooldown_frames: int = 25):
        super().__init__()
        self.threshold = threshold
        self.cooldown_frames = cooldown_frames
        self.frames_since_alert = cooldown_frames
        self.is_speaking = False
        
    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, InputAudioRawFrame):
            try:
                audio_array = np.frombuffer(frame.audio, dtype=np.int16)
                
                if len(audio_array) == 0:
                    await self.push_frame(frame, direction)
                    return
                
                audio_float = audio_array.astype(np.float64)
                rms = np.sqrt(np.mean(audio_float ** 2))
                
                if not np.isfinite(rms):
                    rms = 0.0
                
                # Only alert when amplitude > 2000
                if rms > self.threshold:
                    if self.frames_since_alert >= self.cooldown_frames:
                        if not self.is_speaking:
                            print(f"\n🎤 LOUD VOICE DETECTED! (amplitude: {rms:.1f})")
                            self.is_speaking = True
                        self.frames_since_alert = 0
                else:
                    if self.is_speaking:
                        print(f"🔇 Voice ended (amplitude: {rms:.1f})\n")
                        self.is_speaking = False
                    
                    self.frames_since_alert += 1
                    
            except Exception as e:
                print(f"⚠️  VAD Error: {e}")
        
        await self.push_frame(frame, direction)


# Audio file saver
class AudioFileSaver(FrameProcessor):
    def __init__(self, output_filename: str, sample_rate: int = 16000):
        super().__init__()
        self.output_filename = output_filename
        self.sample_rate = sample_rate
        self.audio_frames = []
        self.frame_count = 0
        
    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, InputAudioRawFrame):
            self.frame_count += 1
            self.audio_frames.append(frame.audio)
            
            if self.frame_count % 100 == 0:
                # print(f"📼 Recording: {self.frame_count * 0.02:.1f}s")
                pass
        
        elif isinstance(frame, (EndFrame, CancelFrame)):
            await self._save_audio_file()
        
        await self.push_frame(frame, direction)
    
    async def _save_audio_file(self):
        if not self.audio_frames:
            print("⚠️  No audio frames captured!")
            return
        
        print(f"\n💾 Saving {self.frame_count} frames to {self.output_filename}...")
        
        try:
            audio_data = b''.join(self.audio_frames)
            
            with wave.open(self.output_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            
            duration = self.frame_count * 0.02
            file_size = len(audio_data) / 1024
            
            print(f"✅ Audio saved!")
            print(f"   Duration: {duration:.2f}s | Size: {file_size:.1f} KB")
            
        except Exception as e:
            print(f"❌ Error saving audio: {e}")


async def main():
    py_audio = None
    
    try:
        py_audio = pyaudio.PyAudio()
        print("🎤 Voice Activity Detection (Threshold: 2000)")
        print("=" * 50)
        print("Press Ctrl+C to stop\n")
        
        transport_params = LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=False,
            sample_rate=16000,
        )
        
        audio_input = LocalAudioInputTransport(py_audio, transport_params)
        
        # Only alerts when amplitude > 2000
        vad = VoiceActivityDetector(
            threshold=2000,
            cooldown_frames=25
        )
        
        file_saver = AudioFileSaver("recorded_voice.wav", 16000)
        
        pipeline = Pipeline([
            audio_input,
            vad,
            file_saver,
        ])
        
        task = PipelineTask(pipeline)
        runner = PipelineRunner()
        
        await task.queue_frame(StartFrame())
        await asyncio.sleep(0.1)
        
        print("🔴 Listening for loud voice (amplitude > 2000)...\n")
        await runner.run(task)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
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
