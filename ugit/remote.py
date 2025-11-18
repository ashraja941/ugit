from . import data

import os


def fetch(remote_path: str):
    print("Will fetch the following refs")
    heads_path = os.path.join("refs", "heads")
    for refname, _ in _get_remote_refs(remote_path, heads_path).items():
        print(f"- {refname}")


def _get_remote_refs(remote_path: str, prefix: str = ""):
    with data.change_git_dir(remote_path):
        return {refname: ref.value for refname, ref in data.iter_refs(prefix)}
