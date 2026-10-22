"""Small, fail-closed patches on the verified USA Visual+ reference builds."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


class PatchMismatch(ValueError):
    """The supplied game code does not match the audited patch site."""


@dataclass(frozen=True)
class PatchResult:
    feature: str
    address: int
    before: str
    after: str
    behavior: str


LEARN_MOVE_ADDRESS = 0x0208254C
LEARN_MOVE_LENGTH = 0x8C
LEARN_MOVE_SHA256 = '34189c89775cad68df9d02415042ca6ea067f0fbe7ed0e8246a1be183dc7c98b'
TAKE_TM_ADDRESS = 0x020825B4
TAKE_TM_CALL = bytes.fromhex('f5f73eff')
THUMB_NOP_PAIR = bytes.fromhex('c046c046')


def reusable_tms(arm9: bytearray, ram_address: int, destination: int | None = None) -> PatchResult:
    """Keep TMs while retaining move/PP initialization, friendship and mood.

    Audited independently in the USA HeartGold and SoulSilver Visual+ full
    outputs. PartyMenu_LearnMoveToSlot calls Bag_TakeItem at this site only
    when an item is supplied and the move is not an HM. The common teaching
    paths, including replacing an existing move, use this function.

    With a destination, call the resident runtime option wrapper. Omitting it
    retains the original static milestone patch for regression comparisons.
    Hiding the remaining bag quantity label is separate integration work.
    """
    function_offset = LEARN_MOVE_ADDRESS - ram_address
    patch_offset = TAKE_TM_ADDRESS - ram_address
    if function_offset < 0 or function_offset + LEARN_MOVE_LENGTH > len(arm9):
        raise PatchMismatch('PartyMenu_LearnMoveToSlot falls outside ARM9.')
    code = arm9[function_offset:function_offset + LEARN_MOVE_LENGTH]
    if hashlib.sha256(code).hexdigest() != LEARN_MOVE_SHA256:
        raise PatchMismatch('PartyMenu_LearnMoveToSlot differs from the audited USA code.')
    if arm9[patch_offset:patch_offset + 4] != TAKE_TM_CALL:
        raise PatchMismatch('Expected Bag_TakeItem call is not present.')
    if destination is None:
        replacement = THUMB_NOP_PAIR
        behavior = 'TMs retained after teaching; build-time enabled'
    else:
        from .field import thumb_call
        replacement = thumb_call(TAKE_TM_ADDRESS, destination)
        behavior = 'TM consumption follows the saved reusable-TM option'
    arm9[patch_offset:patch_offset + 4] = replacement
    return PatchResult('infinite_tms', TAKE_TM_ADDRESS, TAKE_TM_CALL.hex(),
                       replacement.hex(), behavior)
