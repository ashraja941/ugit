import argparse
import subprocess
import os
import sys
import textwrap

from collections import defaultdict

from . import data
from . import base


def main() -> None:
    """
    This is the function that is called by the cli tool
    """
    args = parse_args()
    args.func(args)


def parse_args():
    """
    Helper function to parse argument
    """
    parser = argparse.ArgumentParser()

    oid = base.get_oid

    commands = parser.add_subparsers(dest="command")
    commands.required = True

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    _ = hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    _ = cat_file_parser.add_argument("object", type=oid)

    read_tree_parser = commands.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    _ = read_tree_parser.add_argument("tree", type=oid)

    write_tree_parser = commands.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    commit_parser = commands.add_parser("commit")
    commit_parser.set_defaults(func=commit)
    _ = commit_parser.add_argument("-m", "--message", required=True)

    log_parser = commands.add_parser("log")
    log_parser.set_defaults(func=log)
    _ = log_parser.add_argument("oid", default="@", type=oid, nargs="?")

    checkout_parser = commands.add_parser("checkout")
    checkout_parser.set_defaults(func=checkout)
    _ = checkout_parser.add_argument("commit")

    tag_parser = commands.add_parser("tag")
    tag_parser.set_defaults(func=tag)
    _ = tag_parser.add_argument("name")
    _ = tag_parser.add_argument("oid", default="@", type=oid, nargs="?")

    k_parser = commands.add_parser("k")
    k_parser.set_defaults(func=k)

    branch_parser = commands.add_parser("branch")
    branch_parser.set_defaults(func=branch)
    _ = branch_parser.add_argument("name", nargs="?")
    _ = branch_parser.add_argument("starting_point", default="@", type=oid, nargs="?")

    status_parser = commands.add_parser("status")
    status_parser.set_defaults(func=status)

    return parser.parse_args()


def init(args: argparse.Namespace) -> None:
    """
    Initialize the ugit repository

    Args: None
    Returns: None
    """
    _ = args
    base.init()
    print(f"Initialized empty ugit repository in {os.getcwd()}/{data.GIT_DIR}")


def hash_object(args: argparse.Namespace) -> None:
    """
    Create hashed object

    Args: file location
    Returns: Object Id
    """
    _ = args
    with open(args.file, "rb") as f:
        print(data.hash_object(f.read()))


def cat_file(args: argparse.Namespace) -> None:
    """
    display the file.

    Args: Object Id
    Returns: None
    """
    _ = sys.stdout.flush()
    _ = sys.stdout.buffer.write(data.get_object(args.object, expected=None))


def write_tree(args: argparse.Namespace) -> None:
    """
    Hash all objects and trees from the current directory

    Args: None
    Returns: None
    """
    print(base.write_tree())


def read_tree(args: argparse.Namespace) -> None:
    """
    Pass in the tree object ID and recursively go through all folders and replace files with the one from the tree hash passed before

    Args: Tree Object ID
    Returns: None
    """
    base.read_tree(args.tree)


def commit(args: argparse.Namespace) -> None:
    """
    Create a commit with a message

    Args: Commit Message
    Returns: None
    """
    base.commit(args.message)


def log(args: argparse.Namespace) -> None:
    """
    Pass in Object ID and get commit history

    Args: Object ID
    Returns: None
    """
    refs: defaultdict[str, list[str]] = defaultdict(list)

    for ref_name, ref_value in data.iter_refs():
        assert ref_value.value is not None
        refs[ref_value.value].append(ref_name)

    oids = args.oid
    oids = data.get_ref(oids)
    assert oids.value is not None

    for oid in base.iter_commits_and_parents({oids.value}):
        commit = base.get_commit(oid)

        refs_str = f" ({', '.join(refs[oid])})" if oid in refs else ""
        print(f"commit {oid} {refs_str}\n")
        print(textwrap.indent(commit.message, "     "))
        print("")


def checkout(args: argparse.Namespace) -> None:
    """
    Takes in a COMMIT OID and returns the state to said Commit

    Args: COMMIT OID (str)
    Returns: None
    """

    base.checkout(args.commit)


def tag(args: argparse.Namespace) -> None:
    """
    Link a Name to a commit for easy moving around

    Args: Name (str), <Optional> OID (str)
    Returns: None
    """
    print("Tag created for ", args.oid)
    base.create_tag(name=args.name, oid=args.oid)


def branch(args: argparse.Namespace) -> None:
    if not args.name:
        current = base.get_branch_name()
        for branch in base.iter_branch_names():
            prefix = "*" if branch == current else " "
            print(f"{prefix} {branch}")

    else:
        base.create_branch(args.name, args.starting_point)
        print(f"Branch {args.name} created at {args.starting_point[:10]}...")


def k(args: argparse.Namespace) -> None:
    """
    Print the commmit history graph
    """
    dot = "digraph commits {\n"
    oids: set[str] = set()
    for ref_name, ref_oid in data.iter_refs(deref=False):
        # print(ref_name, ref_oid)
        dot += f'"{ref_name}" [shape=note]\n'
        dot += f'"{ref_name}" -> "{ref_oid.value}"\n'
        if not ref_oid.symbolic and ref_oid.value is not None:
            oids.add(ref_oid.value)

    for oid in base.iter_commits_and_parents(oids):
        commit = base.get_commit(oid)
        # print(oid)
        dot += f'"{oid}" [shape=box style=filled label="{oid[:10]}"]\n'
        if commit.parent:
            dot += f'"{oid}" -> "{commit.parent}"\n'

    dot += "}"
    print(dot)
    proc = subprocess.Popen(
        ["dot", "-Tpng"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = proc.communicate(dot.encode())

    if err:
        print("Graphviz error:", err.decode())
    # Save to file
    out_file = "ugit_graph.png"
    with open(out_file, "wb") as f:
        _ = f.write(out)
    # print(out.decode())


def status(args: argparse.Namespace) -> None:
    _ = args
    head = base.get_oid("@")
    branch = base.get_branch_name()

    if branch:
        print(f"On branch {branch}")
    else:
        print(f"HEAD Detached at {head[10:]}")
