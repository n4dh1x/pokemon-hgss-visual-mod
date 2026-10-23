"""Guarded modern EXP callbacks plus one appended native battle-bank string."""
from dataclasses import replace as replace_record
import hashlib
import struct
import ndspy.code
import ndspy.narc
from .field import OverlayPatch, FilePatch, fingerprint, replace, thumb_call
from .messages import append_message, entries
from .patches import PatchMismatch

GROUP_TEXT = 'The rest of your team gained\nEXP. Points!'
ARCHIVE_SHA = '570433fadb7f2959c99e73ee446ad7bc770702dd71b472acf51c0e358a51136c'
BANK_SHA = 'cd45ea9f6ad249508c562c7c8967ee3929bec616a6aaa2034d329131180780bf'


def install_party_exp(rom, payload):
    overlay = ndspy.code.loadOverlayTable(rom.arm9OverlayTable,
        lambda oid, fid: rom.files[fid], {12})[12]
    for address, size, digest in (
        (0x02245898,2896,'a2bd10b089685b468573bdb5799af0998b25ee4a200f05a0c1f8d882767de550'),
        (0x0223E6A0,380,'e34511fdf98dd6f68a1756c9a8691a07a6626e1eb9bd31cd4144e1fe23c5cf6e'),
        (0x0223E81C,64,'84ff4d4227fe139383ba2a14c59cccbab35836666e22b156cdefffc525003c91'),
    ): fingerprint(overlay.data,overlay.ramAddress,address,size,digest)
    file_id = rom.filenames.idOf('a/0/2/7')
    if file_id is None or hashlib.sha256(rom.files[file_id]).hexdigest() != ARCHIVE_SHA:
        raise PatchMismatch('Native USA message archive differs from the audit.')
    archive = ndspy.narc.NARC(rom.files[file_id])
    if hashlib.sha256(archive.files[197]).hexdigest() != BANK_SHA or len(entries(archive.files[197])[1]) != 1276:
        raise PatchMismatch('Native battle message bank differs from the audit.')
    original_messages = list(archive.files)
    archive.files[197] = append_message(archive.files[197], GROUP_TEXT)
    data = archive.save()
    parsed = ndspy.narc.NARC(data)
    if any(before != after for i,(before,after) in enumerate(zip(original_messages,parsed.files)) if i != 197):
        raise PatchMismatch('Unrelated native message bank changed.')
    changes = []
    for site, old, new, behavior in (
        (0x0226C764,struct.pack('<I',0x0223E6A1),struct.pack('<I',payload.symbols['EnhancedCalcExperience']),'Modern full/half EXP calculation, original when disabled'),
        (0x0223E858,struct.pack('<I',0x02245899),struct.pack('<I',payload.symbols['EnhancedPartyExperienceTask']),'Eligible party recipients through the native EXP task'),
        (0x02245B62,thumb_call(0x02245B62,0x0223C495),thumb_call(0x02245B62,payload.symbols['EnhancedExperienceMessage']),'One collective message for bench rewards'),
    ):
        patch = replace(overlay.data,overlay.ramAddress,site,old,new,behavior)
        changes.append(OverlayPatch(12,overlay.fileID,replace_record(patch,feature='party_exp')))
    rom.files[overlay.fileID] = overlay.save(compress=False)
    table = bytearray(rom.arm9OverlayTable)
    for offset in range(0,len(table),32):
        if struct.unpack_from('<I',table,offset)[0] == 12:
            table[offset:offset+32] = ndspy.code.saveOverlayTable({12:overlay})
            break
    rom.arm9OverlayTable = bytes(table)
    rom.files[file_id] = data
    asset = FilePatch(file_id,'party_exp_message',ARCHIVE_SHA,hashlib.sha256(data).hexdigest(),data,
                      'Append owned English group message 1276; preserve every old message and other bank')
    return changes, [asset]
