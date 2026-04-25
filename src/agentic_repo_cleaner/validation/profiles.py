from __future__ import annotations


VALIDATION_PROFILES: dict[str, list[str]] = {
    "python": [
        "python -m compileall -q .",
        "python -m unittest discover -s tests",
    ],
    "python_pytest": [
        "python -m compileall -q .",
        "python -m pytest -q",
    ],
    "python_and_cpp": [
        "python -m compileall -q .",
        "python -m unittest discover -s tests",
        "cmake -S cpp -B cpp/build",
        "cmake --build cpp/build",
    ],
    "cpp": [
        "cmake -S . -B build",
        "cmake --build build",
    ],
    "generic": [],
}


def get_profile_commands(profile_name: str) -> list[str]:
    return list(VALIDATION_PROFILES.get(profile_name, []))