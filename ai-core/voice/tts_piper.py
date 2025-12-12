"""
Piper Text-to-Speech Integration
Actual implementation using Piper TTS
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional
import wave
import io

logger = logging.getLogger(__name__)


class PiperTTS:
    """
    Text-to-Speech using Piper
    Falls back to mock audio if Piper not available
    """
    
    def __init__(self, model_path: str = "models/voice/piper", sample_rate: int = 22050):
        self.model_path = Path(model_path)
        self.sample_rate = sample_rate
        self.use_mock = True
        self.piper_bin = None
        
        # Check if piper binary exists
        piper_paths = [
            '/usr/local/bin/piper',
            '/usr/bin/piper',
            Path.home() / '.local/bin/piper'
        ]
        
        for path in piper_paths:
            if Path(path).exists():
                self.piper_bin = str(path)
                self.use_mock = False
                logger.info(f"✓ Found Piper at {path}")
                break
        
        if self.use_mock:
            logger.warning("Piper not found, using mock synthesis")
    
    def synthesize(self, text: str, voice_id: str = "en_US-lessac-medium", 
                   output_path: Optional[str] = None) -> bytes:
        """Convert text to speech"""
        
        if self.use_mock:
            return self._mock_synthesize(text, output_path)
        
        try:
            # Run Piper command
            cmd = [
                self.piper_bin,
                '--model', str(self.model_path / f"{voice_id}.onnx"),
                '--output_file', '-'  # Output to stdout
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            audio_data, error = process.communicate(input=text.encode())
            
            if process.returncode == 0:
                if output_path:
                    with open(output_path, 'wb') as f:
                        f.write(audio_data)
                    logger.info(f"Saved audio to {output_path}")
                
                return audio_data
            else:
                logger.error(f"Piper failed: {error.decode()}")
                return self._mock_synthesize(text, output_path)
                
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return self._mock_synthesize(text, output_path)
    
    def _mock_synthesize(self, text: str, output_path: Optional[str] = None) -> bytes:
        """Generate mock WAV audio"""
        # Create minimal valid WAV file
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(self.sample_rate)
            
            # Silent audio (1 second)
            silence = b'\x00\x00' * self.sample_rate
            wav.writeframes(silence)
        
        audio_bytes = buffer.getvalue()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            logger.debug(f"Saved mock audio to {output_path}")
        
        return audio_bytes
    
    def is_loaded(self) -> bool:
        """Check if real TTS is available"""
        return not self.use_mock
    
    def get_available_voices(self) -> list:
        """List available voice models"""
        if not self.model_path.exists():
            return []
        
        voices = []
        for onnx_file in self.model_path.glob("*.onnx"):
            voices.append(onnx_file.stem)
        
        return voices


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    tts = PiperTTS()
    
    audio = tts.synthesize(
        "Hello, this is a test of the text to speech system.",
        output_path="/tmp/test_tts.wav"
    )
    
    print(f"Generated {len(audio)} bytes of audio")
    print(f"Using mock: {tts.use_mock}")
    print(f"Available voices: {tts.get_available_voices()}")
