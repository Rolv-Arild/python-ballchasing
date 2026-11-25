"""
Generate ballchasing/typed/models.py (the typed response objects) from the OpenAPI document snapshot.

    python scripts/generate_models.py          # write models.py
    python scripts/generate_models.py --check  # exit with 1 if models.py is out of date

One class is made per object schema reachable from a successful JSON response (with allOf flattened), plus the
shared base classes in BASES. Methods are not generated: they live in ballchasing/typed/methods.py, mapped in METHODS.
Every field has a default (0, "", False, None or an empty list), as the API leaves out many zero/empty values.
"""
import argparse
import importlib.util
import json
import keyword
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "tests" / "data" / "openapi.json"
OUTPUT = ROOT / "ballchasing" / "typed" / "models.py"

# Schema name -> class name, where the library has its own established name
RENAMES = {
    "Replay": "DeepReplay",
    "ReplaySummary": "ShallowReplay",
    "Group": "DeepGroup",
    "GroupSummary": "ShallowGroup",
}
# (class, field) -> class name for inline object schemas (default: class + field name, singular for arrays)
INLINE_NAMES = {
    ("ReplaySummaryTeam", "players"): "ReplaySummaryPlayer",
    ("DuplicateReplayList", "list"): "DuplicateReplay",
}
# Shared base classes: name -> (the classes it is a base of, its own base class or None).
# A base gets the fields all those classes have (with the same type); they keep the others.
BASES = {
    "BasicGroup": (["GroupRef", "ShallowGroup", "DeepGroup"], None),
    "BaseGroup": (["ShallowGroup", "DeepGroup"], "BasicGroup"),
    "BasePlayer": (["ReplayPlayer", "ReplaySummaryPlayer"], None),
    "BaseTeam": (["ReplayTeam", "ReplaySummaryTeam"], None),
    "BaseReplay": (["DeepReplay", "ShallowReplay"], None),
}
# Fields the OpenAPI document doesn't have, kept for compatibility: class -> {field: (type, description)}
EXTRA_FIELDS = {
    "ReplayPlayer": {"pro": ("bool", "Not sent for full replays (see ReplaySummaryPlayer): always False.")},
}
# Class -> mixin of ballchasing/typed/methods.py holding its hand-written methods
METHODS = {
    "User": "UserMethods",
    "PlayerId": "PlayerIdMethods",
    "Rank": "RankMethods",
    "BasicGroup": "BasicGroupMethods",
    "BasePlayer": "BasePlayerMethods",
    "BaseTeam": "BaseTeamMethods",
    "BaseReplay": "BaseReplayMethods",
    "DeepReplay": "DeepReplayMethods",
    "ShallowReplay": "ShallowReplayMethods",
}
# Classes using the __eq__/__repr__ of their base's mixin. Other subclasses get the dataclass's own (field by field),
# as with the hand-written classes before: e.g. BaseReplay compares ids, while DeepReplay compares all fields.
INHERIT_DUNDERS = {
    "ReplaySummaryTeam",  # Was TeamSR, which had BaseTeam's __eq__
    "GroupRef",  # Was BasicGroup
}
# Field order of classes that may be constructed with positional arguments: their order before generation.
# The other classes follow the OpenAPI document's order.
FIELD_ORDER = {
    "Rank": ["tier", "division", "name", "id"],
    "BasePlayer": ["start_time", "end_time", "name", "id", "pro", "mvp", "rank"],
    "BaseReplay": ["id", "link", "rocket_league_id", "recorder", "map_code", "map_name", "playlist_id",
                   "playlist_name", "duration", "overtime", "overtime_seconds", "season", "season_type", "date",
                   "visibility", "created", "uploader", "min_rank", "max_rank", "groups", "blue", "orange"],
}
# Names a field can't have: class bodies in models.py refer to them (a field would shadow them)
RESERVED = {"field", "datetime", "Any", "List", "Optional", "model", "_new_list"}
PRIMITIVES = {"integer": "int", "number": "float", "boolean": "bool", "string": "str"}
DEFAULTS = {"int": "0", "float": "0", "bool": "False", "str": '""'}


