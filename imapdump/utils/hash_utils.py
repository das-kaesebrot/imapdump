import hashlib


def filehash(filename: str) -> str:
    with open(filename, "rb", buffering=0) as f:
        return hashlib.file_digest(f, "md5").hexdigest()


def bytehash(byteobject) -> str:
    return hashlib.md5(byteobject).hexdigest()
