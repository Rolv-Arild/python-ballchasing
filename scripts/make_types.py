import os
import random
from dataclasses import make_dataclass, fields
from typing import List, Any

from requests import HTTPError

import ballchasing as bc

api = bc.Api(os.environ.get("BALLCHASING_API_KEY"))


# Creates a starting point for dataclasses that contain response data

def get_diverse_replays(limit=1000, deep=False):
    remaining = limit
    while True:
        rank = random.choice(bc.Rank.ALL)
        season = random.choice(bc.Season.ALL)
        playlist = random.choice(bc.Playlist.ALL)
        map_id = random.choice(bc.Map.ALL)
        try:
            replays = api.get_replays(
                playlist=playlist,
                season=season,
                max_rank=rank,
                map_id=map_id,
                count=10,
                deep=deep,
            )

            for replay in replays:
                yield replay
                remaining -= 1
                if remaining <= 0:
                    return
        except HTTPError:
            continue


def get_diverse_groups(deep=False):
    if deep:
        for group in get_diverse_groups(deep=False):
            yield api.get_group(group["id"])
    else:
        groups = api.get_groups(count=10)
        yield from groups
        groups = api.get_groups(creator="76561199225615730")
        yield from groups


classes = {}


def get_structure(name, item):
    if isinstance(item, (str, int, float, bool)):
        return type(item)
    elif isinstance(item, list):
        sub_name = name.title().replace("_", "")
        if sub_name[-1] == "s":
            sub_name = sub_name[:-1]  # Remove plural 's' for lists
        sub_structures = [get_structure(sub_name, item) for item in item]
        if len(sub_structures) == 0:
            return List[Any]
        else:
            return List[sub_structures.pop()]
    elif isinstance(item, dict):
        s = {}
        for key, value in item.items():
            sub_name = name + "|" + key.title().replace("_", "")
            s[key] = get_structure(sub_name, value)
        name = name.replace("|", "_")
        if name in classes:
            # Update with new fields if there are any
            existing_dc = classes[name]
            for field in fields(existing_dc):
                if field.name not in s:
                    t = field.type
                    if t == int and s.get(field.name) == float:
                        t = float
                    s[field.name] = t
        dc = make_dataclass(name, s.items())
        classes[name] = dc
        return dc
    else:
        return Any


def print_class(cls):
    print("@dataclass")
    print(f"class {cls.__name__}:")
    for field in fields(cls):
        if type(field.type) == type(List):
            default = "field(default_factory=list)"
            print(f"    {field.name}: List[{field.type.__args__[0].__name__}] = {default}")
        else:
            if field.type == str:
                default = '""'
                print(f"    {field.name}: {field.type.__name__} = {default}")
            elif field.type in {int, float, bool}:
                default = field.type()
                print(f"    {field.name}: {field.type.__name__} = {default}")
            else:
                default = None
                print(f"    {field.name}: Optional[{field.type.__name__}] = {default}")
    print()


def main():
    global classes

    classes_per_category = {}
    for deep in (False, True):
        name = "DeepReplay" if deep else "ShallowReplay"
        it = get_diverse_replays(deep=deep)
        # it = tqdm(it)
        for replay in it:
            structure = get_structure(name, replay)
            # break

        for cls in classes.values():
            print_class(cls)
        print("=" * 80)
        classes_per_category[name] = classes
        classes = {}

    for deep in (False, True):
        name = "DeepGroup" if deep else "ShallowGroup"
        for group in get_diverse_groups(deep=deep):
            structure = get_structure(name, group)
            # break

        for cls in classes.values():
            print_class(cls)
        print("=" * 80)

        classes_per_category[name] = classes
        classes = {}

    # Print all classes without duplicates

    all_classes = {}
    for category, cls_dict in classes_per_category.items():
        for cls_name, cls in cls_dict.items():
            # for cls_name2, cls2 in all_classes.items():
            #     share_all = True
            #     if len(fields(cls2)) != len(fields(cls)):
            #         share_all = False
            #     elif set(f.name for f in fields(cls2)) != set(f.name for f in fields(cls)):
            #         share_all = False
            #     else:
            #         for f in fields(cls2):
            #             if f.type != next((f2.type for f2 in fields(cls) if f2.name == f.name), None):
            #                 share_all = False
            #                 break
            #     if share_all and cls_name != cls_name2:
            #         new_name = f"shared_{cls_name}_{cls_name2}"
            #         new_cls = make_dataclass(new_name, [(f.name, f.type) for f in fields(cls)])
            #         all_classes[new_name] = new_cls
            #         break
            # else:  # No break
            #     all_classes[cls_name] = cls
            if cls_name not in all_classes:
                all_classes[cls_name] = cls
            else:
                # Check that they share all fields (name and type)
                existing_cls = all_classes[cls_name]
                share_all = True
                if len(fields(existing_cls)) != len(fields(cls)):
                    share_all = False
                elif set(f.name for f in fields(existing_cls)) != set(f.name for f in fields(cls)):
                    share_all = False
                else:
                    for f in fields(existing_cls):
                        if f.type != next((f2.type for f2 in fields(cls) if f2.name == f.name), None):
                            share_all = False
                            break
                if not share_all:
                    all_classes[f"{cls_name}_{category}"] = cls
    for cls in all_classes.values():
        print_class(cls)

    print("=" * 80)
    # Find unique classes (by fields)
    groups = {}
    for cls_name, cls in all_classes.items():
        fields_set = frozenset((f.name, f.type) for f in fields(cls))
        if fields_set not in groups:
            groups[fields_set] = []
        groups[fields_set].append(cls_name)


if __name__ == '__main__':
    main()
