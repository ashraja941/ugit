import os
import hashlib

GIT_DIR = ".ugit"


def init():
    os.makedirs(GIT_DIR)


def hash_object(data: bytes, type_: str = "blob") -> str:
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
    object_location: str = os.path.join(GIT_DIR, "objects", object)

    with open(object_location, "rb") as f:
        obj = f.read()

    type_, _, content = obj.partition(b"\x00")
    type_ = type_.decode()

    if expected is not None:
        assert type_ == expected, f"Expected {expected}, got {type_}"
    return content


def set_HEAD(oid: str) -> None:
    with open(os.path.join(GIT_DIR, "HEAD"), "w") as f:
        _ = f.write(oid)


def get_HEAD() -> str | None:
    HEAD_path: str = os.path.join(GIT_DIR, "HEAD")
    if os.path.isfile(HEAD_path):
        with open(HEAD_path, "r") as f:
            return f.read().strip()
