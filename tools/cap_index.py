#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"ERR: {msg}", file=sys.stderr)
    sys.exit(2)


def load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        fail("PyYAML is required. Install with: python3 -m pip install pyyaml")
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"yaml parse failed for {path}: {exc}")


def build_index(repo_root: Path):
    caps_root = repo_root / "caps"
    items = []
    if not caps_root.is_dir():
        return items
    for cap_dir in sorted(p for p in caps_root.iterdir() if p.is_dir()):
        capd = cap_dir / "capd" / "capability.yaml"
        if not capd.exists():
            continue
        data = load_yaml(capd) or {}
        cap = data.get("capability", {})
        items.append({
            "directory": cap_dir.relative_to(repo_root).as_posix(),
            "name": cap.get("name"),
            "package_name": cap.get("package_name", cap_dir.name),
            "version": cap.get("version"),
            "kind": cap.get("kind"),
            "aliases": cap.get("aliases", []),
            "validator": (cap_dir / "tools" / "validate_package.py").relative_to(repo_root).as_posix() if (cap_dir / "tools" / "validate_package.py").exists() else None,
        })
    return items


def validate_all(repo_root: Path, index_items):
    for item in index_items:
        validator = item.get("validator")
        if not validator:
            fail(f"missing validator for {item.get('directory')}")
        result = subprocess.run([sys.executable, validator], cwd=repo_root, text=True)
        if result.returncode != 0:
            fail(f"validator failed for {item.get('directory')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and optionally validate capability index")
    parser.add_argument("--output", default="dist/caps.index.json", help="Path to write JSON index")
    parser.add_argument("--validate-all", action="store_true", help="Run each cap package validator")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    index_items = build_index(repo_root)
    if not index_items:
        fail("no capability packages found under caps/")

    for _it in index_items:
        for _k in ("directory", "validator"):
            _v = _it.get(_k)
            if _v is not None and Path(_v).is_absolute():
                fail(f"{_k} must be repo-relative, got absolute path: {_v} (the committed index must be portable)")

    out_path = repo_root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"capabilities": index_items}, indent=2) + "\n", encoding="utf-8")
    print(f"OK: wrote {out_path.as_posix()}")

    if args.validate_all:
        validate_all(repo_root, index_items)
        print("OK: validated all capability packages")


if __name__ == "__main__":
    main()
