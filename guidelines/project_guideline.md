# Project Guideline: Guideline-Driven Repo Cleanup

## Mission

Organize, clean, document, and test a target repository while preserving working behavior.

The system should let LLM agents make engineering decisions using this guideline as the source of truth. The Python pipeline should not over-constrain the LLM with arbitrary file-count, line-count, or minimal-change rules.

## Core Pillars

### 1. Preserve Working Behavior

Do not intentionally change validated behavior unless the user explicitly asks for behavior change.

Preserve public function signatures when practical, CLI entry points, import paths, algorithmic behavior, input/output expectations, config behavior, and file formats.

### 2. Improve Organization

Good cleanup can include splitting mixed-responsibility files, creating clearer modules, moving helper code into better locations, grouping related functionality, simplifying imports, naming modules clearly, and improving package structure.

### 3. Improve Readability

Good cleanup can include clearer function names, simpler control flow, better comments, docstrings for important public functions, removing dead or duplicated code when safe, and clarifying assumptions.

### 4. Improve Documentation

Documentation is valid work when it improves future understanding. Useful documentation can include README updates, module-level docs, function docstrings, examples, architecture notes, usage notes, and test documentation.

### 5. Add or Improve Tests

When code is cleaned or reorganized, add or update tests where useful. Prefer unit tests for helper functions, smoke tests for entry points, import tests for package structure, regression tests for preserved behavior, and lightweight tests over fragile heavy tests.

### 6. Use LLM Judgment

The LLM agents should decide what files belong together, what scope is appropriate, what kind of cleanup matters, whether tests are sufficient, whether the work is good enough for this pass, and what should be deferred.

### 7. Use Deterministic Validation

The validator should run objective checks: syntax checks, compile checks, import checks, unit tests, smoke tests, and LLM-proposed validation commands. The LLM may design the validation plan, but real commands determine pass/fail.

## Definition of Good Enough

A pass can be considered good enough when the selected work improves organization, readability, documentation, or tests; the affected files belong together; the intended behavior is preserved; validation passes; the final summary explains what changed and why; and deferred work is explicitly listed.

## What to Avoid

Avoid changing algorithmic behavior without user approval, deleting important functionality, broad rewrites without tests, cosmetic-only edits while ignoring obvious structure problems, claiming success without validation evidence, hiding uncertainty, inventing APIs that do not exist, and editing unrelated files just to appear productive.
