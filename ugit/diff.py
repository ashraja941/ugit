from collections import defaultdict
import difflib
from . import data


def compare_trees(*trees: dict[str, str]):
    """
    Takes in any number of trees (dictionary of path and oid for all files in tree) and yields the path and oids for all the trees
    """
    entries: defaultdict[str, list[None | str]] = defaultdict(
        lambda: [None] * len(trees)
    )
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield (path, *oids)


def diff_trees(t_from: dict[str, str], t_to: dict[str, str]):
    """
    Compares 2 trees, if they have the same path, compare oid
    """
    output = ""
    for path, o_from, o_to in compare_trees(t_from, t_to):
        _ = path
        if o_from != o_to and o_from is not None and o_to is not None:
            # output += f"changed: {path}\n"
            output += diff_blobs(o_from, o_to)
    return output


def diff_blobs(t_from: str, t_to: str) -> str:
    """
    Display the difference between 2 files

    Args: OIDs of files
    Returns: str output
    """
    data_from = data.get_object(t_from).decode()
    data_to = data.get_object(t_to).decode()

    lines1 = data_from.splitlines()
    lines2 = data_to.splitlines()

    diff = difflib.unified_diff(
        lines1, lines2, fromfile="Previous", tofile="New", lineterm=""
    )
    return "\n".join(diff)
