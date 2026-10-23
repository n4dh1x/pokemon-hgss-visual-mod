"""Guard two native summary call sites; retain original data and screen layout."""
from dataclasses import replace as rename
from .field import fingerprint, replace, thumb_call

def install_summary_viewer(rom, payload):
    arm=bytearray(rom.arm9)
    for address,size,digest in (
        (0x02088424,300,'8661397b83fb43bd9c9d6f0ebf46956dc91c8c1bc5b6cbef228056a8bfe36314'),
        (0x02088b40,472,'6906b7756e0c1934a5561cdc535d3d54aecc3cd09fb2c3fa36a12f2f7a737472'),
        (0x0208cbd4,180,'85612322de9b6e5448b0bb0f748f950edb4d6d25c706fc3bb7decde751fef278'),
        (0x0208d178,764,'ac05fe2f3c19dc8222779b7d0cd9de99d57b2f25195fca112cfe53f635a4fe09'),
        (0x0208a520,68,'8593cee31489bcc52bab7dc2089a78356d0b0c6a1607ec94d9c77fb5305bb853'),
        (0x0208c778,128,'edd44e51eb2ad35998ea528d20dd68eaf4e55d6cd6d2a56544e5a14bcbc3de9b'),
        (0x0208c87c,76,'14e77ccbb0aa7b5bc48ccca6e5f9695c39dd9c16b19e07671a6d17e004660ea9'),
    ):fingerprint(arm,rom.arm9RamAddress,address,size,digest)
    records=[]
    for site,original,symbol in (
        (0x02088494,0x02088B41,'EnhancedSummaryInput'),
        (0x0208CC5A,0x0208D179,'EnhancedSummaryDraw'),
    ):
        records.append(rename(replace(arm,rom.arm9RamAddress,site,
            thumb_call(site,original),thumb_call(site,payload.symbols[symbol]),
            'Saved optional IV/EV summary views; native page navigation, data access and normal stats retained'),feature='ivs_evs'))
    rom.arm9=bytes(arm)
    return records
