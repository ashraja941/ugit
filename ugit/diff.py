from collections import defaultdict


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
        if o_from != o_to:
            output += f"changed: {path}\n"
    return output
