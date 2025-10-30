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


def get_tree(oid: str, base_path: str = "") -> dict[str, str]:
    result: dict[str, str] = {}

    for type_, oid_, name in _iter_tree_entries(oid):
        assert "/" not in name
        assert "\\" not in name
        assert name not in ("..", ".")

        path = base_path + name
        if type_ == "blob":
            result[path] = oid_
        elif type_ == "tree":
            result.update(get_tree(oid_, os.path.join(path, "")))
        else:
            assert False, f"Unknown type : {type_}"
    return result


def read_tree(tree_oid: str) -> None:
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, base_path="./").items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data.get_object(oid))


def _empty_current_directory() -> None:
    for root, dirnames, filenames in os.walk(".", topdown=False):
        for filename in filenames:
            path = os.path.relpath(os.path.join(root, filename))
            if is_ignored(path) or not os.path.isfile(path):
                continue
            os.remove(path)
        for dirname in dirnames:
            path = os.path.relpath(os.path.join(root, dirname))
            if is_ignored(path):
                continue
            try:
                os.rmdir(path)
            except (FileNotFoundError, OSError):
                pass


def _iter_tree_entries(oid: str):
    if not oid:
        return
    tree = data.get_object(oid, "tree")
    for entry in tree.decode().splitlines():
        type_, oid_, name = entry.split(" ", 2)
        yield type_, oid_, name


def is_ignored(path: str) -> bool:
    # multiple slashes to account for different os
    for delimiter in ["/", "\\"]:
        path = path.replace(delimiter, " ")
    return ".ugit" in path.split(" ")
