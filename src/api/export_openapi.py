"""Exports the OpenAPI 3.0 spec to docs/openapi.json — Sprint 6, Day 40."""
import json
import os
from src.api.main import app


def export_openapi(path="docs/openapi.json"):
    spec = app.openapi()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"OpenAPI spec written to {path} ({len(spec.get('paths', {}))} paths)")
    return path


if __name__ == "__main__":
    export_openapi()
