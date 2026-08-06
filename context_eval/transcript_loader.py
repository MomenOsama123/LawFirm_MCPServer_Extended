import glob
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("transcript_loader")

DEFAULT_TEST_SUITE_DIR = os.path.join("context_eval", "test_suite")


class TranscriptLoadError(Exception):
    """Raised when a transcript JSON file is missing, unparseable, or malformed."""
    pass


def validate_transcript_schema(data: Dict[str, Any], file_path: str) -> None:
    """
    Validates that the loaded JSON matches the required test case schema.
    
    Required Keys:
      - case_id: str
      - expected_decision: str
      - messages: list
    """
    required_keys = ["case_id", "expected_decision", "messages"]
    for key in required_keys:
        if key not in data:
            raise TranscriptLoadError(
                f"File '{file_path}' is missing required key: '{key}'"
            )

    if not isinstance(data["messages"], list) or len(data["messages"]) == 0:
        raise TranscriptLoadError(
            f"File '{file_path}' has invalid or empty 'messages' list."
        )

    for idx, msg in enumerate(data["messages"]):
        if not isinstance(msg, dict) or "role" not in msg:
            raise TranscriptLoadError(
                f"File '{file_path}' message at index {idx} missing 'role' field."
            )


def load_single_transcript(file_path: str) -> Dict[str, Any]:
    """
    Loads and validates a single transcript JSON file.
    
    Args:
        file_path: Absolute or relative path to the .json transcript file.

    Returns:
        Dict containing case_id, description, expected_decision, and messages.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Transcript file not found at: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise TranscriptLoadError(f"Failed to parse JSON in '{file_path}': {e}") from e

    validate_transcript_schema(data, file_path)
    return data


def load_all_transcripts(
    test_suite_dir: str = DEFAULT_TEST_SUITE_DIR,
    case_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Discovers, loads, and validates all JSON transcript files in the test suite directory.
    
    Args:
        test_suite_dir: Path to directory containing transcript JSON files.
        case_ids: Optional list of specific case_ids to filter (e.g. ['case_001_high_risk_waiver']).

    Returns:
        List of validated transcript dictionaries sorted by case_id.
    """
    if not os.path.isdir(test_suite_dir):
        raise FileNotFoundError(
            f"Test suite directory '{test_suite_dir}' does not exist. "
            "Run generate_test_suite.py first."
        )

    pattern = os.path.join(test_suite_dir, "*.json")
    json_files = sorted(glob.glob(pattern))

    if not json_files:
        raise FileNotFoundError(
            f"No JSON transcript files found in '{test_suite_dir}'."
        )

    transcripts = []
    for file_path in json_files:
        try:
            transcript = load_single_transcript(file_path)
            
            # If a subset filter was provided, check against case_id
            if case_ids and transcript["case_id"] not in case_ids:
                continue

            transcripts.append(transcript)
        except TranscriptLoadError as e:
            logger.error(f"Skipping invalid transcript: {e}")

    if not transcripts:
        logger.warning(f"No valid transcripts loaded from '{test_suite_dir}'.")

    return transcripts