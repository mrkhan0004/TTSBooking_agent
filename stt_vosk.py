"""
Offline Speech-to-Text Module using Vosk
"""
import json
import os
import queue
import threading
import time
from typing import Optional, Callable, Dict, Any, Generator

# Optional imports - will gracefully degrade if not available
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio not available. STT will be disabled.")

try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Warning: Vosk not available. STT will be disabled.")


class VoskSTT:
    """Offline Speech-to-Text using Vosk"""
    
    def __init__(self, model_path: Optional[str] = None, 
                 sample_rate: int = 16000,
                 chunk_size: int = 4000):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        
        # Audio configuration
        self.format = pyaudio.paInt16
        self.channels = 1
        
        # Vosk components
        self.model = None
        self.recognizer = None
        
        # Audio components
        self.audio = None
        self.stream = None
        
        # State management
        self.is_initialized = False
        self.is_listening = False
        self.is_recording = False
        
        # Callbacks
        self.on_result: Optional[Callable] = None
        self.on_final_result: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_listening_start: Optional[Callable] = None
        self.on_listening_end: Optional[Callable] = None
        
        # Initialize
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Vosk model and recognizer"""
        if not VOSK_AVAILABLE or not PYAUDIO_AVAILABLE:
            print("STT dependencies not available. Skipping initialization.")
            self.is_initialized = False
            return
            
        try:
            # Use default model path if not provided
            if not self.model_path:
                self.model_path = self._get_default_model_path()
            
            if not os.path.exists(self.model_path):
                print(f"Model not found at {self.model_path}")
                print("Please download a Vosk model from: https://alphacephei.com/vosk/models")
                return
            
            # Set Vosk log level (0 = no logs, 1 = errors, 2 = info)
            vosk.SetLogLevel(0)
            
            # Load model
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            self.is_initialized = True
            print(f"Vosk STT initialized with model: {self.model_path}")
            
        except Exception as e:
            print(f"Failed to initialize Vosk STT: {e}")
            self.is_initialized = False
    
    def _get_default_model_path(self) -> str:
        """Get default model path"""
        # Check common model locations
        possible_paths = [
            "models/vosk-model-small-en-us-0.15",
            "models/vosk-model-en-us-0.22",
            "vosk-model-small-en-us-0.15",
            "vosk-model-en-us-0.22",
            os.path.expanduser("~/vosk-model-small-en-us-0.15"),
            os.path.expanduser("~/vosk-model-en-us-0.22")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return the most likely default
        return "models/vosk-model-small-en-us-0.15"
    
    def start_listening(self, timeout: Optional[float] = None) -> bool:
        """
        Start listening for speech
        Args:
            timeout: Maximum listening time in seconds (None for no timeout)
        Returns:
            True if started successfully, False otherwise
        """
        if not self.is_initialized:
            if self.on_error:
                self.on_error("STT not initialized")
            return False
        
        if self.is_listening:
            return True
        
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_listening = True
            self.is_recording = True
            
            if self.on_listening_start:
                self.on_listening_start()
            
            # Start listening in a separate thread
            self._listen_thread = threading.Thread(
                target=self._listen_worker, 
                args=(timeout,),
                daemon=True
            )
            self._listen_thread.start()
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to start listening: {e}")
            return False
    
    def stop_listening(self):
        """Stop listening for speech"""
        if self.is_listening:
            self.is_listening = False
            self.is_recording = False
            
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
                self.stream = None
            
            if self.on_listening_end:
                self.on_listening_end()
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback for processing audio data"""
        if self.is_recording and self.recognizer:
            # Process audio chunk
            if self.recognizer.AcceptWaveform(in_data):
                # Final result
                result = json.loads(self.recognizer.Result())
                if result.get("text"):
                    if self.on_final_result:
                        self.on_final_result(result["text"])
            else:
                # Partial result
                result = json.loads(self.recognizer.PartialResult())
                if result.get("partial"):
                    if self.on_result:
                        self.on_result(result["partial"])
        
        return (in_data, pyaudio.paContinue)
    
    def _listen_worker(self, timeout: Optional[float]):
        """Worker thread for listening"""
        start_time = time.time()
        
        while self.is_listening:
            if timeout and (time.time() - start_time) > timeout:
                break
            
            time.sleep(0.1)
        
        self.stop_listening()
    
    def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """
        Listen for speech once and return the result
        Args:
            timeout: Maximum time to listen in seconds
        Returns:
            Recognized text or None if no speech detected
        """
        if not self.is_initialized:
            return None
        
        result_queue = queue.Queue()
        
        def on_final_result(text):
            result_queue.put(text)
        
        # Set callback
        original_callback = self.on_final_result
        self.on_final_result = on_final_result
        
        try:
            # Start listening
            if not self.start_listening(timeout):
                return None
            
            # Wait for result
            try:
                result = result_queue.get(timeout=timeout + 1)
                return result.strip() if result else None
            except queue.Empty:
                return None
                
        finally:
            # Restore callback and stop listening
            self.on_final_result = original_callback
            self.stop_listening()
    
    def listen_continuous(self) -> Generator[str, None, None]:
        """
        Continuously listen for speech and yield results
        Returns:
            Generator that yields recognized text
        """
        if not self.is_initialized:
            return
        
        result_queue = queue.Queue()
        
        def on_final_result(text):
            if text.strip():
                result_queue.put(text)
        
        # Set callback
        original_callback = self.on_final_result
        self.on_final_result = on_final_result
        
        try:
            # Start listening
            if not self.start_listening():
                return
            
            # Yield results as they come
            while self.is_listening:
                try:
                    result = result_queue.get(timeout=0.1)
                    yield result.strip()
                except queue.Empty:
                    continue
                    
        finally:
            # Restore callback and stop listening
            self.on_final_result = original_callback
            self.stop_listening()
    
    def set_model(self, model_path: str) -> bool:
        """Change the Vosk model"""
        if not os.path.exists(model_path):
            if self.on_error:
                self.on_error(f"Model not found: {model_path}")
            return False
        
        try:
            # Stop current listening
            self.stop_listening()
            
            # Load new model
            self.model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            self.model_path = model_path
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to load model: {e}")
            return False
    
    def get_available_devices(self) -> list:
        """Get list of available audio input devices"""
        if not self.audio:
            return []
        
        devices = []
        try:
            device_count = self.audio.get_device_count()
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info.get("maxInputChannels", 0) > 0:
                    devices.append({
                        "index": i,
                        "name": device_info.get("name", f"Device {i}"),
                        "channels": device_info.get("maxInputChannels", 0),
                        "sample_rate": device_info.get("defaultSampleRate", 0)
                    })
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error getting devices: {e}")
        
        return devices
    
    def set_device(self, device_index: int) -> bool:
        """Set audio input device"""
        try:
            if self.audio:
                device_info = self.audio.get_device_info_by_index(device_index)
                if device_info.get("maxInputChannels", 0) > 0:
                    # Note: PyAudio device selection is done when opening the stream
                    # This would require reopening the stream with the new device
                    return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error setting device: {e}")
        return False
    
    def is_available(self) -> bool:
        """Check if STT is available and initialized"""
        return self.is_initialized
    
    def shutdown(self):
        """Shutdown STT engine"""
        self.stop_listening()
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
            self.audio = None
        
        self.model = None
        self.recognizer = None
        self.is_initialized = False
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.shutdown()


