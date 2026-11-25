"""
Report what changed in the ballchasing.com API since the snapshot in tests/data/openapi.json.

    python scripts/check_api_spec.py           # diff the live OpenAPI document against the snapshot
    python scripts/check_api_spec.py --update  # ...then replace the snapshot (and run the tests: tests/test_openapi.py)

Exits with status 1 when something changed, so it can run in CI.
"""
import argparse
import json
import sys
from pathlib import Path

import requests

SPEC_URL = "https://ballchasing.com/doc/api/openapi.json"
SNAPSHOT = Path(__file__).parent.parent / "tests" / "data" / "openapi.json"
METHODS = ("get", "post", "put", "patch", "delete")


def summarize(spec: dict) -> dict[str, str]:
    """Flatten the parts of the spec a client depends on into {key: description} entries."""

    def resolve(schema):
        while isinstance(schema, dict) and "$ref" in schema:
            node = spec
            for part in schema["$ref"].lstrip("#/").split("/"):
                node = node[part]
            schema = node
        return schema

    def schema_type(schema):
        schema = resolve(schema)
        if "enum" in schema:
            return f"enum{sorted(map(str, schema['enum']))}"
        if "items" in schema:
            return f"array[{schema_type(schema['items'])}]"
        for key in ("oneOf", "anyOf"):
            if key in schema:
                return " | ".join(schema_type(s) for s in schema[key])
        return schema.get("type", "object")

    out = {"version": spec["info"].get("version", "")}
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method not in METHODS:
                continue
            key = f"{method.upper()} {path}"
            out[key] = "deprecated" if op.get("deprecated") else "endpoint"
            for param in op.get("parameters", []) + item.get("parameters", []):
                param = resolve(param)
                req = " (required)" if param.get("required") else ""
                out[f"{key} {param['in']}:{param['name']}"] = schema_type(param.get("schema", {})) + req
            for content_type, content in resolve(op.get("requestBody", {})).get("content", {}).items():
                for name, prop in resolve(content.get("schema", {})).get("properties", {}).items():
                    out[f"{key} body:{name}"] = schema_type(prop)
            for status in op.get("responses", {}):
                out[f"{key} -> {status}"] = "response"
            if "x-rate-limits" in op:
                out[f"{key} rate-limits"] = json.dumps(op["x-rate-limits"], sort_keys=True)
            if "x-daily-quota" in op:
                out[f"{key} daily-quota"] = json.dumps(op["x-daily-quota"], sort_keys=True)
    for name, schema in spec.get("components", {}).get("schemas", {}).items():
        parts = [schema] + schema.get("allOf", [])
        for part in parts:
            for prop, sub in resolve(part).get("properties", {}).items():
                out[f"schema {name}.{prop}"] = schema_type(sub)
        if "enum" in schema:
            out[f"schema {name}"] = schema_type(schema)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--update", action="store_true", help="replace the snapshot with the live document")
    args = parser.parse_args()

    response = requests.get(SPEC_URL, headers={"User-Agent": "python-ballchasing-spec-check"}, timeout=30)
    response.raise_for_status()
    live = response.json()
    old, new = summarize(json.loads(SNAPSHOT.read_text())), summarize(live)

    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = sorted(k for k in old.keys() & new.keys() if old[k] != new[k])
    for label, keys in (("Added", added), ("Removed", removed), ("Changed", changed)):
        if keys:
            print(f"\n{label} ({len(keys)}):")
        for k in keys:
            print(f"  {k}: {old.get(k, '')} -> {new.get(k, '')}" if label == "Changed" else f"  {k}: {(new | old)[k]}")
    if not (added or removed or changed):
        print(f"No changes since the snapshot (version {new['version']}).")

    if args.update:
        SNAPSHOT.write_text(json.dumps(live, indent=1, ensure_ascii=False) + "\n")
        print(f"\nUpdated {SNAPSHOT}. Run the tests (tests/test_openapi.py) to see what the client needs.")
    return 1 if (added or removed or changed) else 0


if __name__ == "__main__":
    sys.exit(main())
