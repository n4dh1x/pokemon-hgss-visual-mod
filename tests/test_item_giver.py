"""All-pocket item selection and original native Bag arithmetic/sorting."""
from pathlib import Path
import struct
import unittest
import ndspy.narc
import test_settings as api
from gameplay.items import audit_items, item_pocket_table, MAIN_CONTEXTS
from gameplay.messages import entries
ROOT=Path(__file__).resolve().parent.parent

def name_codes(data,index):
    _, spans=entries(data);start,n=spans[index];seed=((index+1)*596947)&0xffff
    values=[]
    for value in struct.unpack_from('<'+str(n)+'H',data,start):
        values.append(value^seed);seed=(seed+18749)&0xffff
    if values[0]!=0xF100:return values
    out=[];bits=0;available=0
    for value in values[1:]:
        bits|=(value&0x7fff)<<available;available+=15
        while available>=9:
            code=bits&511;bits>>=9;available-=9
            if code==511:return out+[0xffff]
            out.append(code)
    raise ValueError('Compressed native item name lacks terminator.')

@unittest.skipUnless(api.AVAILABLE,'Install native ARM dependencies.')
class TestItemGiver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=api.build_payload()
        cls.payload.symbols['NativeBagSlot']=0x02078725
        cls.rom=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds')
        data=ndspy.narc.NARC(cls.rom.getFileByName('a/0/1/7'))
        names=ndspy.narc.NARC(cls.rom.getFileByName('a/0/2/7')).files[222]
        cls.mapping=[struct.unpack_from('<H',cls.rom.arm9,0x100194+i*8)[0] for i in range(537)]
        cls.pockets=[(struct.unpack_from('<H',data.files[m],8)[0]>>7)&15 for m in cls.mapping]
        cls.names=[name_codes(names,i) for i in range(537)]

    def setUp(self):
        owner=self;self.safari=self.contest=self.palpark=self.tower=self.inhibit=0
        self.bag=0x02220020;self.name=0x02224000;self.events=[];self.name_override={}
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,context):
                if 0x02078240<=address<0x0207879C:return # Original Bag helpers, sorting and getters.
                a,b,c,d=[uc.reg_read(reg) for reg in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)]
                result=0
                if address==0x02077D88:
                    owner.assertEqual((b,c),(5,4));owner.assertIn(a,range(1,537));result=owner.pockets[a]
                elif address==0x02077D40:
                    owner.assertIn(a,(owner.name,0x02213300));owner.assertEqual(c,4)
                    codes=owner.name_override.get(b,owner.names[b]);text=codes[:-1] if codes and codes[-1]==0xffff else codes
                    uc.mem_write(a,struct.pack('<HHI',64,len(text),0xB6F8D2EC)+struct.pack('<'+str(len(text)+1)+'H',*text,0xffff));owner.events.append(('name',b))
                elif address==0x0207879C:
                    owner.assertEqual(a,f.save);result=owner.bag
                elif address==0x020503D0: result=0x02225000
                elif address==0x02066860: result=owner.safari
                elif address==0x02066870: result=owner.contest
                elif address==0x020668A0: result=owner.palpark
                elif address==0x02067584: result=owner.tower
                elif address==0x0203BE60: result=owner.inhibit
                elif address==0x0200604C: owner.events.append(('sound',a))
                else:return super().hook(uc,address,size,context)
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        self.f=Fixture();self.f.payload=self.payload;self.f.setUp()
        self.f.uc.mem_write(0x02000000,bytes(self.rom.arm9))
        self.f.execute('EnhancedSettingsEnsure',self.f.field)
        self.extra=self.payload.symbols['gEnhancedExtraOptions'];self.ui=self.payload.symbols['gItemUi']
        self.f.uc.mem_write(self.bag-32,b'\xa5'*32);self.f.uc.mem_write(self.bag+0x79c,b'\x5a'*32)
        self.profile_before=bytes(self.f.uc.mem_read(self.f.profile,64))

    def prefs(self,pocket,item,count):
        for offset,value in ((56,pocket),(60,item),(64,count)):self.f.put(self.extra+offset,value)
    def give(self,pocket,item,count):
        self.prefs(pocket,item,count)
        result=self.f.execute('EnhancedGiveItem',self.f.field,self.extra,self.name)
        self.assertEqual(bytes(self.f.uc.mem_read(self.f.profile,64)),self.profile_before)
        self.assertEqual(bytes(self.f.uc.mem_read(self.bag-32,32)),b'\xa5'*32)
        self.assertEqual(bytes(self.f.uc.mem_read(self.bag+0x79c,32)),b'\x5a'*32)
        self.assertEqual(self.f.writes,[])
        return result
    def slot(self,pocket,n):return self.f.execute('NativeBagSlot',self.bag,pocket,n)
    def quantity(self,pocket,item):
        for n in range((165,40,24,101,64,12,30,50)[pocket]):
            at=self.slot(pocket,n);i,q=struct.unpack('<HH',self.f.uc.mem_read(at,4))
            if i==item:return q
        return 0

    def test_all_eight_native_pockets_and_five_counts_add_only_the_requested_stack(self):
        for pocket,item in enumerate((79,17,4,328,149,137,55,536)):
            self.assertEqual(self.pockets[item],pocket)
            for count,quantity in enumerate((1,5,10,50,99)):
                self.f.uc.mem_write(self.bag,b'\0'*0x79c)
                self.assertEqual(self.give(pocket,item,count),1)
                self.assertEqual(self.quantity(pocket,item),1 if pocket==7 else quantity)
                self.assertEqual(self.f.get(self.ui+16),item)
                self.assertEqual(self.f.get(self.ui+20),1 if pocket==7 else quantity)
        self.assertEqual(self.f.get(self.ui+8),40)

    def test_native_general_and_machine_stack_caps_fail_without_changing_the_bag(self):
        for pocket,item,cap in ((0,79,999),(1,17,999),(2,4,999),(3,328,99),(4,149,999),(5,137,999),(6,55,999)):
            self.f.uc.mem_write(self.bag,b'\0'*0x79c);at=self.slot(pocket,0)
            self.f.uc.mem_write(at,struct.pack('<HH',item,cap));before=bytes(self.f.uc.mem_read(self.bag,0x79c))
            self.assertEqual(self.give(pocket,item,0),4)
            self.assertEqual(bytes(self.f.uc.mem_read(self.bag,0x79c)),before)
            self.f.uc.mem_write(at+2,struct.pack('<H',cap-1));self.assertEqual(self.give(pocket,item,0),1)
            self.assertEqual(self.quantity(pocket,item),cap)
        self.assertEqual(self.f.get(self.ui+12),7)

    def test_full_native_pockets_with_distinct_valid_items_reject_a_new_item_without_partial_writes(self):
        for pocket,capacity in ((0,165),(2,24),(7,50)):
            valid=[i for i in range(1,537) if self.mapping[i] and self.pockets[i]==pocket and self.names[i][0] not in (428,0xffff)]
            self.assertGreater(len(valid),capacity)
            self.f.uc.mem_write(self.bag,b'\0'*0x79c)
            for slot,item in enumerate(valid[:capacity]):
                self.f.uc.mem_write(self.slot(pocket,slot),struct.pack('<HH',item,1))
            before=bytes(self.f.uc.mem_read(self.bag,0x79c))
            self.assertEqual(self.give(pocket,valid[capacity],0),4)
            self.assertEqual(bytes(self.f.uc.mem_read(self.bag,0x79c)),before)
        self.assertEqual(self.f.get(self.ui+12),3)

    def test_key_items_are_unique_and_native_berry_and_machine_sorting_is_retained(self):
        self.assertEqual(self.give(7,536,4),1);before=bytes(self.f.uc.mem_read(self.bag,0x79c))
        self.assertEqual(self.give(7,536,4),3);self.assertEqual(bytes(self.f.uc.mem_read(self.bag,0x79c)),before)
        for pocket,ids in ((3,(330,329,328)),(4,(151,150,149))):
            for item in ids:self.assertEqual(self.give(pocket,item,0),1)
            self.assertEqual([struct.unpack('<H',self.f.uc.mem_read(self.slot(pocket,n),2))[0] for n in range(3)],sorted(ids))

    def test_invalid_unused_placeholder_and_wrong_pocket_entries_are_never_given(self):
        for item,pocket in ((0,0),(537,0),(428,0),(113,0),(17,0),(4,8)):
            self.assertEqual(self.f.execute('EnhancedItemValid',item,pocket,self.name),0)
        self.name_override[79]=[428,428,428,0xffff]
        self.assertEqual(self.give(0,79,0),5)
        self.name_override[79]=[0xffff];self.assertEqual(self.give(0,79,0),5)
        self.name_override={};self.assertEqual(self.give(0,79,5),5)
        self.assertEqual(bytes(self.f.uc.mem_read(self.bag,0x79c)),b'\0'*0x79c)

    def test_picker_wraps_and_skips_every_native_unused_or_wrong_pocket_item(self):
        for pocket in range(8):
            expected=[i for i in range(1,537) if self.mapping[i] and self.pockets[i]==pocket and self.names[i][0] not in (428,0xffff)]
            self.assertTrue(expected);self.prefs(pocket,0,0)
            self.f.execute('EnhancedItemStep',self.extra,1,self.name)
            self.assertEqual(self.f.get(self.extra+60),expected[0])
            for item in expected[1:]+expected[:1]:
                self.f.execute('EnhancedItemStep',self.extra,1,self.name);self.assertEqual(self.f.get(self.extra+60),item)
            self.f.execute('EnhancedItemStep',self.extra,0xffffffff,self.name);self.assertEqual(self.f.get(self.extra+60),expected[-1])

    def test_ownership_native_bag_permissions_and_save_mismatch_block_without_mutation(self):
        for mode in ('contest','palpark','tower','inhibit','owner','save','unloaded'):
            self.contest=self.palpark=self.tower=self.inhibit=0
            old_owner=self.f.owner;self.f.put(self.f.field+12,self.f.save);self.f.put(self.f.state+8,1)
            if mode in ('contest','palpark','tower'):setattr(self,mode,1)
            elif mode=='inhibit':self.inhibit=4
            elif mode=='owner':self.f.owner^=1
            elif mode=='save':self.f.put(self.f.field+12,self.f.save+4)
            else:self.f.put(self.f.state+8,0)
            self.assertEqual(self.give(0,79,0),2)
            self.assertEqual(bytes(self.f.uc.mem_read(self.bag,0x79c)),b'\0'*0x79c);self.f.owner=old_owner
        self.f.put(self.f.state+8,1);self.f.put(self.f.field+12,self.f.save)
        self.safari=self.contest=self.palpark=self.tower=1;self.inhibit=4
        self.assertEqual(self.give(0,79,0),1) # Native Safari precedence allows the Bag.

    def key(self,k):self.f.put(0x021D1154,k);return self.f.execute('EnhancedMenuTask',0)
    def open_picker(self):
        self.f.execute('EnhancedMenuOpen',self.f.field);self.key(0);self.key(0x200)
        for _ in range(5):self.key(0x80)
        self.key(1);self.assertEqual(self.f.get(self.f.menu+28),4)

    def test_picker_B_and_menu_Cancel_discard_preferences_without_giving_or_flash_writes(self):
        self.open_picker();self.key(0x10);self.key(0x80);self.key(0x10);self.key(0x80);self.key(0x10)
        self.key(2);self.assertEqual(self.f.get(self.f.menu+28),1)
        self.assertEqual(self.f.get(self.f.menu+116),1)
        self.key(2);self.assertEqual(tuple(self.f.get(self.extra+i) for i in (56,60,64)),(0,0,0))
        self.assertEqual(bytes(self.f.uc.mem_read(self.bag,0x79c)),b'\0'*0x79c);self.assertEqual(self.f.writes,[])

    def test_Give_is_immediate_but_preferences_and_other_switches_apply_only_on_settings_Save(self):
        self.open_picker()
        self.f.put(self.f.menu+36,0) # Staged trade switch is independent of giving.
        for _ in range(3):self.key(0x80)
        item=self.f.get(self.f.menu+120);self.assertNotEqual(item,0)
        self.key(1);self.assertEqual(self.quantity(0,item),1)
        self.assertEqual(self.f.values()[0],1);self.assertEqual(self.f.writes,[])
        self.key(2);self.f.put(self.f.menu+32,6);self.key(1);self.key(0)
        self.assertEqual(self.f.values()[0],0)
        self.assertEqual(self.f.get(self.extra+60),item);self.assertEqual(self.quantity(0,item),1)
        self.assertEqual(len(self.f.writes),1)

    def test_idle_picker_does_not_reload_names_or_repeat_giving(self):
        self.open_picker();before=len(self.events)
        for _ in range(20):self.key(0)
        self.assertEqual(len(self.events),before);self.assertEqual(self.f.get(self.ui+8),0)

    def test_resident_lookup_matches_every_native_record_in_both_games_and_has_no_committed_asset(self):
        expected=None
        for game in ('heartgold','soulsilver'):
            rom=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds')
            table=item_pocket_table(rom);self.assertEqual(len(table),269)
            if expected is not None:self.assertEqual(table,expected)
            expected=table
            for item in range(537):
                actual=(table[item//2]>>((item&1)*4))&15
                self.assertEqual(actual,self.pockets[item] if self.mapping[item] else 15)
            self.assertEqual(table[-1]>>4,15)
        at=self.payload.symbols['gItemPocketTable']-api.PAYLOAD_BASE
        self.assertEqual(self.payload.data[at:at+269],expected)
        self.assertFalse((ROOT/'native/item_pockets.bin').exists())
        with self.assertRaises(api.PatchMismatch):api.build_payload(item_pockets=bytes(268))

    def test_both_baselines_guard_native_bag_item_mapping_data_and_names(self):
        for game in ('heartgold','soulsilver'):
            original=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds');before=original.save();audit_items(original);self.assertEqual(original.save(),before)
            for address,size,digest in MAIN_CONTEXTS:
                bad=api.ndspy.rom.NintendoDSRom(before);arm=bytearray(bad.arm9);arm[address-bad.arm9RamAddress]^=1;bad.arm9=bytes(arm)
                with self.assertRaises(api.PatchMismatch):audit_items(bad)
            bad=api.ndspy.rom.NintendoDSRom(before);data=bytearray(bad.getFileByName('a/0/1/7'));data[-1]^=1;bad.setFileByName('a/0/1/7',bytes(data))
            with self.assertRaises(api.PatchMismatch):audit_items(bad)
            bad=api.ndspy.rom.NintendoDSRom(before);n=ndspy.narc.NARC(bad.getFileByName('a/0/2/7'));data=bytearray(n.files[222]);data[-1]^=1;n.files[222]=bytes(data);bad.setFileByName('a/0/2/7',n.save())
            with self.assertRaises(api.PatchMismatch):audit_items(bad)