# Convenience functions for backward compatibility
_global_stt = None


def initialize_stt(model_path: Optional[str] = None) -> VoskSTT:
    """Initialize global STT instance"""
    global _global_stt
    if _global_stt is None:
        _global_stt = VoskSTT(model_path)
    return _global_stt


def listen_once(timeout: float = 5.0) -> Optional[str]:
    """Listen for speech once using global STT instance"""
    global _global_stt
    if _global_stt is None:
        _global_stt = initialize_stt()
    return _global_stt.listen_once(timeout)


def shutdown_stt():
    """Shutdown global STT instance"""
    global _global_stt
    if _global_stt:
        _global_stt.shutdown()
        _global_stt = None


if __name__ == "__main__":
    # Test the STT module
    print("Testing Vosk STT...")
    
    stt = VoskSTT()
    
    if stt.is_available():
        print("STT initialized successfully")
        print("Available audio devices:")
        devices = stt.get_available_devices()
        for device in devices:
            print(f"  {device['index']}: {device['name']} ({device['channels']} channels)")
        
        print("\nListening for 5 seconds... Say something!")
        result = stt.listen_once(5.0)
        
        if result:
            print(f"Recognized: {result}")
        else:
            print("No speech detected")
        
        print("STT test completed")
    else:
        print("Failed to initialize STT")
        print("Please ensure you have:")
        print("1. Downloaded a Vosk model")
        print("2. Installed pyaudio")
        print("3. Have a working microphone")
    
    stt.shutdown()
