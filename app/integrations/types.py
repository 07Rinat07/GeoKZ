from enum import StrEnum


class SyncMode(StrEnum):
    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"


class SyncRunStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ExternalRecordStatus(StrEnum):
    STAGED = "STAGED"
    UNCHANGED = "UNCHANGED"
    CHANGED = "CHANGED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class EntityLinkStatus(StrEnum):
    AUTO_MATCHED = "AUTO_MATCHED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class MatchMethod(StrEnum):
    EXACT_ID = "EXACT_ID"
    EXACT_NAME = "EXACT_NAME"
    ALIAS = "ALIAS"
    SPATIAL = "SPATIAL"
    FUZZY = "FUZZY"
    MANUAL = "MANUAL"
