import os
import hashlib

GIT_DIR = ".ugit"


def init():
    os.makedirs(GIT_DIR)


def hash_object(data: bytes):
    oid = hashlib.sha1(data).hexdigest()

    # handle using correct slashes in all os
    out_file_location: str = os.path.join(GIT_DIR, "objects", oid)

    # Create a objects folder if it doesn't exist
    os.makedirs(os.path.dirname(out_file_location), exist_ok=True)
    with open(out_file_location, "wb") as out:
        _ = out.write(data)
    return oid


def get_object(object) -> bytes:
    object_location: str = os.path.join(GIT_DIR, "objects", object)

    with open(object_location, "rb") as f:
        return f.read()
