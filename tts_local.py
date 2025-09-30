"""
Local Text-to-Speech Module using pyttsx3
"""
import pyttsx3
import threading
import queue
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass


@dataclass
class TTSConfig:
    """Configuration for TTS engine"""
    voice_id: Optional[int] = None
    rate: int = 200  # Words per minute
    volume: float = 0.8  # 0.0 to 1.0
    enabled: bool = True


class LocalTTS:
    """Local Text-to-Speech using pyttsx3"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self.engine = None
        self.is_initialized = False
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.speech_thread = None
        self.stop_speaking = False
        
        # Callbacks
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Initialize engine
        self._initialize_engine()
        
        # Start speech processing thread
        if self.is_initialized:
            self._start_speech_thread()
    
    def _initialize_engine(self):
        """Initialize the TTS engine"""
        try:
            self.engine = pyttsx3.init()
            
            if self.engine:
                # Configure voice
                voices = self.engine.getProperty('voices')
                
                if voices:
                    if self.config.voice_id is not None and self.config.voice_id < len(voices):
                        self.engine.setProperty('voice', voices[self.config.voice_id].id)
                    else:
                        # Use first available voice
                        self.engine.setProperty('voice', voices[0].id)
                
                # Configure rate
                self.engine.setProperty('rate', self.config.rate)
                
                # Configure volume
                self.engine.setProperty('volume', self.config.volume)
                
                self.is_initialized = True
                print("TTS Engine initialized successfully")
                
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")
            self.is_initialized = False
    
    def _start_speech_thread(self):
        """Start the background speech processing thread"""
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
    
    def _speech_worker(self):
        """Background worker for processing speech queue"""
        while True:
            try:
                # Get text from queue (blocking)
                text = self.speech_queue.get(timeout=1)
                
                if text is None:  # Shutdown signal
                    break
                
                # Speak the text
                self._speak_sync(text)
                
                # Mark task as done
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                if self.on_error:
                    self.on_error(f"Speech error: {e}")
    
    def speak(self, text: str, priority: bool = False) -> bool:
        """
        Queue text for speech synthesis
        Args:
            text: Text to speak
            priority: If True, add to front of queue
        Returns:
            True if successfully queued, False otherwise
        """
        if not self.is_initialized or not self.config.enabled:
            return False
        
        if not text or not text.strip():
            return False
        
        try:
            if priority and not self.speech_queue.empty():
                # For priority, we'll stop current speech and speak immediately
                self.stop()
                time.sleep(0.1)  # Brief pause
            
            self.speech_queue.put(text.strip())
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to queue speech: {e}")
            return False
    
    def speak_sync(self, text: str) -> bool:
        """
        Speak text synchronously (blocks until complete)
        Args:
            text: Text to speak
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized or not self.config.enabled:
            return False
        
        if not text or not text.strip():
            return False
        
        try:
            self._speak_sync(text.strip())
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Sync speech error: {e}")
            return False
    
    def _speak_sync(self, text: str):
        """Internal synchronous speech method"""
        self.is_speaking = True
        self.stop_speaking = False
        
        try:
            # Notify speech start
            if self.on_speech_start:
                self.on_speech_start(text)
            
            # Speak the text
            self.engine.say(text)
            self.engine.runAndWait()
            
            # Notify speech end
            if self.on_speech_end:
                self.on_speech_end(text)
                
        except Exception as e:
            if self.on_error:
                self.on_error(f"Speech synthesis error: {e}")
        finally:
            self.is_speaking = False
    
    def stop(self):
        """Stop current speech"""
        try:
            if self.engine:
                self.engine.stop()
            self.stop_speaking = True
            self.is_speaking = False
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error stopping speech: {e}")
    
    def pause(self):
        """Pause current speech"""
        try:
            if self.engine:
                self.engine.stop()  # pyttsx3 doesn't have pause, so we stop
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error pausing speech: {e}")
    
    def resume(self):
        """Resume speech (not directly supported by pyttsx3)"""
        # pyttsx3 doesn't support resume, so this is a placeholder
        pass
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        self.config.rate = rate
        if self.engine:
            self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float):
        """Set speech volume (0.0 to 1.0)"""
        self.config.volume = max(0.0, min(1.0, volume))
        if self.engine:
            self.engine.setProperty('volume', self.config.volume)
    
    def set_voice(self, voice_id: int):
        """Set voice by ID"""
        try:
            voices = self.engine.getProperty('voices')
            if voices and 0 <= voice_id < len(voices):
                self.engine.setProperty('voice', voices[voice_id].id)
                self.config.voice_id = voice_id
                return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error setting voice: {e}")
        return False
    
    def get_voices(self) -> list:
        """Get list of available voices"""
        try:
            if self.engine:
                voices = self.engine.getProperty('voices')
                return [{"id": i, "name": v.name, "gender": v.gender, "age": v.age} 
                       for i, v in enumerate(voices)]
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error getting voices: {e}")
        return []
    
    def get_properties(self) -> Dict[str, Any]:
        """Get current TTS properties"""
        if not self.engine:
            return {}
        
        try:
            return {
                "rate": self.engine.getProperty('rate'),
                "volume": self.engine.getProperty('volume'),
                "voice": self.engine.getProperty('voice')
            }
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error getting properties: {e}")
            return {}
    
    def is_busy(self) -> bool:
        """Check if TTS is currently speaking or has queued speech"""
        return self.is_speaking or not self.speech_queue.empty()
    
    def clear_queue(self):
        """Clear all queued speech"""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
    
    def shutdown(self):
        """Shutdown TTS engine"""
        try:
            self.stop()
            self.clear_queue()
            
            # Send shutdown signal to worker thread
            self.speech_queue.put(None)
            
            if self.speech_thread and self.speech_thread.is_alive():
                self.speech_thread.join(timeout=2)
            
            if self.engine:
                self.engine.stop()
                
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error shutting down TTS: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.shutdown()


# Convenience functions for backward compatibility
_global_tts = None


def initialize_tts(config: Optional[TTSConfig] = None) -> LocalTTS:
    """Initialize global TTS instance"""
    global _global_tts
    if _global_tts is None:
        _global_tts = LocalTTS(config)
    return _global_tts


def speak(text: str, priority: bool = False) -> bool:
    """Speak text using global TTS instance"""
    global _global_tts
    if _global_tts is None:
        _global_tts = initialize_tts()
    return _global_tts.speak(text, priority)


def speak_sync(text: str) -> bool:
    """Speak text synchronously using global TTS instance"""
    global _global_tts
    if _global_tts is None:
        _global_tts = initialize_tts()
    return _global_tts.speak_sync(text)


def stop_speech():
    """Stop current speech"""
    global _global_tts
    if _global_tts:
        _global_tts.stop()


def shutdown_tts():
    """Shutdown global TTS instance"""
    global _global_tts
    if _global_tts:
        _global_tts.shutdown()
        _global_tts = None


if __name__ == "__main__":
    # Test the TTS module
    print("Testing Local TTS...")
    
    tts = LocalTTS()
    
    if tts.is_initialized:
        print("TTS initialized successfully")
        print("Available voices:")
        voices = tts.get_voices()
        for voice in voices:
            print(f"  {voice['id']}: {voice['name']} ({voice['gender']})")
        
        print("\nTesting speech...")
        tts.speak_sync("Hello! This is a test of the text-to-speech system.")
        
        print("TTS test completed")
    else:
        print("Failed to initialize TTS")
    
    tts.shutdown()

