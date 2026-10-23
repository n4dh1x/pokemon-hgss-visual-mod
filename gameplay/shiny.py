"""Target new wild, starter and gift creation; leave eggs/trades/fixed PIDs alone."""
from dataclasses import replace as rename
from .field import fingerprint,replace,thumb_call

def install_shiny(rom,payload):
    arm=bytearray(rom.arm9);base=rom.arm9RamAddress
    for address,size,digest in (
        (0x0206DE38,0x98,'ad138492771ff6e41ec0680d45eb0539a03cf52ca3915ee4e2307cdcc3e26c36'),
        (0x0206DED0,0x238,'2da800045eb0447b79f59a2d16a784a1f09240d294ce3115c46b13ae1027dfa2'),
        (0x0206E108,0x44,'39b359c819abba5c9c235eedc4cefd48997058153ce551f27ddf98bfc3dcac04'),
        (0x0206E14C,0xA0,'10f211341e16360f8cf96ec03a08bcf864246a0def171d0e24e3615d8b4f7482'),
        (0x020541DC,0xA8,'2ebd5d90a0df577cbeff462a0ca259500cf2568a528076bfb8cfdf64f6d87d93'),
        (0x020960A0,0x80,'3f4b82239433e3c732dda45b726a392c672cd4777be21ab5790cb550568c28e9'),
        (0x0206FE2C,0x14,'5275a557e104f05a735883e239185376e09792a6c5b68e85ec227a5bd04401d5'),
        (0x0206FBE8,0x28,'47315b771971aa537c493e450e36b2b1e822b677553f07ba71d6100b8af41c7d'),
    ):fingerprint(arm,base,address,size,digest)
    changes=[]
    for site,symbol in ((0x02054216,'EnhancedPlayerCreateMon'),
                        (0x020960E6,'EnhancedPlayerCreateMon'),
                        (0x0206E142,'EnhancedNatureCreateMon'),
                        (0x0206E1E4,'EnhancedGenderCreateMon')):
        changes.append(rename(replace(arm,base,site,thumb_call(site,0x0206DE39),
            thumb_call(site,payload.symbols[symbol]),
            'Saved shiny rolls on new eligible wild/starters/gifts; native creation and fixed/egg/trade identities retained'),feature='shiny_odds'))
    rom.arm9=bytes(arm)
    return changes
