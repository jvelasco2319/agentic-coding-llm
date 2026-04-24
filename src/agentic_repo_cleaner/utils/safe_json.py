from __future__ import annotations

import json
from typing import Any


def dumps_pretty(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)
