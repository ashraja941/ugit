import itertools
import string
import operator
import os
from sys import stdout
from typing import NamedTuple

from . import data


class Commit(NamedTuple):
    tree: str
    parent: str | None
    message: str


def create_tag(name: str, oid: str) -> None:
    """
    Create a tag for a OID

    Args: Name (str), OID (str)
    Returns: None
    """
    ref_location: str = os.path.join("refs", "tags", name)
    data.update_ref(ref_location, oid)


def checkout(oid: str) -> None:
    """
    Switch repository state to state at COMMIT OID

    Args: OID (str)
    Returns: None
    """
    commit = get_commit(oid)
    read_tree(commit.tree)
    data.update_ref("HEAD", oid)


def commit(message: str) -> str:
    """
    create a commit Object with the following information
        Tree TreeOID
         Parent ParentOID <Optional>
        \\n
        message

    Args: message(str)
    Returns: Commit OID (str)
    """

    commitObject: str = f"tree {write_tree()}\n"
    HEAD: str | None = data.get_ref("HEAD")
    if HEAD:
        commitObject += f"parent {HEAD}\n"
    commitObject += "\n"
    commitObject += f"{message}\n"

    oid: str = data.hash_object(commitObject.encode(), "commit")
    data.update_ref("HEAD", oid)

    _ = stdout.flush()
    _ = stdout.write(commitObject)
    return oid


def write_tree(directory: str = ".") -> str:
    """
    Recursively go through all the files and folders and hash them with the correct types.
    creates tree Object with type, OID, name information for every entry in it.

    Args: directory = '.' (str)
    Returns: OID (str)
    """
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


def read_tree(tree_oid: str) -> None:
    """
    Replace current directory with the files from a tree OID
    Empties current directory first and then puts every file back in it's position

    Args: Tree OID (str)
    Returns: None
    """
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, base_path="./").items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            _ = f.write(data.get_object(oid))


def get_tree(oid: str, base_path: str = "") -> dict[str, str]:
    """
    creates a dictionary with the path and the oid recrusively
    only has results from files because trees are taken into accoun in the path

    Args: OID (str), Base Path = "" (str)
    Returns: Dict[Path:OID]
    """
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


def _empty_current_directory() -> None:
    """
    Helper function to erase all files from current directory
    """
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
    """
    Helper function to iterate through all the entries in a tree

    Args: OID (str)
    Returns: Generator[tuple[type (str), oid (str), name (str)]]
    """
    if not oid:
        return
    tree = data.get_object(oid, "tree")
    for entry in tree.decode().splitlines():
        type_, oid_, name = entry.split(" ", 2)
        yield type_, oid_, name


def get_commit(oid: str):
    """
    Reads through commit Information and returns tree hash, parent hash and message

    Args: Commit OID (str)
    Returns: Commit(Tree (str), parent (str), message (str))
    """
    parent: str | None = None

    tree: str = ""

    commit: str = data.get_object(oid, "commit").decode()
    lines = iter(commit.splitlines())
    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(" ", 1)
        if key == "tree":
            tree = value
        elif key == "parent":
            parent = value
        else:
            assert False, f"Unknown field {key}"

    message = "\n".join(lines)
    return Commit(tree=tree, parent=parent, message=message)


def get_oid(name: str) -> str:
    """
    return the oid with the tag / name

    Args: name (str)
    Returns: OID (str)
    """
    if name == "@":
        name = "HEAD"

    refs_to_try = [
        os.path.join(name),
        os.path.join("refs", name),
        os.path.join("refs", "tags", name),
        os.path.join("refs", "heads", name),
    ]

    for ref in refs_to_try:
        if data.get_ref(ref) is not None:
            result: str = data.get_ref(ref)
            return result

    is_hex = all(c in string.hexdigits for c in name)
    if len(name) == 40 and is_hex:
        return name

    print("already oid")
    assert False, f"Unknown name {name}"


def is_ignored(path: str) -> bool:
    """
    Helper function to check if a folder is ignored
    .ugit by default

    Args: Path (str)
    Returns: bool
    """
    # multiple slashes to account for different os
    for delimiter in ["/", "\\"]:
        path = path.replace(delimiter, " ")
    return ".ugit" in path.split(" ")
