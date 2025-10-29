import os

from . import data


def write_tree(directory: str = ".") -> str:
    entries: list[tuple[str, str, str]] = []
    with os.scandir(directory) as it:
        for entry in it:
            full_file_location: str = os.path.join(directory, entry.name)
            if is_ignored(full_file_location):
                continue

            type_: str = ""
            if entry.is_file(follow_symlinks=True):
                type_ = "blob"
                with open(full_file_location, "rb") as f:
                    oid = data.hash_object(f.read(), type_)

            elif entry.is_dir(follow_symlinks=True):
                type_ = "tree"
                oid = write_tree(full_file_location)
            else:
                raise NotImplementedError
            entries.append((entry.name, oid, type_))

    tree = "".join(f"{type_} {oid} {name}\n" for name, oid, type_ in sorted(entries))
    return data.hash_object(tree.encode(), "tree")


def is_ignored(path: str) -> bool:
    # multiple slashes to account for different os
    for delimiter in ["/", "\\"]:
        path = path.replace(delimiter, " ")
    return ".ugit" in path.split(" ")
