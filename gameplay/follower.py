"""Guarded native party-follower initialization and deferred refresh hooks."""
from dataclasses import replace as rename
import struct
import ndspy.code
from .field import fingerprint,replace,thumb_call,OverlayPatch

def install_follower(rom,payload):
    arm=bytearray(rom.arm9);base=rom.arm9RamAddress
    for address,size,digest in (
        (0x020699f8,0x17c,'d97852464f630ccad9e8dae5c9b82187f8aa08896b63c7f81fb97a980bb91125'),
        (0x02069b74,0x1f4,'f5c15098f1fdb3d73834083ee61eb8897c4c13086598794feb327322664742e3'),
        (0x02069ff4,0x4c,'3f0727e1ca030890da96b1887f27a304d35508e7e937c0dfaf813d51b2e25ceb'),
        (0x0205f1e4,0x4,'4b547d6e4f8ab8fc7b567fb65c7496a439768c56e470b6ce365a5b832d81c006'),
    ):
        fingerprint(arm,base,address,size,digest)
    main=[]
    for site,original,symbol in ((0x02069A04,0x0205F1E5,'EnhancedFollowerField'),
            (0x02069B7A,0x0205F1E5,'EnhancedFollowerField'),
            (0x02069A64,0x02069FF5,'EnhancedFollowerPermission'),
            (0x02069BCE,0x02069FF5,'EnhancedFollowerPermission')):
        main.append(rename(replace(arm,base,site,thumb_call(site,original),
            thumb_call(site,payload.symbols[symbol]),symbol),feature='follower_control'))
    o=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda oid,fid:rom.files[fid],{1})[1]
    fingerprint(o.data,o.ramAddress,0x022059AC,0x88,'0ca8cbb472638495245ce532010b3447480a14ea3f6075f2287d7814bc70dcfc')
    site=0x02205A10
    patch=rename(replace(o.data,o.ramAddress,site,thumb_call(site,0x02069FF5),
        thumb_call(site,payload.symbols['EnhancedFollowerPermission']),
        'Native deferred party-follower removal/recreation respects saved permission'),feature='follower_control')
    rom.files[o.fileID]=o.save(compress=False)
    table=bytearray(rom.arm9OverlayTable)
    for at in range(0,len(table),32):
        if struct.unpack_from('<I',table,at)[0]==1:
            table[at:at+32]=ndspy.code.saveOverlayTable({1:o});break
    else:raise ValueError('Native follower overlay descriptor is missing.')
    rom.arm9=bytes(arm);rom.arm9OverlayTable=bytes(table)
    return main,[OverlayPatch(1,o.fileID,patch)]
