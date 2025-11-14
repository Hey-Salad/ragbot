"""
Voice Agent for Twilio Voice Calls
Integrates with RAG system for intelligent voice responses
"""

from fastapi import WebSocket
from twilio.twiml.voice_response import VoiceResponse, Gather, Say
from rag_system import RAGSystem
import logging
import json
import asyncio
from typing import Optional

class VoiceAgent:
    def __init__(self):
        self.rag_system = RAGSystem()
        self.active_calls = {}
        
    def handle_incoming_call(self, from_number: str) -> str:
        """Handle incoming voice call - return TwiML"""
        response = VoiceResponse()
        
        # Greet the caller
        response.say(
            "Hello! Welcome to the RAG Bot voice assistant. "
            "I can answer questions based on my knowledge base. "
            "Please ask your question after the beep.",
            voice='Polly.Joanna',
            language='en-US'
        )
        
        # Gather speech input
        gather = Gather(
            input='speech',
            action='/voice/process',
            method='POST',
            speech_timeout='auto',
            language='en-US'
        )
        
        response.append(gather)
        
        # If no input, say goodbye
        response.say(
            "I didn't hear anything. Please call back if you have a question. Goodbye!",
            voice='Polly.Joanna'
        )
        
        return str(response)
    
    def process_speech(self, speech_result: str, call_sid: str) -> str:
        """Process speech input and return TwiML response"""
        response = VoiceResponse()
        
        if not speech_result:
            response.say(
                "I'm sorry, I didn't catch that. Please try again.",
                voice='Polly.Joanna'
            )
            response.redirect('/voice/webhook')
            return str(response)
        
        # Query the RAG system
        try:
            answer = self.rag_system.query(speech_result)
            
            # Clean up answer for speech (remove markdown, emojis, etc.)
            clean_answer = self._clean_for_speech(answer)
            
            # Speak the answer
            response.say(
                clean_answer,
                voice='Polly.Joanna',
                language='en-US'
            )
            
            # Ask if they want to ask another question
            gather = Gather(
                input='speech',
                action='/voice/process',
                method='POST',
                speech_timeout='auto',
                language='en-US',
                hints='yes, no, another question'
            )
            
            gather.say(
                "Would you like to ask another question? Say yes or no.",
                voice='Polly.Joanna'
            )
            
            response.append(gather)
            
            # If no response, end call
            response.say("Thank you for using RAG Bot. Goodbye!", voice='Polly.Joanna')
            response.hangup()
            
        except Exception as e:
            logging.error(f"Error processing speech: {str(e)}")
            response.say(
                "I'm sorry, I encountered an error processing your question. Please try again later.",
                voice='Polly.Joanna'
            )
            response.hangup()
        
        return str(response)
    
    def handle_continue(self, speech_result: str) -> str:
        """Handle continuation decision"""
        response = VoiceResponse()
        
        speech_lower = speech_result.lower() if speech_result else ""
        
        if any(word in speech_lower for word in ['yes', 'yeah', 'sure', 'another']):
            # Continue to another question
            response.say(
                "Great! Please ask your next question.",
                voice='Polly.Joanna'
            )
            response.redirect('/voice/webhook')
        else:
            # End the call
            response.say(
                "Thank you for using RAG Bot. Have a great day! Goodbye!",
                voice='Polly.Joanna'
            )
            response.hangup()
        
        return str(response)
    
    def _clean_for_speech(self, text: str) -> str:
        """Clean text for speech synthesis"""
        # Remove markdown
        text = text.replace('**', '').replace('*', '')
        text = text.replace('_', '').replace('`', '')
        
        # Remove emojis and special characters
        import re
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        # Limit length for speech (max ~500 chars)
        if len(text) > 500:
            text = text[:497] + "..."
        
        return text
    
    def get_call_status(self, call_sid: str) -> dict:
        """Get status of an active call"""
        return self.active_calls.get(call_sid, {})


class VoiceAgentRealtime:
    """
    Advanced voice agent using OpenAI Realtime API
    For more natural conversations with streaming audio
    """
    def __init__(self):
        self.rag_system = RAGSystem()
        self.active_sessions = {}
    
    async def handle_websocket(self, websocket: WebSocket, call_sid: str):
        """Handle WebSocket connection for real-time voice"""
        await websocket.accept()
        
        try:
            # Send initial greeting
            greeting = {
                "event": "start",
                "streamSid": call_sid,
                "message": "Connected to RAG Bot voice assistant"
            }
            await websocket.send_json(greeting)
            
            # Handle incoming audio streams
            while True:
                data = await websocket.receive_json()
                
                if data.get("event") == "media":
                    # Process audio chunk
                    await self._process_audio_chunk(websocket, data, call_sid)
                
                elif data.get("event") == "stop":
                    logging.info(f"Call {call_sid} ended")
                    break
                    
        except Exception as e:
            logging.error(f"WebSocket error: {str(e)}")
        finally:
            if call_sid in self.active_sessions:
                del self.active_sessions[call_sid]
    
    async def _process_audio_chunk(self, websocket: WebSocket, data: dict, call_sid: str):
        """Process incoming audio chunk"""
        # This would integrate with OpenAI Realtime API
        # For now, we'll use the simpler Gather approach
        pass