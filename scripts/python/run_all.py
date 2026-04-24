"""Regenerate the whole Game Development portfolio: 5 engine projects + posters.

This is the script CI runs. It's intentionally boring — imports each builder
and calls its `main()`. Running it in a clean sandbox produces the same bytes
every time.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _load(name: str) -> object:
    """Load a sibling script as a module, preserving package visibility so
    that dataclasses and typing.get_type_hints() work (see video portfolio)."""
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # MUST come before exec_module for dataclasses
    spec.loader.exec_module(mod)
    return mod


STAGES = [
    "build_godot_project",
    "build_defold_project",
    "build_solar2d_project",
    "build_panda3d_project",
    "build_stride_project",
    "render_posters",
]


def main() -> None:
    # Ensure `art_helpers` resolves regardless of how run_all.py is invoked.
    sys.path.insert(0, str(HERE))
    for name in STAGES:
        print(f"\n=== {name} ===")
        mod = _load(name)
        mod.main()

    print("\n[ok] run_all complete — see scripts/projects/ and assets/renders/")


if __name__ == "__main__":
    main()
