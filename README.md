# Agentic Repo Cleaner

A guideline-driven autonomous repo cleanup system.

The core idea:

```text
The guideline defines what good work means.
The LLM agents decide what to clean, document, refactor, and test.
The validator runs objective syntax/import/unit/smoke checks.
The reviewer decides if the validated outcome is good enough.
```

## Default Ollama model routing

This repo defaults to the same three-role Ollama setup you were using:

```text
Mapper/context model:   glm-5.1:cloud
Planner model:          minimax-m2.5:cloud
Reviewer model:         kimi-k2.5:cloud
```

Supporting roles default to the planner model:

```text
Applier:        minimax-m2.5:cloud
Test Designer:  minimax-m2.5:cloud
Repair:         minimax-m2.5:cloud
```

## Main command

```bash
python -m agentic_repo_cleaner.cli apply ^
  --repo C:\Users\jarve\Downloads\messy_analytics_repo ^
  --guideline guidelines\project_guideline.md ^
  --task "Organize, clean, document, and test this repo while preserving working behavior." ^
  --mapper-model glm-5.1:cloud ^
  --planner-model minimax-m2.5:cloud ^
  --reviewer-model kimi-k2.5:cloud
```

You can omit the model flags because these are already the defaults.

## Other useful commands

```bash
python -m agentic_repo_cleaner.cli models
python -m agentic_repo_cleaner.cli map --repo C:\path\to\target_repo
python -m agentic_repo_cleaner.cli plan --repo C:\path\to\target_repo --guideline guidelines\project_guideline.md --task "Clean this repo"
python -m agentic_repo_cleaner.cli validate --repo C:\path\to\target_repo
```

## Philosophy

This system does **not** hardcode every rule about what a cleanup must look like.
Your multipage guideline acts as the source of truth.

The LLM agents decide:

- what files need work
- what tests should be added
- whether refactoring or documentation is needed
- what "good enough" means for the pass
- what should be deferred

The deterministic validator decides:

- whether Python parses
- whether imports work
- whether unit tests pass
- whether smoke commands pass
- whether validation commands return exit code 0
