import argparse
import os
import sys

from . import data
from . import base


def main() -> None:
    args = parse_args()
    args.func(args)


def parse_args():
    parser = argparse.ArgumentParser()

    commands = parser.add_subparsers(dest="command")
    commands.required = True

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument("object")

    read_tree_parser = commands.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument("tree")

    write_tree_parser = commands.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    commit_parser = commands.add_parser("commit")
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument("-m", "--message", required=True)

    return parser.parse_args()


def init(args) -> None:
    """
    Initialize the ugit repository
    Args: None
    Returns: None
    """
    data.init()
    print(f"Initialized empty ugit repository in {os.getcwd()}/{data.GIT_DIR}")


def hash_object(args) -> None:
    """
    Create hashed object
    Args: file location
    Returns: Object Id
    """
    with open(args.file, "rb") as f:
        print(data.hash_object(f.read()))


def cat_file(args) -> None:
    """
    display the file.

    Args: Object Id
    Returns: None
    """
    _ = sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))


def write_tree(args) -> None:
    print(base.write_tree())


def read_tree(args) -> None:
    base.read_tree(args.tree)


def commit(args) -> None:
    print(base.commit(args.message))
