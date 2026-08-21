# scheduler.py
import logging
import threading
import time
from .consolidation import MemoryConsolidator

logger = logging.getLogger(__name__)

def run_consolidation():
    """External trigger for a single periodic consolidation pass."""
    logger.info("Starting consolidation pass...")
    consolidator = MemoryConsolidator()
    consolidator.run()
    logger.info("Consolidation pass completed.")


class ConsolidationScheduler:
    """Runs memory consolidation in a background thread at fixed time intervals."""

    def __init__(self, interval_seconds: int = 300):
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread = None

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                run_consolidation()
            except Exception as e:
                logger.exception("Error during scheduled consolidation: %s", e)
            
            # Wait for the next interval or until stopped
            self._stop_event.wait(self.interval_seconds)

    def start(self):
        """Start the background scheduler thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("ConsolidationScheduler is already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("ConsolidationScheduler started (interval: %ds).", self.interval_seconds)

    def stop(self):
        """Stop the background scheduler thread cleanly."""
        if self._thread is None:
            return

        self._stop_event.set()
        self._thread.join(timeout=5)
        logger.info("ConsolidationScheduler stopped.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Running a single manual consolidation pass...")
    run_consolidation()