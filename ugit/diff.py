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


def diff3_merge(
    base_text: str,
    head_text: str,
    other_text: str,
    label_head="HEAD",
    label_base="BASE",
    label_other="MERGE_HEAD",
) -> str:
    """
    Pure Python 3-way merge (replacement for `diff3 -m`).
    Produces Git-style conflict markers.
    """

    base = base_text.splitlines(keepends=True)
    head = head_text.splitlines(keepends=True)
    other = other_text.splitlines(keepends=True)

    sm_head = difflib.SequenceMatcher(None, base, head)
    sm_other = difflib.SequenceMatcher(None, base, other)

    output = []
    i_h = i_o = 0

    while i_h < len(sm_head.get_opcodes()) and i_o < len(sm_other.get_opcodes()):
        op_h, bh1, bh2, hh1, hh2 = sm_head.get_opcodes()[i_h]
        op_o, bo1, bo2, oh1, oh2 = sm_other.get_opcodes()[i_o]

        # If both HEAD and OTHER changed the same base region → conflict
        if bh1 == bo1 and bh2 == bo2 and (op_h != "equal" or op_o != "equal"):
            output.append(f"<<<<<<< {label_head}\n")
            output.extend(head[hh1:hh2])
            output.append(f"||||||| {label_base}\n")
            output.extend(base[bh1:bh2])
            output.append("=======\n")
            output.extend(other[oh1:oh2])
            output.append(f">>>>>>> {label_other}\n")
            i_h += 1
            i_o += 1
            continue

        # If only HEAD changed
        if op_h != "equal":
            output.extend(head[hh1:hh2])
            i_h += 1
            continue

        # If only OTHER changed
        if op_o != "equal":
            output.extend(other[oh1:oh2])
            i_o += 1
            continue

        # If both equal → write base
        output.extend(base[bh1:bh2])
        i_h += 1
        i_o += 1

    return "".join(output)


def merge_trees(t_base, t_head, t_other):
    tree = {}
    for path, o_base, o_head, o_other in compare_trees(t_base, t_head, t_other):
        blob = merge_blobs(o_base, o_head, o_other)
        if blob is None:
            continue
        tree[path] = blob
    return tree


def merge_blobs(o_base: str | None, o_head: str | None, o_other: str | None):
    if o_head is None and o_other is None and o_base is None:
        return None

    if o_head is None:
        return data.get_object(o_other) if o_other is not None else None

    if o_other is None:
        return data.get_object(o_head)

    if o_base is None:
        return data.get_object(o_base) if o_base is not None else None

    head = data.get_object(o_head).decode()
    other = data.get_object(o_other).decode()
    base = data.get_object(o_base).decode()

    # result = diff_DHEAD(a, b)
    result = diff3_merge(base, head, other)
    return result.encode()