class Generator:
    def __init__(self, spec: dict):
        self.spec = spec
        # name -> {"description", "fields": {name: (type, description)} (own fields), "flat": (all fields)}
        self.classes: dict[str, dict] = {}
        self.parents: dict[str, str | None] = {}  # class -> its base class (from allOf, or BASES)
        self.sources: dict[str, int] = {}  # class -> id() of its schema, to detect two schemas with the same name

    # --- Schema helpers

    def resolve(self, schema: dict) -> dict:
        while "$ref" in schema:
            node = self.spec
            for part in schema["$ref"].lstrip("#/").split("/"):
                node = node[part]
            schema = node
        return schema

    def properties(self, schema: dict) -> dict:
        schema = self.resolve(schema)
        props = {}
        for part in schema.get("allOf", []):
            props.update(self.properties(part))
        props.update(schema.get("properties", {}))
        return props

    def is_object(self, schema: dict) -> bool:
        return bool(self.properties(schema))

    # --- Collecting classes

    def register(self, name: str, schema: dict) -> str:
        schema = self.resolve(schema)
        if name in self.classes:
            if self.sources[name] != id(schema):
                raise ValueError(f"Two different schemas would be generated as class {name}: "
                                 f"add a RENAMES or INLINE_NAMES entry")
            return name
        self.sources[name] = id(schema)
        cls = self.classes[name] = {"description": schema.get("description", ""), "fields": {}, "flat": {}}
        for field_name, prop in self.properties(schema).items():
            if not field_name.isidentifier() or keyword.iskeyword(field_name) or field_name in RESERVED:
                raise ValueError(f"{name}.{field_name} can't be a dataclass field name")
            cls["flat"][field_name] = (self.type_of(prop, name, field_name), prop.get("description", ""))
        cls["flat"].update(EXTRA_FIELDS.get(name, {}))
        # allOf with one object $ref (e.g. PlayerCore: allOf CoreCounters + own fields) -> subclass of it
        refs = [part for part in schema.get("allOf", []) if "$ref" in part and self.is_object(part)]
        parent = self.type_of(refs[0], name, "") if len(refs) == 1 else None
        self.parents[name] = parent
        inherited = self.all_fields(parent) if parent else {}
        cls["fields"] = {k: v for k, v in cls["flat"].items() if k not in inherited}
        return name

    def type_of(self, schema: dict, owner: str, field_name: str, array_item: bool = False) -> str:
        if "$ref" in schema:
            target = self.resolve(schema)
            if self.is_object(target):
                ref = schema["$ref"].split("/")[-1]
                return self.register(RENAMES.get(ref, ref), target)
            schema = target
        variants = schema.get("oneOf", []) + schema.get("anyOf", [])
        if variants or len(schema.get("allOf", [])) == 1:
            types = {self.type_of(v, owner, field_name, array_item) for v in variants or schema["allOf"]}
            types.discard("None")
            return types.pop() if len(types) == 1 else "Any"
        type_ = schema.get("type")
        if isinstance(type_, list):
            type_ = next((t for t in type_ if t != "null"), None)
        if type_ is None and "const" in schema:
            type_ = {bool: "boolean", int: "integer", float: "number", str: "string"}[type(schema["const"])]
        if type_ == "null":
            return "None"
        if type_ == "array":
            return f"List[{self.type_of(schema.get('items', {}), owner, field_name, array_item=True)}]"
        if type_ == "object" or "properties" in schema:
            if not self.is_object(schema):
                return "dict"
            name = INLINE_NAMES.get((owner, field_name))
            if name is None:
                camel = "".join(part.title() for part in field_name.split("_"))
                name = owner + (camel[:-1] if array_item and camel.endswith("s") else camel)
            return self.register(name, schema)
        if type_ == "string" and schema.get("format") == "date-time":
            return "datetime"
        return PRIMITIVES.get(type_, "Any")

    def collect(self):
        for path_item in self.spec["paths"].values():
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue
                operation_id = operation.get("operationId", "")
                owner = operation_id[:1].upper() + operation_id[1:] + "Response"  # Name of an inline response object
                for status, response in operation.get("responses", {}).items():
                    content = self.resolve(response).get("content", {}).get("application/json")
                    if status.startswith("2") and content and "schema" in content:
                        self.type_of(content["schema"], owner + (status if status != "200" else ""), "")

    # --- Base classes

    def make_bases(self):
        """Create the BASES classes, and make them the base class of their members (instead of an allOf one)."""
        for base, (members, base_parent) in BASES.items():  # In order: a base's own base comes first
            if base in self.classes:
                raise ValueError(f"A schema would be generated as class {base}, a name of BASES")
            inherited = set(self.all_fields(base_parent)) if base_parent else set()
            first = self.classes[members[0]]["flat"]
            common, overridden = {}, set()
            for name, (type_, description) in first.items():
                types = [self.classes[m]["flat"].get(name, (None,))[0] for m in members]
                if name in inherited or None in types:
                    continue
                if len(set(types)) == 1:
                    common[name] = (type_, description)
                elif (supertype := self.common_base(types)) is not None:
                    # E.g. blue: ReplayTeam / ReplaySummaryTeam -> BaseTeam in the base, members keep their own
                    common[name] = (supertype, description)
                    overridden.add(name)
            self.classes[base] = {"description": f"Fields shared by {', '.join(members)}.", "fields": common}
            self.parents[base] = base_parent
            for member in members:
                self.parents[member] = base
            for member in members:
                inherited = set(self.all_fields(base)) - overridden
                cls = self.classes[member]
                cls["fields"] = {k: v for k, v in cls["flat"].items() if k not in inherited}

    def common_base(self, types: list[str]) -> str | None:
        """The base class of BASES all these (class or List[class]) types share, as the same kind of type."""
        wrapped = {t.startswith("List[") for t in types}
        names = {re.sub(r"^List\[(.*)]$", r"\1", t) for t in types}
        bases = {self.parents.get(n) for n in names}
        if len(wrapped) != 1 or len(bases) != 1 or (base := bases.pop()) not in BASES:
            return None
        return f"List[{base}]" if wrapped.pop() else base

    def all_fields(self, name):
        fields = {}
        while name:
            fields = {**self.classes[name]["fields"], **fields}
            name = self.parents.get(name)
        return fields

    # --- Output

    def generate(self) -> str:
        self.collect()
        self.make_bases()
        parents = self.parents

        order, done, visiting = [], set(), []

        def visit(name):
            if name in done:
                return
            if name in visiting:  # The classes are used at runtime (to convert dicts), so they can't be forward refs
                raise ValueError(f"Cyclic class references: {' -> '.join(visiting + [name])}")
            visiting.append(name)
            deps = [parents.get(name)] + [dep for t, _ in self.classes[name]["fields"].values()
                                         for dep in re.findall(r"\w+", t)]
            for dep in deps:
                if dep in self.classes:
                    visit(dep)
            visiting.pop()
            done.add(name)
            order.append(name)

        for name in sorted(self.classes):
            visit(name)

        methods = load_methods_module()
        mixins_used = sorted(set(METHODS.values()))

        def chain(name):  # The class and its generated base classes
            names = [name]
            while parents.get(names[-1]):
                names.append(parents[names[-1]])
            return names

        def mixin_attributes(names):
            return {attr for n in names if n in METHODS
                    for c in getattr(methods, METHODS[n]).__mro__[:-1] for attr in c.__dict__}

        def overrides(name, dunder):
            return dunder in mixin_attributes(chain(name) if name in INHERIT_DUNDERS else [name])

        for name, cls in self.classes.items():
            if clash := set(self.all_fields(name)) & (mixin_attributes(chain(name)) | set(self.classes)):
                raise ValueError(f"Fields of {name} would shadow methods or classes: {sorted(clash)}")
            if name in FIELD_ORDER:  # Listed fields first, new ones after them (so positions don't move)
                if gone := set(FIELD_ORDER[name]) - set(cls["fields"]):
                    raise ValueError(f"FIELD_ORDER[{name!r}] lists fields {name} no longer has: {sorted(gone)}")
                field_order = FIELD_ORDER[name] + [k for k in cls["fields"] if k not in FIELD_ORDER[name]]
                cls["fields"] = {k: cls["fields"][k] for k in field_order}

        version = self.spec["info"].get("version", "")
        lines = [
            f"# Generated by scripts/generate_models.py from tests/data/openapi.json (ballchasing.com API {version}).",
            "# Do not edit: change the generator (or methods.py for methods) and run it again.",
            "from dataclasses import field",
            "from datetime import datetime",
            "from typing import Any, List, Optional",
            "",
            "from ballchasing.typed._base import _BaseModel, _DictToTypeMixin, model",
            "from ballchasing.typed.methods import (",
            *textwrap.wrap(", ".join(mixins_used) + ",", 116, initial_indent="    ", subsequent_indent="    "),
            ")",
            "",
            "_new_list = list  # For default_factory: in a class with a field named list, list is that field",
        ]
        for name in order:
            cls = self.classes[name]
            flags = [f"{arg}=False" for arg, dunder in (("eq", "__eq__"), ("repr", "__repr__"))
                     if overrides(name, dunder)]
            bases = [METHODS[name]] if name in METHODS else []
            bases += [parents[name]] if parents.get(name) else ["_BaseModel", "_DictToTypeMixin"]
            lines += ["", "", f"@model({', '.join(flags)})" if flags else "@model", f"class {name}({', '.join(bases)}):"]
            body = []
            if cls["description"]:
                body.append(docstring(cls["description"]))
            for field_name, (type_, description) in cls["fields"].items():
                if description:
                    body += textwrap.wrap(clean(description), 116, initial_indent="    #: ",
                                          subsequent_indent="    #: ")
                body.append(f"    {field_name}: {annotation(type_, self.classes)}")
            lines += body or ["    pass"]
        return "\n".join(lines) + "\n"


