"""
Report what changed in the ballchasing.com API since the snapshot in tests/data/openapi.json.

    python scripts/check_api_spec.py           # diff the live OpenAPI document against the snapshot
    python scripts/check_api_spec.py --update  # ...then replace the snapshot and regenerate the typed models

Exits with status 1 when something changed, so it can run in CI.
"""
import argparse
import json
import sys
from pathlib import Path

import requests

from generate_models import OUTPUT as MODELS, generate

SPEC_URL = "https://ballchasing.com/doc/api/openapi.json"
SNAPSHOT = Path(__file__).parent.parent / "tests" / "data" / "openapi.json"
METHODS = ("get", "post", "put", "patch", "delete")
# Schema keywords the client can depend on (e.g. page sizes, list lengths), compared along with the types
CONSTRAINTS = ("format", "minimum", "maximum", "minItems", "maxItems", "minLength", "maxLength", "pattern", "default",
               "const", "required")


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
        ref = schema.get("$ref", "").split("/")[-1]
        schema = resolve(schema)
        if "enum" in schema:
            text = f"enum{sorted(map(str, schema['enum']))}"
        elif "items" in schema:
            text = f"array[{schema_type(schema['items'])}]"
        elif "oneOf" in schema or "anyOf" in schema:
            text = " | ".join(schema_type(s) for s in schema.get("oneOf", schema.get("anyOf")))
        else:
            text = str(schema.get("type", "object"))
        constraints = {k: schema[k] for k in CONSTRAINTS if k in schema}
        return (f"{ref}:" if ref else "") + text + (f" {json.dumps(constraints, sort_keys=True)}" if constraints else "")

    def properties(key, schema, seen=()):
        """Entries for an object schema's properties, and those of the inline objects (and arrays of) in it."""
        if isinstance(schema, dict) and "$ref" in schema:
            return  # Named schemas get their own entries
        schema = resolve(schema)
        if id(schema) in seen:
            return
        for part in schema.get("allOf", []) + schema.get("oneOf", []) + schema.get("anyOf", []):
            if "$ref" not in part:
                yield from properties(key, part, seen + (id(schema),))
        for name, sub in schema.get("properties", {}).items():
            yield f"{key}.{name}", schema_type(sub)
            yield from properties(f"{key}.{name}", sub, seen + (id(schema),))
        if "items" in schema:
            yield from properties(f"{key}[]", schema["items"], seen + (id(schema),))

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
                out[f"{key} body ({content_type})"] = schema_type(content.get("schema", {}))
                out.update(properties(f"{key} body", content.get("schema", {})))
            for status, response in op.get("responses", {}).items():
                out[f"{key} -> {status}"] = "response"
                for content_type, content in resolve(response).get("content", {}).items():
                    out[f"{key} -> {status} ({content_type})"] = schema_type(content.get("schema", {}))
                    out.update(properties(f"{key} -> {status}", content.get("schema", {})))
            if "x-rate-limits" in op:
                out[f"{key} rate-limits"] = json.dumps(op["x-rate-limits"], sort_keys=True)
            if "x-daily-quota" in op:
                out[f"{key} daily-quota"] = json.dumps(op["x-daily-quota"], sort_keys=True)
    for name, schema in spec.get("components", {}).get("schemas", {}).items():
        out[f"schema {name}"] = schema_type(schema) + "".join(
            f" allOf:{part['$ref'].split('/')[-1]}" for part in schema.get("allOf", []) if "$ref" in part)
        out.update(properties(f"schema {name}", schema))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--update", action="store_true", help="replace the snapshot with the live document")
    args = parser.parse_args()

    response = requests.get(SPEC_URL, headers={"User-Agent": "python-ballchasing-spec-check"}, timeout=30)
    response.raise_for_status()
    live = response.json()
    old, new = summarize(json.loads(SNAPSHOT.read_text(encoding="utf-8"))), summarize(live)

    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = sorted(k for k in old.keys() & new.keys() if old[k] != new[k])
    for label, keys in (("Added", added), ("Removed", removed), ("Changed", changed)):
        if keys:
            print(f"\n{label} ({len(keys)}):")
        for k in keys:
            print(f"  {k}: {old.get(k, '')} -> {new.get(k, '')}" if label == "Changed" else f"  {k}: {(new | old)[k]}")
    # Anything else that changes the typed models (e.g. descriptions) counts too
    models = generate(live)
    models_change = models != MODELS.read_text(encoding="utf-8")
    if models_change:
        print(f"\nThe typed models ({MODELS.name}) would change.")
    changes = bool(added or removed or changed or models_change)
    if not changes:
        print(f"No changes since the snapshot (version {new['version']}).")

    if args.update:
        SNAPSHOT.write_text(json.dumps(live, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        MODELS.write_text(models, encoding="utf-8")
        print(f"\nUpdated {SNAPSHOT} and regenerated {MODELS}.")
        print("Run the tests (tests/test_openapi.py) to see what else the client needs, e.g. new parameters.")
    return 1 if changes else 0


if __name__ == "__main__":
    sys.exit(main())
