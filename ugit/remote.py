from . import data

import os

REMOTE_REFS_BASE = os.path.join("refs", "heads")
LOCAL_REFS_BASE = os.path.join("refs", "remote")


def fetch(remote_path: str):
    heads_path = os.path.join("refs", "heads")
    refs = _get_remote_refs(remote_path, REMOTE_REFS_BASE)

    for remote_name, value in refs.items():
        refname = os.path.relpath(remote_name, REMOTE_REFS_BASE)
        local_path = os.path.join(LOCAL_REFS_BASE, refname)
        data.update_ref(local_path, data.RefValue(symbolic=False, value=value))


def _get_remote_refs(remote_path: str, prefix: str = ""):
    with data.change_git_dir(remote_path):
        return {refname: ref.value for refname, ref in data.iter_refs(prefix)}
