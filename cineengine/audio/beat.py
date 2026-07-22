
import librosa
import numpy as np
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class BeatDetector:
    """
    Handles beat detection in audio files to enable beat-synced video editing.
    """
    def __init__(self):
        logger.info("BeatDetector initialized.")

    def detect_beats(self, audio_path: str) -> Tuple[np.ndarray, float]:
        """
        Detects beats and estimates the tempo (BPM) of an audio file.

        Args:
            audio_path (str): Path to the audio file.

        Returns:
            Tuple[np.ndarray, float]: A tuple containing an array of beat timestamps (in seconds) 
                                      and the estimated tempo (BPM).
        """
        logger.info(f"Detecting beats in {audio_path}...")
        try:
            y, sr = librosa.load(audio_path)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            logger.info(f"Detected tempo: {tempo:.2f} BPM. Found {len(beat_times)} beats.")
            return beat_times, tempo
        except Exception as e:
            logger.error(f"Error during beat detection: {e}")
            return np.array([]), 0.0

    def get_beat_intervals(self, beat_times: np.ndarray) -> List[float]:
        """
        Calculates the time intervals between consecutive beats.

        Args:
            beat_times (np.ndarray): Array of beat timestamps.

        Returns:
            List[float]: A list of time intervals between beats in seconds.
        """
        if len(beat_times) < 2:
            return []
        return np.diff(beat_times).tolist()

if __name__ == "__main__":
    # Example usage (requires an actual audio file)
    detector = BeatDetector()
    # beats, bpm = detector.detect_beats("path/to/audio.wav")
    # print(f"BPM: {bpm}, Beats: {beats[:10]}")
