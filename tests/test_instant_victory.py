"""Native faint/EXP handoff and guarded opponent-only selection."""
from pathlib import Path
import struct,unittest
import test_settings as api
from gameplay.victory import install_victory
from gameplay.field import verify_field_files
ROOT=Path(__file__).resolve().parent.parent

@unittest.skipUnless(api.AVAILABLE,'Install native ARM dependencies.')
class TestInstantVictory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.payload=api.build_payload()
    def setUp(self):
        owner=self;self.events=[];self.outcome=0;self.replace=0;self.original_helpers=False;self.original_mode=False
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,ctx):
                names={0x2248848:'selection',0x224873C:'get_mon',0x223B514:'special',0x223A7F0:'count',0x223AB1C:'side',0x223BD14:'outcome',0x224EB9C:'script',0x224DC74:'faint',0x224DD18:'exp',0x224D7EC:'win',0x224D540:'replace',0x2250F44:'init',0x2251710:'reset',0x2237ED0:'mode',0x2006F7C:'unload',0x2006FF8:'load'}
                if owner.original_mode and 0x2237ED0<=address<0x2237F18:return
                if owner.original_helpers and (0x224DC74<=address<0x224DD74 or 0x20726C0<=address<0x2072700):return
                if address in names:
                    a,b,c,d=[uc.reg_read(reg) for reg in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)];name=names[address];owner.events.append((name,a,b,c,d));result=0
                    if name=='special':result=f.get(owner.battle+0x240C)
                    elif name=='count':result=f.get(owner.battle+0x44)
                    elif name=='side':result=b&1
                    elif name=='outcome':result=owner.outcome
                    elif name=='script':owner.assertEqual(a,owner.ctx);owner.assertEqual(b,1)
                    elif name=='faint':owner.assertEqual((a,b,c,d),(owner.ctx,5,5,1))
                    elif name=='exp':owner.assertEqual((a,b,c),(owner.ctx,5,5))
                    elif name=='win':result=owner.outcome
                    elif name=='replace':result=owner.replace
                    elif name=='mode':owner.assertEqual((a,b),(owner.battle,0));uc.mem_write(a+0x2445,b'\0')
                    elif name=='get_mon':f.put(b+8,1)
                    uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR));return
                if address==0x223A7E0:
                    uc.reg_write(api.UC_ARM_REG_R0,f.get(owner.battle+0x2C));uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR));return
                return super().hook(uc,address,size,ctx)
        Fixture.payload=self.payload;self.f=Fixture('runTest');self.f.setUp();self.f.reload()
        self.battle,self.ctx=0x02288000,0x02290000;self.extra=self.payload.symbols['gEnhancedExtraOptions'];self.state=self.payload.symbols['gInstantVictoryState']
        self.prepare()
    def prepare(self,typ=0,count=2):
        f=self.f;f.uc.mem_write(self.ctx,bytes(0x3200));f.uc.mem_write(self.state,bytes(48));f.put(self.battle+0x2C,typ);f.put(self.battle+0x44,count);f.put(self.battle+0x240C,0);f.uc.mem_write(self.battle+0x2445,b'\x01');f.put(self.ctx+8,5)
        for i,hp in enumerate((25,30,20,40)):
            f.put(self.ctx+0x2D8C+192*i,hp);f.put(self.ctx+0x2D90+192*i,hp)
        f.uc.mem_write(self.ctx+0x21EC,bytes(range(4)));f.put(self.extra+44,1);self.events=[];self.outcome=self.replace=0
    def execute(self,name='EnhancedVictorySelection'):return self.f.execute(name,self.battle,self.ctx)
    def names(self):return [x[0] for x in self.events]
    def test_default_off_owner_and_special_formats_preserve_complete_native_input_context(self):
        for mode in ('off','owner','unloaded','link','frontier','safari','park','tutorial','unknown','recording','recorded'):
            self.prepare();self.f.owner=0x12345678;self.f.put(self.f.state+8,1)
            if mode=='off':self.f.put(self.extra+44,0)
            elif mode=='owner':self.f.owner^=1
            elif mode=='unloaded':self.f.put(self.f.state+8,0)
            elif mode in ('recording','recorded'):self.f.put(self.battle+0x240C,16 if mode=='recording' else 32)
            else:self.f.put(self.battle+0x2C,{'link':4,'frontier':128,'safari':32,'park':512,'tutorial':1024,'unknown':8192}[mode])
            before=bytes(self.f.uc.mem_read(self.ctx,0x3200));self.execute();self.assertEqual(bytes(self.f.uc.mem_read(self.ctx,0x3200)),before);self.assertEqual(self.names().count('selection'),1);self.assertNotIn('script',self.names());self.assertEqual(self.f.get(self.state+16),0)
    def test_all_supported_flags_inject_only_native_hp_script_and_do_not_write_hp_or_result(self):
        bits=[1,2,8,16,64,256,4096]
        for mask in range(128):
            self.prepare(typ=sum(b for i,b in enumerate(bits) if mask&(1<<i)));self.execute()
            self.assertEqual((self.f.get(self.ctx+8),self.f.get(self.ctx+12)),(22,5));self.assertEqual(self.f.get(self.ctx+0x118),1);self.assertEqual(self.f.get(self.ctx+0x215C),(-30)&0xffffffff)
            self.assertEqual(self.f.get(self.ctx+0x2D8C+192),30);self.assertEqual(self.f.get(self.ctx+0x213C),64);self.assertEqual(self.events[-1][0:4],('script',self.ctx,1,2));self.assertNotIn('selection',self.names());self.assertLess(self.names().index('mode'),self.names().index('script'));self.assertEqual(self.outcome,0)
    def test_pending_input_faint_exp_work_and_invalid_player_or_count_defer_without_context_writes(self):
        for mode in ('input','faint','exp','work','player','absent','outcome','count','wrong-command','wrong-overlay'):
            self.prepare()
            if mode=='input':self.f.uc.mem_write(self.ctx,b'\x01')
            elif mode=='faint':self.f.put(self.ctx+0x213C,1<<24)
            elif mode=='exp':self.f.put(self.ctx+0x2140,1<<28)
            elif mode=='work':self.f.put(self.ctx+0x178,0x02280000)
            elif mode=='player':self.f.put(self.ctx+0x2D8C,0)
            elif mode=='absent':self.f.uc.mem_write(self.ctx+0x3108,b'\x01')
            elif mode=='outcome':self.outcome=1
            elif mode=='count':self.f.put(self.battle+0x44,3)
            elif mode=='wrong-overlay':self.f.uc.mem_write(self.battle+0x2445,b'\0')
            else:self.f.put(self.ctx+8,22)
            before=bytes(self.f.uc.mem_read(self.ctx,0x3200));self.execute();self.assertEqual(bytes(self.f.uc.mem_read(self.ctx,0x3200)),before);self.assertIn('selection',self.names());self.assertNotIn('script',self.names())
    def test_native_faint_exp_replacement_and_win_order_and_disabled_inflight_cleanup(self):
        self.execute();self.events=[];self.f.put(self.extra+44,0);self.f.owner^=1;self.replace=1
        self.execute();self.assertEqual(self.names(),['faint','exp','win','replace']);self.assertEqual(self.f.get(self.state+8),1)
        self.events=[];self.replace=0;self.f.put(self.ctx+0x150,7);self.f.put(self.ctx+0x174,9);self.execute()
        self.assertEqual(self.names(),['faint','exp','win','replace','init','reset']);self.assertEqual(self.f.get(self.ctx+8),2);self.assertEqual(self.f.get(self.ctx+0x150),7);self.assertEqual(self.f.get(self.ctx+0x174),9);self.assertEqual(self.f.get(self.state+8),0)
        self.f.owner^=1;self.prepare();self.execute();self.events=[];self.outcome=1;self.execute();self.assertEqual(self.names(),['faint','exp','win']);self.assertEqual(self.f.get(self.state+8),0);self.assertNotIn('replace',self.names())
    def test_original_native_mode_handoff_unloads_menu_overlay_then_loads_battle_overlay(self):
        rom=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds');ov=rom.loadArm9Overlays([12])[12];self.f.uc.mem_write(ov.ramAddress,bytes(ov.data));self.original_mode=True
        self.execute();self.assertEqual(bytes(self.f.uc.mem_read(self.battle+0x2445,1)),b'\0')
        transitions=[(e[0],e[1],e[2] if e[0]=='load' else None) for e in self.events if e[0] in ('unload','load')];self.assertEqual(transitions,[('unload',10,None),('load',7,2)])
        self.assertLess(self.names().index('load'),self.names().index('script'));self.assertEqual(self.f.get(self.ctx+8),22)
    def test_native_calculator_helpers_dispatch_original_faint_and_exp_scripts(self):
        self.prepare();rom=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds');self.f.uc.mem_write(0x02000000,bytes(rom.arm9));ov=rom.loadArm9Overlays([12])[12];self.f.uc.mem_write(ov.ramAddress,bytes(ov.data));self.original_helpers=True
        self.execute();self.f.put(self.ctx+8,5);self.f.put(self.ctx+0x213C,1<<25);self.events=[];self.execute()
        self.assertEqual(self.f.get(self.ctx+0x74),1);self.assertEqual(self.f.get(self.ctx+8),22);self.assertEqual(self.f.get(self.ctx+12),5);self.assertEqual(self.events[-1][0:4],('script',self.ctx,1,6));self.assertEqual(self.f.get(self.state+20),1)
        self.f.put(self.ctx+8,5);self.f.put(self.ctx+0x2140,1<<29);self.events=[];self.execute()
        self.assertEqual(self.f.get(self.ctx+0x2140)&(1<<29),0);self.assertEqual(self.events[-1][0:4],('script',self.ctx,1,276));self.assertEqual(self.f.get(self.state+24),1)
        self.events=[];self.f.put(self.ctx+8,5);self.execute();self.assertEqual(self.f.get(self.ctx+8),2);self.assertEqual(self.f.get(self.state+8),0)
    def test_doubles_skip_absent_and_fainted_targets_then_return_for_remaining_enemy(self):
        self.prepare(count=4);self.f.uc.mem_write(self.ctx+0x3108,b'\x02');self.execute();self.assertEqual(self.f.get(self.state+12),3)
        self.prepare(count=4);self.f.put(self.ctx+0x2D8C+192,0);self.execute();self.assertEqual(self.f.get(self.state+12),3)
        self.prepare(count=4);self.execute();self.assertEqual(self.f.get(self.state+12),1);self.execute();self.f.put(self.ctx+8,5);self.f.uc.mem_write(self.battle+0x2445,b'\x01');self.f.put(self.ctx+0x2D8C+192,0);self.execute();self.assertEqual(self.f.get(self.state+12),3);self.assertEqual(self.f.get(self.state+16),2)
    def test_new_battle_command_zero_clears_interrupted_work_even_with_reused_pointers(self):
        self.execute();self.events=[];self.execute('EnhancedVictoryGetBattleMon');self.assertEqual(self.f.get(self.state+8),0);self.assertEqual(self.f.get(self.state+44),1);self.assertEqual(self.names(),['get_mon']);self.assertEqual(self.f.get(self.ctx+8),1)
    def test_both_guarded_tables_only_change_two_pointers_and_reject_script_or_context_mutation(self):
        import ndspy.narc
        for g in ('heartgold','soulsilver'):
            rom=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{g}-visual-plus-full-baseline.nds');r=api.ndspy.rom.NintendoDSRom(rom.save());changes=install_victory(r,self.payload);self.assertEqual(len(changes),2);self.assertEqual(r.arm9,rom.arm9);verify_field_files(rom,r,changes)
            r=api.ndspy.rom.NintendoDSRom(rom.save());n=ndspy.narc.NARC(r.getFileByName('a/0/0/1'));n.files[2]=bytes([n.files[2][0]^1])+n.files[2][1:];r.setFileByName('a/0/0/1',n.save())
            with self.assertRaises(api.PatchMismatch):install_victory(r,self.payload)
            r=api.ndspy.rom.NintendoDSRom(rom.save());o=r.loadArm9Overlays([12])[12];o.data[0x224D7EC-o.ramAddress]^=1;r.files[o.fileID]=o.save(compress=False)
            with self.assertRaises(api.PatchMismatch):install_victory(r,self.payload)
