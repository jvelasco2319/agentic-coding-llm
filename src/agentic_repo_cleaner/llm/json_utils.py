from __future__ import annotations

import json
import re
from typing import Any


class JSONExtractionError(ValueError):
    pass


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    return stripped


def _parse_first_json_value(text: str) -> Any:
    decoder = json.JSONDecoder()

    for i, char in enumerate(text):
        if char not in "[{":
            continue

        try:
            value, _end = decoder.raw_decode(text[i:])
            return value
        except json.JSONDecodeError:
            continue

    raise JSONExtractionError("No valid JSON value found in LLM response.")


def _parse_all_json_objects(text: str) -> list[dict[str, Any]]:
    """
    Parse multiple top-level JSON objects from messy LLM output.

    This handles model outputs like:

        {"path": "...", "content": "...", "reason": "..."}
        {"path": "...", "content": "...", "reason": "..."}

    which are invalid as a single JSON document but can be recovered.
    """
    decoder = json.JSONDecoder()
    objects: list[dict[str, Any]] = []
    idx = 0

    while idx < len(text):
        next_obj = text.find("{", idx)
        if next_obj == -1:
            break

        try:
            value, end = decoder.raw_decode(text[next_obj:])
        except json.JSONDecodeError:
            idx = next_obj + 1
            continue

        if isinstance(value, dict):
            objects.append(value)

        idx = next_obj + end

    return objects


def _looks_like_file_edit(obj: dict[str, Any]) -> bool:
    return (
        isinstance(obj.get("path"), str)
        and isinstance(obj.get("content"), str)
        and isinstance(obj.get("reason"), str)
    )


def _wrap_file_edits_as_apply_result(objects: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "summary": "Recovered file edits from multiple top-level JSON objects returned by the LLM.",
        "changed_files": objects,
        "added_files": [],
        "deleted_files": [],
        "notes": [
            "The LLM returned one JSON object per file instead of the required ApplyResult wrapper. "
            "json_utils recovered the output so the pipeline can continue."
        ],
    }


def extract_json_object(text: str) -> dict[str, Any]:
    """
    Extract one JSON object from an LLM response.

    The prompts ask for pure JSON, but this function tolerates:
    - leading prose before JSON
    - markdown code fences
    - one valid JSON object embedded in text
    - multiple file-edit JSON objects from the Applier
    """
    stripped = _strip_code_fences(text)

    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        value = _parse_first_json_value(stripped)

    if isinstance(value, dict):
        # If the first object is only a file edit, the Applier probably returned
        # several file edit objects instead of one ApplyResult object.
        if _looks_like_file_edit(value):
            objects = _parse_all_json_objects(stripped)
            if objects and all(_looks_like_file_edit(obj) for obj in objects):
                return _wrap_file_edits_as_apply_result(objects)
        return value

    if isinstance(value, list):
        if all(isinstance(item, dict) and _looks_like_file_edit(item) for item in value):
            return _wrap_file_edits_as_apply_result(value)

    raise JSONExtractionError(f"Expected JSON object, got {type(value).__name__}.")