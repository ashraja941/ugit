from . import data
from . import base

import os

REMOTE_REFS_BASE = os.path.join("refs", "heads")
LOCAL_REFS_BASE = os.path.join("refs", "remote")


def fetch(remote_path: str):
    heads_path = os.path.join("refs", "heads")
    refs = _get_remote_refs(remote_path, REMOTE_REFS_BASE)

    for oid in base.iter_objects_in_commit(refs.values()):
        data.fetch_object_if_missing(oid, remote_path)

    for remote_name, value in refs.items():
        refname = os.path.relpath(remote_name, REMOTE_REFS_BASE)
        local_path = os.path.join(LOCAL_REFS_BASE, refname)
        data.update_ref(local_path, data.RefValue(symbolic=False, value=value))


def _get_remote_refs(remote_path: str, prefix: str = ""):
    with data.change_git_dir(remote_path):
        return {refname: ref.value for refname, ref in data.iter_refs(prefix)}


def push(remote_path: str, refname: str):
    local_ref = data.get_ref(refname).value
    assert local_ref

    objects_to_push = base.iter_objects_in_commit({local_ref})

    for oid in objects_to_push:
        data.push_object(oid, remote_path)

    with data.change_git_dir(remote_path):
        data.update_ref(refname, data.RefValue(symbolic=False, value=local_ref))