def load_methods_module():
    """Load methods.py by path: importing the ballchasing package would import the models.py being generated."""
    module_spec = importlib.util.spec_from_file_location("_methods", ROOT / "ballchasing" / "typed" / "methods.py")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def generate(spec: dict) -> str:
    return Generator(spec).generate()


def clean(text: str) -> str:
    """First paragraph of a Markdown description, as plain text on one line."""
    text = text.strip().split("\n\n")[0]
    text = re.sub(r"^\s*[*-] ", "", re.sub(r"\n\s*[*-] ", "; ", text))  # Bullet lists -> "a; b; c"
    text = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", text)  # Links -> their text
    return re.sub(r"\s+", " ", text)


def docstring(text: str) -> str:
    text = clean(text).replace("\\", "\\\\").replace('"""', "'''")  # Docstrings aren't raw strings
    wrapped = textwrap.wrap(text, 116, initial_indent="    ", subsequent_indent="    ")
    return '    """\n' + "\n".join(wrapped) + '\n    """'


def annotation(type_: str, classes: dict) -> str:
    if type_.startswith("List["):
        return f"{type_} = field(default_factory=_new_list)"
    if type_ in DEFAULTS:
        return f"{type_} = {DEFAULTS[type_]}"
    if type_ == "Any":
        return "Any = None"
    return f"Optional[{type_}] = None"  # Classes, datetime, dict


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="only check that models.py is up to date")
    args = parser.parse_args()

    code = generate(json.loads(SPEC_PATH.read_text(encoding="utf-8")))
    if args.check:
        up_to_date = OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == code
        print(f"{OUTPUT.relative_to(ROOT)} is {'up to date' if up_to_date else 'OUT OF DATE'}")
        return 0 if up_to_date else 1
    OUTPUT.write_text(code, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
