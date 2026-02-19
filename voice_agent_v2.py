"""
Voice Agent with OpenAI Whisper (STT) and 11Labs (TTS)
Integrates with Asterisk SIP for real-time voice calls
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
import subprocess
import tempfile

import openai
from elevenlabs import generate, set_api_key, voices
import requests

logger = logging.getLogger(__name__)


class VoiceAgent:
    def __init__(
        self,
        openai_api_key: str,
        elevenlabs_api_key: str,
        elevenlabs_voice_id: Optional[str] = None
    ):
        """
        Initialize Voice Agent

        Args:
            openai_api_key: OpenAI API key for Whisper
            elevenlabs_api_key: 11Labs API key
            elevenlabs_voice_id: Voice ID (default: Rachel)
        """
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key

        set_api_key(elevenlabs_api_key)
        self.elevenlabs_voice_id = elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"  # Rachel

        logger.info("Voice Agent initialized")

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio using OpenAI Whisper

        Args:
            audio_file_path: Path to audio file (wav, mp3, m4a, etc.)

        Returns:
            Transcribed text
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"  # Optional: specify language
                )

            text = transcript.text
            logger.info(f"Transcribed: {text[:100]}...")
            return text

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise

    async def synthesize_speech(
        self,
        text: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Synthesize speech using 11Labs

        Args:
            text: Text to convert to speech
            output_path: Where to save the audio file

        Returns:
            Path to generated audio file
        """
        try:
            if not output_path:
                output_path = tempfile.mktemp(suffix=".mp3")

            # Generate audio using 11Labs
            audio = generate(
                text=text,
                voice=self.elevenlabs_voice_id,
                model="eleven_monolingual_v1"
            )

            # Save to file
            with open(output_path, "wb") as f:
                f.write(audio)

            logger.info(f"Generated speech: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"11Labs synthesis failed: {e}")
            raise

    def convert_to_asterisk_format(self, audio_path: str) -> str:
        """
        Convert audio to Asterisk-compatible format (8kHz, mono, ulaw)

        Args:
            audio_path: Input audio file

        Returns:
            Path to converted file
        """
        output_path = audio_path.replace(".mp3", ".wav")

        # Use ffmpeg to convert
        cmd = [
            "ffmpeg", "-i", audio_path,
            "-ar", "8000",  # 8kHz sample rate
            "-ac", "1",     # mono
            "-acodec", "pcm_mulaw",  # ulaw codec
            "-y",           # overwrite
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Converted to Asterisk format: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio conversion failed: {e}")
            raise

    async def process_voice_call(
        self,
        audio_input_path: str,
        ai_response_generator
    ) -> str:
        """
        Process a complete voice interaction cycle

        Args:
            audio_input_path: Path to caller's audio
            ai_response_generator: Function to generate AI response

        Returns:
            Path to response audio file (Asterisk format)
        """
        try:
            # 1. Transcribe caller's speech
            user_text = await self.transcribe_audio(audio_input_path)
            logger.info(f"User said: {user_text}")

            # 2. Get AI response
            ai_text = await ai_response_generator(user_text)
            logger.info(f"AI response: {ai_text[:100]}...")

            # 3. Synthesize AI response
            tts_audio = await self.synthesize_speech(ai_text)

            # 4. Convert to Asterisk format
            asterisk_audio = self.convert_to_asterisk_format(tts_audio)

            return asterisk_audio

        except Exception as e:
            logger.error(f"Voice call processing failed: {e}")
            # Generate error message audio
            error_audio = await self.synthesize_speech(
                "I'm sorry, I encountered an error. Please try again."
            )
            return self.convert_to_asterisk_format(error_audio)

    def get_available_voices(self):
        """Get list of available 11Labs voices"""
        try:
            voice_list = voices()
            return [{
                "voice_id": v.voice_id,
                "name": v.name,
                "category": v.category
            } for v in voice_list]
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []


class AsteriskIntegration:
    """
    Integration with Asterisk SIP server
    """

    def __init__(self, asterisk_agi_path: str = "/var/lib/asterisk/agi-bin"):
        self.agi_path = Path(asterisk_agi_path)
        self.recording_dir = Path("/var/spool/asterisk/recording")

    def create_agi_script(self, script_name: str = "voice_agent.py"):
        """
        Create AGI script for Asterisk to use
        """
        agi_script = f"""#!/usr/bin/env python3
import sys
import asyncio
from voice_agent_v2 import VoiceAgent

# AGI environment variables
env = {{}}
while True:
    line = sys.stdin.readline().strip()
    if line == '':
        break
    key, value = line.split(':', 1)
    env[key.strip()] = value.strip()

# Initialize voice agent
agent = VoiceAgent(
    openai_api_key="{os.getenv('OPENAI_API_KEY')}",
    elevenlabs_api_key="{os.getenv('ELEVENLABS_API_KEY')}"
)

# Process call
async def handle_call():
    # Get recording path from Asterisk
    unique_id = env.get('agi_uniqueid')
    recording_path = f"/var/spool/asterisk/recording/{{unique_id}}.wav"

    # AI response generator (example)
    async def generate_response(user_text):
        # TODO: Integrate with your RAG system or AI backend
        return f"You said: {{user_text}}. How can I help you?"

    # Process the call
    response_audio = await agent.process_voice_call(recording_path, generate_response)

    # Return path to Asterisk
    print(f"SET VARIABLE response_audio {{response_audio}}")
    print("200 result=1")

asyncio.run(handle_call())
"""

        script_path = self.agi_path / script_name
        script_path.write_text(agi_script)
        script_path.chmod(0o755)

        logger.info(f"Created AGI script: {script_path}")
        return script_path

    def create_dialplan_extension(self):
        """
        Generate Asterisk dialplan configuration
        """
        dialplan = """
[voice-agent]
exten => _X.,1,Answer()
    same => n,Wait(1)
    same => n,Playback(welcome)
    same => n,Record(/var/spool/asterisk/recording/${UNIQUEID}.wav,3,60)
    same => n,AGI(voice_agent.py)
    same => n,Playback(${response_audio})
    same => n,Hangup()
"""
        return dialplan


# Example usage
async def test_voice_agent():
    """Test the voice agent"""
    agent = VoiceAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY")
    )

    # Test TTS
    print("Testing text-to-speech...")
    audio_path = await agent.synthesize_speech(
        "Hello! I'm your AI voice assistant powered by Whisper and Eleven Labs."
    )
    print(f"Generated audio: {audio_path}")

    # Test available voices
    print("\nAvailable voices:")
    voices = agent.get_available_voices()
    for v in voices[:5]:
        print(f"  - {v['name']} ({v['voice_id']})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_voice_agent())
