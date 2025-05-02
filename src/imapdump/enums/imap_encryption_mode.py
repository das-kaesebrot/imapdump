from enum import StrEnum, auto


class ImapEncryptionMode(StrEnum):
    NONE = auto()
    SSL = auto()
    STARTTLS = auto()

    @staticmethod
    def list():
        return list(map(lambda c: c.value, ImapEncryptionMode))
