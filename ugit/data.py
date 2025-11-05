import os
import hashlib
from typing import NamedTuple


GIT_DIR = ".ugit"


class RefValue(NamedTuple):
    symbolic: bool
    value: str | None


def init() -> None:
    """
    Creates the ugit directory if it doesn't exist
    """
    os.makedirs(GIT_DIR)


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
    out_file_location: str = os.path.join(GIT_DIR, "objects", oid)

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
    object_location: str = os.path.join(GIT_DIR, "objects", object)

    with open(object_location, "rb") as f:
        obj = f.read()

    type_, _, content = obj.partition(b"\x00")
    type_ = type_.decode()

    if expected is not None:
        assert type_ == expected, f"Expected {expected}, got {type_}"
    return content


def update_ref(ref: str, value: RefValue) -> None:
    """
    Set REF to the OID

    Args: OID (str)
    Returns: None
    """
    assert not value.symbolic

    ref_location: str = os.path.join(GIT_DIR, ref)
    os.makedirs(os.path.dirname(ref_location), exist_ok=True)
    with open(ref_location, "w") as f:
        if value.value is not None:
            _ = f.write(value.value)


def get_ref(ref: str) -> RefValue:
    """
    Retreive the REF and whether its symbolic

    Args: None
    Returns: RefValue
    """
    return _get_ref_internal(ref)[1]


def _get_ref_internal(ref: str) -> tuple[str, RefValue]:
    """
    Internal function to dereference symbolic references
    returns the final symbolic ref along with it's OID
    """
    ref_path: str = os.path.join(GIT_DIR, ref)
    value: str | None = None
    if os.path.isfile(ref_path):
        with open(ref_path, "r") as f:
            value = f.read().strip()

    symbolic: bool = bool(value) and value.startswith("ref:")
    if symbolic and value is not None:
        value = value.split(":", 1)[1].strip()
        return _get_ref_internal(value)

    return ref, RefValue(symbolic=False, value=value)


def iter_refs():
    refs: list[str] = ["HEAD"]

    for root, _, filenames in os.walk(os.path.join(GIT_DIR, "refs")):
        rel_path = os.path.relpath(root, GIT_DIR)
        refs.extend(os.path.join(rel_path, filename) for filename in filenames)

    for ref_name in refs:
        yield ref_name, get_ref(ref_name)
