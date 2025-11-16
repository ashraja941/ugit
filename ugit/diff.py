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


def iter_changed_files(t_from, t_to):
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            action = (
                "New File " if not o_from else "Deleted " if not o_to else "modified"
            )
            yield path, action


def diff_DHEAD(head_text: str, other_text: str, macro="HEAD"):
    head_lines = head_text.splitlines(keepends=True)
    other_lines = other_text.splitlines(keepends=True)

    sm = difflib.SequenceMatcher(None, head_lines, other_lines)
    output = []

    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            output.extend(head_lines[i1:i2])
        elif op == "replace":
            # output.append(f"#ifdef {macro}\n")
            output.extend(head_lines[i1:i2])
            # output.append("#else\n")
            output.extend(other_lines[j1:j2])
            # output.append("#endif\n")
        elif op == "delete":
            # output.append(f"#ifdef {macro}\n")
            output.extend(head_lines[i1:i2])
            # output.append("#endif\n")
        elif op == "insert":
            # output.append("#else\n")
            output.extend(other_lines[j1:j2])
            # output.append("#endif\n")

    return "".join(output)


def merge_trees(t_head, t_other):
    tree = {}
    for path, o_head, o_other in compare_trees(t_head, t_other):
        tree[path] = merge_blobs(o_head, o_other)
    return tree


def merge_blobs(o_head: str | None, o_other: str | None):
    a, b = None, None
    if o_head is not None:
        a = data.get_object(o_head).decode()
    if o_other is not None:
        b = data.get_object(o_other).decode()

    result = diff_DHEAD(a, b)
    return result.encode()
