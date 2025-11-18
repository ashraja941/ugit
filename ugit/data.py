from codecs import getreader
from contextlib import contextmanager
import os
import hashlib
from typing import NamedTuple
import shutil


git_dir = ".ugit"


class RefValue(NamedTuple):
    """
    Type to represent the return value from references
    Contains Symbolic status and value
    """

    symbolic: bool
    value: str | None


@contextmanager
def change_git_dir(new_dir: str):
    """
    Temporarily point GIT_DIR at the given directory while executing a block.
    """
    global git_dir
    old_dir = git_dir
    git_dir = os.path.join(new_dir, ".ugit")
    yield
    git_dir = old_dir


def init() -> None:
    """
    Creates the ugit directory if it doesn't exist
    """
    os.makedirs(git_dir)
    os.makedirs(f"{git_dir}/objects")


def hash_object(data: bytes, type_: str = "blob") -> str:
    """
    create Object ID (Hash) for object using type, null, and data
    Stores the result in the objects/ directory in .ugit

    Args: Data (bytes), type_ (str)
    Returns: OID (str)
    """
    obj = type_.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest()

    # handle using correct slashes in all os
    out_file_location: str = os.path.join(git_dir, "objects", oid)

    # Create a objects folder if it doesn't exist
    os.makedirs(os.path.dirname(out_file_location), exist_ok=True)
    with open(out_file_location, "wb") as out:
        _ = out.write(obj)
    return oid


def get_object(object: str, expected: str | None = "blob") -> bytes:
    """
    Finds the data present at OID
    Has inbuild type checking

    Args: OID (str), expected (str)
    Returns: Data (Bytes)
    """
    object_location: str = os.path.join(git_dir, "objects", object)

    with open(object_location, "rb") as f:
        obj = f.read()

    type_, _, content = obj.partition(b"\x00")
    type_ = type_.decode()

    if expected is not None:
        assert type_ == expected, f"Expected {expected}, got {type_}"
    return content


def update_ref(ref: str, value: RefValue, deref: bool = True) -> None:
    """
    Set REF to the OID

    Args: OID (str)
    Returns: None
    """
    assert value.value is not None

    if value.symbolic:
        resultantValue: str = f"ref: {value.value}"
    else:
        resultantValue = value.value

    ref = _get_ref_internal(ref, deref)[0]
    ref_location: str = os.path.join(git_dir, ref)
    os.makedirs(os.path.dirname(ref_location), exist_ok=True)
    with open(ref_location, "w") as f:
        # if value.value is not None:
        _ = f.write(resultantValue)


def get_ref(ref: str, deref: bool = True) -> RefValue:
    """
    Retreive the REF and whether its symbolic

    Args: None
    Returns: RefValue
    """
    return _get_ref_internal(ref, deref=deref)[1]


def delete_ref(ref: str, deref: bool = True):
    """
    Remove the specified ref file.
    """
    ref = _get_ref_internal(ref, deref)[0]
    path_to_remove = os.path.join(git_dir, ref)
    os.remove(path_to_remove)


def _get_ref_internal(ref: str, deref: bool) -> tuple[str, RefValue]:
    """
    Internal function to dereference symbolic references
    returns the final symbolic ref along with it's OID
    """
    ref_path: str = os.path.join(git_dir, ref)
    value: str | None = None
    if os.path.isfile(ref_path):
        with open(ref_path, "r") as f:
            value = f.read().strip()

    symbolic: bool = bool(value) and value.startswith("ref:")
    if symbolic and value is not None:
        value = value.split(":", 1)[1].strip()
        if deref:
            return _get_ref_internal(value, deref=True)

    return ref, RefValue(symbolic=symbolic, value=value)


def iter_refs(prefix: str = "", deref: bool = True):
    """
    Internal function to Iterate through references directory

    Args: deref (bool)
    Returns: None
    """
    refs: list[str] = ["HEAD", "MERGE_HEAD"]

    for root, _, filenames in os.walk(os.path.join(git_dir, "refs")):
        rel_path = os.path.relpath(root, git_dir)
        refs.extend(os.path.join(rel_path, filename) for filename in filenames)

    for ref_name in refs:
        if not ref_name.startswith(prefix):
            continue
        ref = get_ref(ref_name, deref=deref)
        if ref.value:
            yield ref_name, ref


def object_exists(oid):
    path = os.path.join(git_dir, "objects", oid)
    return os.path.isfile(path)


def fetch_object_if_missing(oid, remote_git_dir):
    if object_exists(oid):
        return

    remote_git_dir = os.path.join(remote_git_dir, "ugit")
    from_path = os.path.join(remote_git_dir, "objects", oid)
    to_path = os.path.join(git_dir, "objects", oid)

    shutil.copy(from_path, to_path)
