"""Native Fly/Flash checks and callbacks with a real start-menu layout."""
from pathlib import Path
import struct,sys,unittest
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import test_settings as api

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestFieldHmBag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.payload=api.build_payload()
    def setUp(self):
        owner=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,context):
                if address==(f.payload.symbols['EnhancedBagFieldUser']&~1):
                    result=owner.slot
                elif any(lo<=address<hi for lo,hi in owner.native_ranges):return
                elif address in owner.apis:
                    a,b,c,d=[uc.reg_read(r) for r in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)]
                    owner.calls.append((address,a,b,c,d));result=0
                    if address==0x020784B0:result=int(owner.owned)
                    elif address in (0x0207879C,0x02074904,0x020503D0):result=0x02280000
                    elif address==0x0203B454:result=int(owner.fly_allowed)
                    elif address==0x02066644:result=int(owner.companion)
                    elif address==0x020666B4:result=int(owner.costume)
                    elif address==0x02066860:result=int(owner.safari)
                    elif address==0x020668A0:result=int(owner.palpark)
                    elif address==0x0206BD44:result=int(owner.alph)
                    elif address==0x0205064C:owner.assertEqual(a,owner.task);result=f.field
                    elif address==0x02050650:owner.assertEqual(a,owner.task);result=owner.menu
                    elif address==0x0201AA8C:
                        result=0x022A0000+len(owner.allocations)*0x100
                        owner.allocations.append((result,a,b))
                    elif address==0x02074644:result=0x022D0000
                    elif address==0x02067BF8:result=0x022D0100
                    elif address==0x0203EAB0:result=0x022B0000
                    elif address==0x0203E3FC:result=0x022B0100
                    elif address==0x02026354:
                        result=0x022C0000+len(owner.strings)*0x100
                        owner.strings.append((result,a,b))
                    elif address==0x021FEF48:result=7
                    elif address==0x021FB604:result=1
                    elif address==0x020168F4:result=owner.response
                    elif address==0x02020094:result=int(owner.printing)
                else:return super().hook(uc,address,size,context)
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        self.native_ranges=[(0x02067DF4,0x02067E10),(0x0206800C,0x020680E0),
            (0x020684A0,0x02068504),(0x02067F28,0x02067F4C),(0x02028F98,0x02028FD0),
            (0x0203C8F0,0x0203C8FC),(0x0203D758,0x0203D818)]
        self.apis={0x020784B0,0x0207879C,0x02074904,0x020503D0,0x0203B454,
            0x02066644,0x020666B4,0x02066860,0x020668A0,0x0206BD44,0x0205064C,0x02050650,
            0x0201AA8C,0x0201AB80,0x02074644,0x02067BF8,0x0203EAB0,0x020505C0,0x02064E18,0x0203E3FC,0x02026354,
            0x021FEB84,0x021FD788,0x021FFF24,0x021FB604,0x021FEF48,0x021FF004,
            0x021FF058,0x020168F4,0x02020094,0x020880CC}
        Fixture.payload=self.payload;self.f=Fixture('runTest');f=self.f;f.setUp()
        path=ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds'
        if not path.exists():self.skipTest('Build both local USA baselines first.')
        r=api.ndspy.rom.NintendoDSRom.fromFile(path);f.uc.mem_write(r.arm9RamAddress,bytes(r.arm9))
        self.app,self.view,self.menu,self.task,self.itemdata,self.indices=0x02230000,0x02231000,0x02232000,0x02233000,0x02234000,0x02235000
        self.extra=self.payload.symbols['gEnhancedExtraOptions'];self.state=self.payload.symbols['gFieldBagState']
        f.put(self.extra,1);f.put(self.app+0x234,self.view);f.put(self.view+0x70,self.menu+0x358)
        f.put(self.menu+0x36C,f.field);f.put(self.menu+0x374,f.field)
        f.uc.mem_write(self.menu+0x37C,struct.pack('<H',0x80))
        f.put(self.app+0x5E4,0x02236000);f.put(self.app+0x324,0x02236100)
        f.put(self.app+0x804,0x02236200);f.put(self.itemdata,self.task)
        f.uc.mem_write(f.profile+0x1A,bytes([16]))
        self.item(421);self.slot=2;self.owned=self.fly_allowed=True
        self.companion=self.costume=self.safari=self.palpark=self.alph=self.printing=False
        self.response=1;self.calls=[];self.allocations=[];self.strings=[]
    def item(self,item):
        self.f.uc.mem_write(self.view+0x66,struct.pack('<H',item))
        self.f.uc.mem_write(self.itemdata+4,struct.pack('<H',item))
    def called(self,address):return [c for c in self.calls if c[0]==address]
    def offer(self):return self.f.execute('EnhancedBagFieldSelect',self.app)
    def accept(self):
        self.assertEqual(self.offer(),13)
        self.assertEqual(self.f.execute('EnhancedBagFieldPrompt',self.app),13)
        self.assertEqual(self.f.execute('EnhancedBagFieldPrompt',self.app),13)
        return self.f.execute('EnhancedBagFieldPrompt',self.app)
    def test_context_adds_one_bounded_action_and_preserves_teaching_and_other_buttons(self):
        f=self.f;f.uc.mem_write(self.indices,bytes([0,255,8,255,11]))
        f.execute('EnhancedBagDrawContext',self.app,self.indices,5)
        self.assertEqual(bytes(f.uc.mem_read(self.indices,5)),bytes([0,9,8,255,11]))
        self.assertEqual(f.get(self.app+0x7F4),self.payload.symbols['EnhancedBagFieldSelect'])
        self.assertEqual(self.strings[0][1:],(32,6));self.assertEqual(len(self.called(0x021FEB84)),1)
        for problem in ('off','other_item','context','union','colosseum','occupied'):
            f.put(self.extra,problem!='off');self.item(397 if problem!='other_item' else 328)
            f.uc.mem_write(self.view+0x65,bytes([int(problem=='context')]))
            f.uc.mem_write(self.view+0x76,struct.pack('<H',4 if problem=='union' else 6 if problem=='colosseum' else 0))
            before=bytes([0,8 if problem=='occupied' else 255,8,255,11]);f.uc.mem_write(self.indices,before)
            old=len(self.strings);f.execute('EnhancedBagDrawContext',self.app,self.indices,5)
            self.assertEqual(bytes(f.uc.mem_read(self.indices,5)),before,problem);self.assertEqual(len(self.strings),old)
    def test_real_fly_check_retains_badge_location_companion_costume_safari_and_palpark(self):
        f=self.f
        for problem,expected in [('badge',2),('map',1),('companion',3),('costume',5),('safari',1),('palpark',1),('union',1)]:
            f.uc.mem_write(f.profile+0x1A,bytes([0 if problem=='badge' else 16]))
            f.put(f.field+0x70,2 if problem=='union' else 0)
            self.fly_allowed=problem!='map';self.companion=problem=='companion';self.costume=problem=='costume';self.safari=problem=='safari';self.palpark=problem=='palpark'
            self.assertEqual(self.offer(),12,problem);self.assertEqual(f.get(self.state+40),expected)
        self.assertFalse(self.called(0x020880CC));self.assertEqual(f.get(self.state+12),0)
    def test_real_flash_check_requires_darkness_or_alph_and_rejects_link_rooms(self):
        f=self.f;self.item(397)
        f.uc.mem_write(self.menu+0x37C,bytes(2));self.assertEqual(self.offer(),12)
        self.alph=True;self.assertEqual(self.offer(),13)
        self.alph=False;f.uc.mem_write(self.menu+0x37C,struct.pack('<H',128));self.assertEqual(self.offer(),13)
        f.put(f.field+0x70,3);self.assertEqual(self.offer(),12)
    def test_no_or_unfinished_prompt_never_launches_or_changes_items_and_moves(self):
        f=self.f;self.response=2
        self.assertEqual(self.offer(),13);self.assertEqual(f.execute('EnhancedBagFieldPrompt',self.app),13)
        self.printing=True;self.assertEqual(f.execute('EnhancedBagFieldPrompt',self.app),13);self.assertFalse(self.called(0x021FF004))
        self.printing=False;f.execute('EnhancedBagFieldPrompt',self.app)
        self.response=0;self.assertEqual(f.execute('EnhancedBagFieldPrompt',self.app),13)
        self.response=2;self.assertEqual(f.execute('EnhancedBagFieldPrompt',self.app),1)
        self.assertEqual(f.get(self.state+28),1);self.assertEqual(f.get(self.state+12),0)
        self.assertFalse(self.called(0x020880CC));self.assertFalse(self.called(0x02064E18));self.assertEqual(self.allocations,[])
    def test_yes_hands_off_to_real_native_fly_use_with_actual_menu_environment_in_both_roms(self):
        for game in ('heartgold','soulsilver'):
            self.setUp();f=self.f
            path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            r=api.ndspy.rom.NintendoDSRom.fromFile(path);f.uc.mem_write(r.arm9RamAddress,bytes(r.arm9))
            self.assertEqual(self.accept(),37);self.assertEqual(f.get(self.state+12),1)
            self.assertEqual(struct.unpack('<H',f.uc.mem_read(self.view+0x68,2))[0],0)
            f.execute('EnhancedItemUseTMHM',self.itemdata,self.menu+0x358)
            self.assertEqual(f.get(self.state+12),0);self.assertEqual(f.get(self.state+36),1)
            self.assertEqual(f.get(self.menu+0x380),0x022B0000)
            self.assertEqual(struct.unpack('<H',f.uc.mem_read(self.menu+0x26,2))[0],5)
            a,heap,size=self.allocations[-1];self.assertEqual((heap,size),(11,4));self.assertEqual(f.get(a),self.slot)
            self.assertFalse(self.called(0x02064E18));self.assertEqual(len(self.called(0x0203EAB0)),1)
    def test_cancelled_fly_map_frees_native_owners_and_returns_to_bag(self):
        f=self.f;self.assertEqual(self.accept(),37)
        f.execute('EnhancedItemUseTMHM',self.itemdata,self.menu+0x358)
        old=[f.get(self.menu+0x384),f.get(self.menu+0x380)]
        self.assertEqual(f.execute('EnhancedBagFlyReturn',self.task),0)
        self.assertEqual([c[2] for c in self.called(0x0201AB80)],old)
        self.assertEqual(f.get(self.menu+0x380),0x022B0100)
        self.assertEqual(f.get(self.menu+0x384),0)
        self.assertEqual(f.get(self.menu+0x354),0x0203CFC1)
        self.assertEqual(f.get(self.state+28),1)
    def test_selected_fly_destination_executes_original_native_return_and_flight_handoff(self):
        f=self.f;self.assertEqual(self.accept(),37)
        f.execute('EnhancedItemUseTMHM',self.itemdata,self.menu+0x358)
        f.put(f.get(self.menu+0x380)+0x14,1)
        self.assertEqual(f.execute('EnhancedBagFlyReturn',self.task),0)
        self.assertEqual(f.get(self.menu+0x380),0x022D0100)
        self.assertEqual(f.get(self.menu+0x354),0x02067C31)
        self.assertEqual(struct.unpack('<H',f.uc.mem_read(self.menu+0x26,2))[0],12)
        self.assertEqual(len(self.called(0x02067BF8)),1)
    def test_real_native_flash_use_allocates_its_environment_and_restores_field_overlay(self):
        f=self.f;self.item(397);self.assertEqual(self.accept(),37)
        f.execute('EnhancedItemUseTMHM',self.itemdata,self.menu+0x358)
        self.assertEqual(struct.unpack('<H',f.uc.mem_read(self.menu+0x26,2))[0],12)
        self.assertEqual(f.get(self.menu+0x354),0x02068505)
        a,heap,size=self.allocations[-1];self.assertEqual((heap,size),(32,16))
        self.assertEqual(tuple(struct.unpack('<4I',f.uc.mem_read(a,16))),(0x19740205,0,self.task,self.slot|(7<<16)))
        self.assertEqual(f.get(self.menu+0x380),a);self.assertEqual(len(self.called(0x020505C0)),1)
    def test_revalidation_at_acceptance_and_native_return_cannot_consume_a_stale_intent(self):
        for problem in ('missing_item','off','no_party','badge','changed_save'):
            self.setUp();f=self.f;self.assertEqual(self.accept(),37)
            if problem=='missing_item':self.owned=False
            if problem=='off':f.put(self.extra,0)
            if problem=='no_party':self.slot=255
            if problem=='badge':f.uc.mem_write(f.profile+0x1A,bytes([0]))
            if problem=='changed_save':f.put(f.field+12,f.save+64)
            f.execute('EnhancedItemUseTMHM',self.itemdata,self.menu+0x358)
            self.assertEqual(f.get(self.state+12),0);self.assertEqual(f.get(self.state+36),0)
            self.assertEqual(len(self.called(0x0203E3FC)),1);self.assertEqual(f.get(self.menu+0x354),0x0203CFC1)
            self.assertFalse(self.called(0x02064E18))
        self.setUp();f=self.f;self.assertEqual(self.offer(),13)
        f.execute('EnhancedBagFieldPrompt',self.app);f.execute('EnhancedBagFieldPrompt',self.app);self.owned=False
        self.assertEqual(f.execute('EnhancedBagFieldPrompt',self.app),12);self.assertEqual(f.get(self.state+12),0)
    def test_unmarked_or_different_item_keeps_original_tm_teaching(self):
        f=self.f
        for mode in ('ordinary','disabled','different'):
            f.put(self.extra,mode!='disabled');f.put(self.state+12,int(mode=='different'));f.put(self.state+8,397)
            f.execute('EnhancedItemUseTMHM',self.itemdata,self.menu+0x358)
            self.assertEqual(f.get(self.state+12),0)
        self.assertEqual(len(self.called(0x02064E18)),3)
    def test_guarded_installation_accepts_both_roms_and_composes_with_repel(self):
        from gameplay.field_hm_bag import install_field_hm_bag
        from gameplay.repel import install_repel
        from gameplay.field import verify_field_files
        from gameplay.patches import PatchMismatch
        for game in ('heartgold','soulsilver'):
            path=ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds'
            original=api.ndspy.rom.NintendoDSRom.fromFile(path);patched=api.ndspy.rom.NintendoDSRom.fromFile(path)
            prior,_=install_repel(patched,self.payload);main,overlays=install_field_hm_bag(patched,self.payload)
            verify_field_files(original,patched,prior+overlays)
            self.assertEqual(main[0].address,0x020FE2AC);self.assertEqual(overlays[0].patch.address,0x021FB35A)
            bad=api.ndspy.rom.NintendoDSRom.fromFile(path);a=bytearray(bad.arm9);a[0x68024]^=1;bad.arm9=bytes(a)
            with self.assertRaises(PatchMismatch):install_field_hm_bag(bad,self.payload)
