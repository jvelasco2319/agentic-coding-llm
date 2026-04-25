from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class WorkflowMode:
    """
    Defines a high-level agentic coding workflow.

    The mode tells the agents:
    - what kind of coding task this is
    - what output policy to follow
    - what validation profile to use
    - what file types should be considered relevant
    """

    name: str
    description: str
    task_prefix: str
    output_policy: str
    validation_profile: str
    allowed_extensions: tuple[str, ...]
    preserve_source: bool = True
    default_target_dir: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_prompt_dict(self) -> dict:
        return asdict(self)


CLEANUP_MODE = WorkflowMode(
    name="cleanup",
    description="Organize, clean, document, and test code while preserving behavior.",
    task_prefix="Organize, clean, document, and test this repo while preserving working behavior.",
    output_policy="Modify the existing repo in place only after validation passes.",
    validation_profile="python",
    allowed_extensions=(
        ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml",
        ".csv", ".ini", ".cfg",
    ),
    preserve_source=True,
    notes=(
        "Improve organization, readability, documentation, and tests.",
        "Preserve working behavior and public APIs unless explicitly allowed.",
        "Add or update tests when useful.",
    ),
)


TRANSLATE_CPP_MODE = WorkflowMode(
    name="translate_cpp",
    description="Translate a Python repository to C++ while preserving behavior.",
    task_prefix=(
        "Translate this Python repository to C++ while preserving behavior. "
        "Keep the Python source as the reference implementation and create C++ code under cpp/."
    ),
    output_policy="Create C++ files under cpp/. Do not delete or overwrite the Python source.",
    validation_profile="python_and_cpp",
    allowed_extensions=(
        ".py", ".md", ".txt", ".json", ".csv", ".toml", ".yaml", ".yml",
        ".cpp", ".hpp", ".h", ".cc", ".cxx", ".hh", ".c", ".cmake",
    ),
    preserve_source=True,
    default_target_dir="cpp",
    notes=(
        "Generate simple, readable, standard C++.",
        "Create CMakeLists.txt when useful.",
        "Validate that the Python reference still works.",
        "Validate that the C++ version builds and runs.",
        "Compare behavior with the Python reference when practical.",
    ),
)


DOCUMENT_ONLY_MODE = WorkflowMode(
    name="document_only",
    description="Improve documentation without changing behavior.",
    task_prefix="Document this repository for future developers while preserving code behavior.",
    output_policy="Prefer README, docstrings, comments, and architecture notes. Avoid logic changes.",
    validation_profile="python",
    allowed_extensions=(
        ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml",
        ".csv", ".ini", ".cfg",
    ),
    preserve_source=True,
    notes=(
        "Documentation is the main goal.",
        "Only touch code when adding docstrings or explanatory comments.",
        "Avoid refactoring unless required for documentation clarity.",
    ),
)


TEST_GENERATION_MODE = WorkflowMode(
    name="test_generation",
    description="Add or improve tests for an existing repository.",
    task_prefix="Add or improve unit and smoke tests while preserving code behavior.",
    output_policy="Prefer adding tests. Avoid changing source code unless needed to enable testability.",
    validation_profile="python",
    allowed_extensions=(
        ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml",
        ".csv", ".ini", ".cfg",
    ),
    preserve_source=True,
    notes=(
        "Focus on unit tests, smoke tests, and regression tests.",
        "Do not refactor source code unless required.",
        "If source changes are needed, explain why.",
    ),
)


BUG_FIX_MODE = WorkflowMode(
    name="bug_fix",
    description="Fix a bug while preserving unrelated behavior.",
    task_prefix="Fix the requested bug with the smallest coherent behavior-preserving change.",
    output_policy="Modify only files relevant to the bug and tests.",
    validation_profile="python",
    allowed_extensions=(
        ".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml",
        ".csv", ".ini", ".cfg",
    ),
    preserve_source=True,
    notes=(
        "First verify whether the bug still exists.",
        "If the bug is already fixed, do not invent a source-code change.",
        "Add or preserve a regression test proving the behavior.",
        "Avoid unrelated cleanup.",
    ),
)


MODES = {
    mode.name: mode
    for mode in [
        CLEANUP_MODE,
        TRANSLATE_CPP_MODE,
        DOCUMENT_ONLY_MODE,
        TEST_GENERATION_MODE,
        BUG_FIX_MODE,
    ]
}


def get_mode(name: str) -> WorkflowMode:
    try:
        return MODES[name]
    except KeyError as exc:
        valid = ", ".join(sorted(MODES))
        raise ValueError(f"Unknown mode '{name}'. Valid modes: {valid}") from exc


def available_modes() -> dict[str, dict]:
    return {name: mode.to_prompt_dict() for name, mode in MODES.items()}