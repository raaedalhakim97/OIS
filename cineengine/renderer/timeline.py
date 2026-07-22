
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TimelineEvent:
    """
    Represents an event on the video timeline, such as displaying an image, playing audio, or applying an effect.
    """
    def __init__(
        self,
        event_type: str,
        start_time: float,
        duration: float,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Initializes a TimelineEvent.

        Args:
            event_type (str): The type of event (e.g., 'image', 'audio', 'effect', 'subtitle').
            start_time (float): The start time of the event in seconds.
            duration (float): The duration of the event in seconds.
            properties (Optional[Dict[str, Any]]): A dictionary of event-specific properties.
        """
        self.event_type = event_type
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.properties = properties if properties is not None else {}

    def is_active(self, current_time: float) -> bool:
        """
        Checks if the event is active at the given time.

        Args:
            current_time (float): The current time in seconds.

        Returns:
            bool: True if the event is active, False otherwise.
        """
        return self.start_time <= current_time < self.end_time


class Timeline:
    """
    Manages all events and their timing on the video timeline.
    """
    def __init__(self):
        """
        Initializes the Timeline.
        """
        self.events: List[TimelineEvent] = []
        self._total_duration: float = 0.0
        logger.info("Timeline initialized.")

    def add_event(self, event: TimelineEvent) -> None:
        """
        Adds an event to the timeline.

        Args:
            event (TimelineEvent): The event to add.
        """
        self.events.append(event)
        self._update_total_duration()
        logger.debug(f"Added event: {event.event_type} from {event.start_time:.2f}s to {event.end_time:.2f}s.")

    def _update_total_duration(self) -> None:
        """
        Recalculates the total duration of the timeline based on its events.
        """
        if not self.events:
            self._total_duration = 0.0
        else:
            self._total_duration = max(event.end_time for event in self.events)

    @property
    def total_duration(self) -> float:
        """
        Returns the total duration of the video timeline in seconds.
        """
        return self._total_duration

    def get_active_events(self, current_time: float) -> List[TimelineEvent]:
        """
        Returns a list of events that are active at the given time.

        Args:
            current_time (float): The current time in seconds.

        Returns:
            List[TimelineEvent]: A list of active TimelineEvent objects.
        """
        return [event for event in self.events if event.is_active(current_time)]

    def clear_events(self) -> None:
        """
        Clears all events from the timeline.
        """
        self.events.clear()
        self._total_duration = 0.0
        logger.info("All timeline events cleared.")

if __name__ == "__main__":
    print("Timeline module example:")
    timeline = Timeline()

    timeline.add_event(TimelineEvent("image", 0.0, 5.0, {"path": "image1.png"}))
    timeline.add_event(TimelineEvent("audio", 0.0, 10.0, {"path": "music.mp3"}))
    timeline.add_event(TimelineEvent("effect", 2.0, 3.0, {"type": "bloom", "intensity": 0.7}))
    timeline.add_event(TimelineEvent("subtitle", 1.0, 3.0, {"text": "Hello!"}))

    print(f"Total timeline duration: {timeline.total_duration:.2f}s")

    print("\n--- Active events at 1.5s ---")
    for event in timeline.get_active_events(1.5):
        print(f"  Type: {event.event_type}, Start: {event.start_time:.2f}, End: {event.end_time:.2f}, Props: {event.properties}")

    print("\n--- Active events at 4.0s ---")
    for event in timeline.get_active_events(4.0):
        print(f"  Type: {event.event_type}, Start: {event.start_time:.2f}, End: {event.end_time:.2f}, Props: {event.properties}")

    print("\n--- Active events at 6.0s ---")
    for event in timeline.get_active_events(6.0):
        print(f"  Type: {event.event_type}, Start: {event.start_time:.2f}, End: {event.end_time:.2f}, Props: {event.properties}")

    timeline.clear_events()
    print(f"\nTotal timeline duration after clearing: {timeline.total_duration:.2f}s")
