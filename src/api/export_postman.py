"""Exports docs/postman_collection.json from the running app's OpenAPI spec — Sprint 6, Day 40."""
import json
import os
from src.api.main import app

BASE_URL = "http://localhost:8000"


def export_postman_collection(path="docs/postman_collection.json"):
    spec = app.openapi()
    items = []
    for route_path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            items.append({
                "name": details.get("summary") or f"{method.upper()} {route_path}",
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {"raw": f"{{{{base_url}}}}{route_path}", "host": ["{{base_url}}"],
                             "path": route_path.strip("/").split("/")},
                },
            })
    collection = {
        "info": {"name": "Nifty 100 Financial Intelligence API", "schema":
                  "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
        "item": items,
        "variable": [{"key": "base_url", "value": BASE_URL}],
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(collection, f, indent=2)
    print(f"Postman collection written to {path} ({len(items)} requests)")
    return path


if __name__ == "__main__":
    export_postman_collection()
