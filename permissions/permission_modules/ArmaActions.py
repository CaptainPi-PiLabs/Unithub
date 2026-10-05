from enum import Enum


class ArmaActions(str, Enum):
    CHECK_PLAYER = "check_player"
    READ_WHITELIST = "read_whitelist"
    ADD_WHITELIST = "add_whitelist"
    REMOVE_WHITELIST = "remove_whitelist"