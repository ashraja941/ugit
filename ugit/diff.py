from collections import defaultdict
from dataclasses import dataclass
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
    """
    Yield the files that differ between the two trees with a descriptive action.
    """
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            action = (
                "New File " if not o_from else "Deleted " if not o_to else "modified"
            )
            yield path, action


def diff_DHEAD(head_text: str, other_text: str, macro="HEAD"):
    """
    Interleave two text versions, keeping HEAD sections unless they differ.
    """
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


@dataclass
class _Change:
    """
    Small helper structure representing a single contiguous edit block.
    """

    start: int
    end: int
    text: list[str]


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

    def collect_changes(sm: difflib.SequenceMatcher, seq: list[str]) -> list[_Change]:
        changes: list[_Change] = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            changes.append(_Change(i1, i2, seq[j1:j2]))
        return changes

    head_changes = collect_changes(sm_head, head)
    other_changes = collect_changes(sm_other, other)

    def materialize(
        changes: list[_Change], start: int, end: int, fallback: list[str]
    ) -> list[str]:
        """Build the text for one side over base[start:end]."""
        out: list[str] = []
        cursor = start
        for change in changes:
            if cursor < change.start:
                out.extend(fallback[cursor : change.start])
                cursor = change.start
            out.extend(change.text)
            cursor = change.end
        if cursor < end:
            out.extend(fallback[cursor:end])
        return out

    def overlaps(change: _Change, region_end: int) -> bool:
        if change.start < region_end:
            return True
        return change.start == region_end and change.start == change.end

    output: list[str] = []
    pos = 0
    i_h = 0
    i_o = 0
    base_len = len(base)

    while pos < base_len or i_h < len(head_changes) or i_o < len(other_changes):
        next_head = head_changes[i_h].start if i_h < len(head_changes) else base_len
        next_other = other_changes[i_o].start if i_o < len(other_changes) else base_len
        next_event = min(next_head, next_other, base_len)

        if pos < next_event:
            output.extend(base[pos:next_event])
            pos = next_event
            continue

        conflict_start = pos
        region_end = pos
        region_head: list[_Change] = []
        region_other: list[_Change] = []

        if i_h < len(head_changes) and head_changes[i_h].start == pos:
            region_head.append(head_changes[i_h])
            region_end = max(region_end, head_changes[i_h].end)
            i_h += 1

        if i_o < len(other_changes) and other_changes[i_o].start == pos:
            region_other.append(other_changes[i_o])
            region_end = max(region_end, other_changes[i_o].end)
            i_o += 1

        expanded = True
        while expanded:
            expanded = False
            if i_h < len(head_changes) and overlaps(head_changes[i_h], region_end):
                region_head.append(head_changes[i_h])
                region_end = max(region_end, head_changes[i_h].end)
                i_h += 1
                expanded = True
            if i_o < len(other_changes) and overlaps(other_changes[i_o], region_end):
                region_other.append(other_changes[i_o])
                region_end = max(region_end, other_changes[i_o].end)
                i_o += 1
                expanded = True

        if region_head and region_other:
            head_version = materialize(region_head, conflict_start, region_end, base)
            other_version = materialize(region_other, conflict_start, region_end, base)
            base_chunk = base[conflict_start:region_end]

            if head_version == other_version:
                output.extend(head_version)
            else:
                output.append(f"<<<<<<< {label_head}\n")
                output.extend(head_version)
                output.append(f"||||||| {label_base}\n")
                output.extend(base_chunk)
                output.append("=======\n")
                output.extend(other_version)
                output.append(f">>>>>>> {label_other}\n")
        elif region_head:
            output.extend(materialize(region_head, conflict_start, region_end, base))
        elif region_other:
            output.extend(materialize(region_other, conflict_start, region_end, base))
        else:
            if pos < base_len:
                output.append(base[pos])
                pos += 1
                continue

        pos = max(region_end, conflict_start)

    return "".join(output)


def merge_trees(t_base, t_head, t_other):
    """
    Run a three-way merge across tree dictionaries and return the merged tree.
    """
    tree = {}
    for path, o_base, o_head, o_other in compare_trees(t_base, t_head, t_other):
        blob = merge_blobs(o_base, o_head, o_other)
        if blob is None:
            continue
        tree[path] = blob
    return tree


def merge_blobs(o_base: str | None, o_head: str | None, o_other: str | None):
    """
    Merge three blob IDs and return conflict-marked content if needed.
    """
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
