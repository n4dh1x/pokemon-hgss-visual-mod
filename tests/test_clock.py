"""Independent world-clock arithmetic with original RTC time/day readers."""
from pathlib import Path
import struct,sys,unittest,zlib
import test_settings as api
from gameplay.clock import install_clock
from gameplay.field import verify_field_files
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestClock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=api.build_payload()
        p=ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds'
        if not p.exists():raise unittest.SkipTest('Build local baseline first.')
        cls.rom=api.ndspy.rom.NintendoDSRom(p.read_bytes())
    def setUp(self):
        self.task_entry=False;self.task_calls=[];self.assertions=0
        self.hud_mode=False;self.field_allowed=True;self.inhibit=0;self.hud_actions=[];self.live_string=False;self.live_window=False;self.start_task=False;self.original_steps=0
        self.now=1000*86400+86370;self.high=0;self.save_result=2;self.berries=[];self.plants=[];self.berry_order=[];self.status=[];self.redraws=[];self.real_berry_calls=0
        owner=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,ctx):
                if owner.task_entry and 0x020504F0<=address<0x02050510:return
                if 0x020147A4<=address<0x020147DC or 0x02014844<=address<0x0201487C or 0x02055618<=address<0x02055624:return
                a,b,c,d=[uc.reg_read(r) for r in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)]
                if owner.hud_mode and address==0x02026354:
                    owner.assertFalse(owner.live_string);owner.live_string=True;owner.hud_actions.append('string');result=0x02238000
                elif owner.hud_mode and address==0x0201D40C:
                    owner.assertFalse(owner.live_window);owner.assertEqual((a,c,d),(0x02236000,3,18))
                    args=struct.unpack('<5I',uc.mem_read(uc.reg_read(api.UC_ARM_REG_SP),20))
                    owner.assertEqual(args,(21,12,2,13,0x360));owner.hud_actions.append('window');owner.live_window=True
                    uc.mem_write(b,struct.pack('<I6BHI',a,3,18,21,12,2,13,0x360,0x0223A000));result=0
                elif owner.hud_mode and address==0x0201D8C8:
                    owner.assertTrue(owner.live_window);owner.hud_actions.append('clear');result=0
                elif owner.hud_mode and address==0x0201D520:
                    owner.assertTrue(owner.live_window);owner.hud_actions.append('remove');owner.live_window=False
                    uc.mem_write(a,b'\0'*16);result=0
                elif owner.hud_mode and address==0x02026380:
                    owner.assertTrue(owner.live_string);owner.assertEqual(a,0x02238000);owner.hud_actions.append('delete');owner.live_string=False;result=0
                elif address==0x0203E13C:result=int(owner.field_allowed)
                elif address==0x0203BE60:result=owner.inhibit
                elif owner.hud_mode and address==0x0203E15C:
                    owner.original_steps+=1
                    if owner.start_task:
                        uc.reg_write(api.UC_ARM_REG_R0,f.field)
                        uc.reg_write(api.UC_ARM_REG_R1,0x02123457)
                        uc.reg_write(api.UC_ARM_REG_R2,0x02233000)
                        uc.reg_write(api.UC_ARM_REG_PC,owner.payload.symbols['EnhancedClockCreateTask']);return
                    result=0
                elif owner.hud_mode and address==0x020504C0:
                    owner.assertFalse(owner.live_string or owner.live_window)
                    owner.task_calls.append((a,b,c));result=0x02213200
                elif owner.hud_mode and address==0x0202551C:
                    owner.assertions+=1;result=0
                elif address==0x020147DC:
                    result=owner.now;uc.reg_write(api.UC_ARM_REG_R1,owner.high)
                elif address==0x0201474C:
                    at=0x021D1094 if f.get(0x021D1090)==3 else 0x021D1068
                    uc.mem_write(a,bytes(uc.mem_read(at,12)));result=0
                elif address==0x02028D3C:result=0x02239000
                elif address==0x020273F0:owner.assertEqual(a,f.save);result=owner.save_result
                elif address==0x022037C8:owner.real_berry_calls+=1;result=0
                elif address==0x02201760:owner.berries.append((a,b,c));owner.berry_order.append('grow');result=0
                elif address==0x02201610:owner.plants.append((a,b,c,d));owner.berry_order.append('plant');result=0
                elif address==0x0220387C:owner.status.append(a);result=0
                elif address==0x02203928:owner.redraws.append(a);result=0
                else:return super().hook(uc,address,size,ctx)
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        Fixture.payload=self.payload;self.f=Fixture('runTest');self.f.setUp();self.f.reload()
        self.extra=self.payload.symbols['gEnhancedExtraOptions'];self.state=self.payload.symbols['gClockState']
        self.f.uc.mem_write(0x020147A4,bytes(self.rom.arm9[0x147A4:0x147DC]))
        self.f.uc.mem_write(0x02014844,bytes(self.rom.arm9[0x14844:0x1487C]))
        table=struct.unpack_from('<I',self.rom.arm9,0x14858)[0]
        self.f.uc.mem_write(table,bytes(self.rom.arm9[table-0x02000000:table-0x02000000+24]))
        self.sample()
    def sample(self):
        seconds=self.now%86400;self.f.uc.mem_write(0x021D1068,struct.pack('<3I',seconds//3600,seconds//60%60,seconds%60))
    def execute(self,name,*args):
        self.sample()
        if not isinstance(name,int):return self.f.execute(name,*args)
        uc=self.f.uc
        for reg,value in zip((api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3),(*args,0,0,0,0)):uc.reg_write(reg,value)
        uc.reg_write(api.UC_ARM_REG_SP,0x023FF000);uc.reg_write(api.UC_ARM_REG_LR,0x02300001)
        uc.emu_start(name,0x02300000,count=200000)
        self.assertEqual(uc.reg_read(api.UC_ARM_REG_PC),0x02300000)
        self.assertEqual(uc.reg_read(api.UC_ARM_REG_SP),0x023FF000)
        return uc.reg_read(api.UC_ARM_REG_R0)
    def get(self,offset):return self.f.get(self.state+offset)
    def test_default_native_seconds_and_all_rates_cross_midnight(self):
        self.assertEqual(self.execute('EnhancedClockSeconds'),86370);self.assertEqual(self.get(4),0)
        for option,rate in enumerate((1,6,12,24,60,120)):
            self.execute('EnhancedClockRestore',0,self.f.owner);self.f.put(self.extra+24,option)
            before=self.execute('EnhancedClockSeconds');self.now+=123
            self.assertEqual(self.execute('EnhancedClockSeconds'),(before+123*rate)%86400)
            if rate>1:self.assertEqual((self.get(24),self.get(28)),divmod(123*(rate-1),60))
    def test_return_to_one_x_preserves_shift_and_rebases_backward_clock(self):
        self.f.put(self.extra+24,5);start=self.execute('EnhancedClockSeconds');self.now+=40
        shifted=self.execute('EnhancedClockSeconds');self.assertEqual(shifted,(start+4800)%86400)
        self.f.put(self.extra+24,0);self.now+=8;self.assertEqual(self.execute('EnhancedClockSeconds'),(shifted+8)%86400)
        value=self.get(16);self.now-=1000;self.assertEqual(self.execute('EnhancedClockSeconds'),value);self.assertEqual(self.get(36),1)
        self.now+=3;self.assertEqual(self.execute('EnhancedClockSeconds'),(value+3)%86400)
    def test_snapshot_cold_resume_uses_one_x_and_no_offline_berry_bonus(self):
        f=self.f;self.f.put(self.extra+24,5);self.execute('EnhancedClockSeconds');self.now+=120;self.execute('EnhancedClockSeconds')
        shifted=self.get(16);debt=(self.get(24),self.get(28));at=0x02220000
        for i,v in enumerate((1,0,1,0,0,0,5)):f.put(at+4*i,v)
        self.assertEqual(self.execute('EnhancedSettingsStoreAll',1,1,1,1,1,1,at),1)
        self.now+=7200;f.reload()
        self.assertEqual(self.execute('EnhancedClockSeconds'),(shifted+7200)%86400)
        self.assertEqual((self.get(24),self.get(28)),debt)
        self.now+=2;self.assertEqual(self.execute('EnhancedClockSeconds'),(shifted+7200+240)%86400)
    def test_native_day_wild_readers_owner_guard_photo_and_native_data_preservation(self):
        f=self.f;f.put(self.extra+24,5);self.now=1000*86400+3*3600+59*60+50
        self.sample();original=bytes(f.uc.mem_read(0x021D1048,0x58));self.execute('EnhancedClockSeconds')
        self.now+=1
        self.assertEqual(self.execute('EnhancedClockDay'),0);self.assertEqual(self.execute('EnhancedClockWild'),0)
        after=bytes(f.uc.mem_read(0x021D1048,0x58))
        self.assertEqual((after[:0x20],after[0x2C:]),(original[:0x20],original[0x2C:]))
        # Morning starts at native 04:00; the real RTC remains in the previous hour.
        self.assertEqual(f.get(0x021D1068),3)
        f.put(0x021D1090,3);f.uc.mem_write(0x021D1094,struct.pack('<3I',21,12,13))
        self.assertEqual(self.execute('EnhancedClockSeconds'),21*3600+12*60+13)
        self.assertEqual(self.execute('EnhancedClockDay'),3)
        f.put(0x021D1090,0);f.owner^=1
        self.assertEqual(self.execute('EnhancedClockSeconds'),self.now%86400)
        self.assertEqual(self.get(16),4*3600+110)
    def test_huge_active_elapsed_saturates_debt_without_overflow_or_calendar_mutation(self):
        self.f.put(self.extra+24,5);start=self.execute('EnhancedClockSeconds');self.now+=3000000000
        self.assertEqual(self.execute('EnhancedClockSeconds'),(start+3000000000*120)%86400)
        self.assertEqual((self.get(24),self.get(28)),(2147483647,0))
        self.high=1;before=self.get(16);self.now+=50;self.execute('EnhancedClockSeconds');self.assertEqual(self.get(16),before)
    def test_only_extra_berry_minutes_are_consumed_once_and_native_update_runs_first(self):
        self.f.put(self.extra+24,1);self.execute('EnhancedClockSeconds');self.now+=25
        data=0x02230000;self.f.put(data+0x14,0x02231000);self.f.put(data+0x1C,0x02232000)
        self.execute('EnhancedClockBerry',data,1)
        self.assertEqual(self.berries,[(0x02231000,0x02232000,2)]);self.assertEqual((self.get(24),self.get(28)),(0,5))
        self.assertEqual((self.status,self.redraws),([data],[data]))
        self.execute('EnhancedClockBerry',data,0);self.assertEqual(len(self.berries),1);self.assertEqual(self.real_berry_calls,2)
    def test_new_seed_does_not_receive_bonus_accumulated_before_planting(self):
        self.f.put(self.extra+24,5);self.execute('EnhancedClockSeconds');self.now+=90
        pots=0x02231000;properties=0x02232000;data=0x02230000
        self.f.put(data+0x14,pots);self.f.put(data+0x1C,properties)
        self.execute('EnhancedClockPlant',pots,2,properties,7)
        self.assertEqual(self.berry_order,['grow','plant'])
        self.assertEqual(self.berries,[(pots,properties,178)])
        self.assertEqual(self.plants,[(pots,2,properties,7)])
        self.execute('EnhancedClockBerry',data,1)
        self.assertEqual(self.berry_order,['grow','plant']);self.assertEqual(self.status,[])
        self.now+=30;self.execute('EnhancedClockBerry',data,1)
        self.assertEqual(self.berries[-1],(pots,properties,60))
        self.assertEqual(self.get(48),238)
        self.f.put(self.extra+24,0);self.now+=10
        self.execute('EnhancedClockPlant',pots,0,properties,3)
        self.assertEqual(self.plants[-1],(pots,0,properties,3))
        self.assertEqual(self.berry_order[-1],'plant');self.assertEqual(len(self.berries),2)

    def test_native_save_result_ownership_and_journal_failure_are_preserved(self):
        self.f.put(self.extra+24,1);self.execute('EnhancedClockSeconds');self.now+=30
        self.assertEqual(self.execute('EnhancedClockSave',self.f.save),2);self.assertEqual(self.get(40),1)
        self.assertEqual(len(self.f.writes),1)
        self.save_result=3;self.assertEqual(self.execute('EnhancedClockSave',self.f.save),3);self.assertEqual(len(self.f.writes),1)
        self.save_result=2;self.f.fail_write=True
        self.assertEqual(self.execute('EnhancedClockSave',self.f.save),2);self.assertEqual(self.get(44),1)
    def test_snapshot_bounds_and_legacy_padding_validation(self):
        r=bytearray(api.record(self.f.owner,4,(1,1,1,1,1,1,1,0,1,0,0,0,5,86399,100000000,1,2147483647,59)))
        struct.pack_into('<I',r,212,512|1024);struct.pack_into('<I',r,252,zlib.crc32(r[:252])&0xFFFFFFFF)
        at=0x02220000;self.f.uc.mem_write(at,bytes(r));self.assertEqual(self.execute('EnhancedSettingsValid',at,self.f.owner),1)
        for index,value in ((12,6),(13,86400),(14,3155760000),(15,2),(16,2147483648),(17,60)):
            bad=bytearray(r);struct.pack_into('<I',bad,20+index*4,value);struct.pack_into('<I',bad,252,zlib.crc32(bad[:252])&0xFFFFFFFF)
            self.f.uc.mem_write(at,bytes(bad));self.assertEqual(self.execute('EnhancedSettingsValid',at,self.f.owner),0,index)

    def test_native_field_hour_tail_branch_preserves_stack_and_calendar_fallback(self):
        r=api.ndspy.rom.NintendoDSRom(self.rom.save());install_clock(r,self.payload)
        self.f.uc.mem_write(0x02055618,bytes(r.arm9[0x55618:0x55624]))
        self.f.put(0x02239014,6)
        self.assertEqual(self.execute(0x02055619,self.f.field),6)
        self.f.put(self.extra+24,5);self.now=1000*86400+14*3600+16*60
        self.assertEqual(self.execute(0x02055619,self.f.field),14)
        self.assertEqual(self.f.get(0x02239014),6)
    def test_both_rom_clock_hooks_preserve_native_calendar_and_reject_tampering(self):
        for g in ('heartgold','soulsilver'):
            original=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{g}-visual-plus-full-baseline.nds')
            r=api.ndspy.rom.NintendoDSRom(original.save());main,overlays=install_clock(r,self.payload)
            self.assertEqual((len(main),len(overlays)),(10,14))
            self.assertEqual({o.overlay for o in overlays},{1,2,17,101})
            verify_field_files(original,r,overlays)
            changed={i for m in main for i in range(m.address-0x02000000,m.address-0x02000000+len(bytes.fromhex(m.before)))}
            self.assertTrue(all(a==b or i in changed for i,(a,b) in enumerate(zip(original.arm9,r.arm9))))
            for at,n in ((0x14708,0x174),(0x55418,0x1C8),(0x55600,0x18)):
                self.assertEqual(r.arm9[at:at+n],original.arm9[at:at+n])
            bad=api.ndspy.rom.NintendoDSRom(original.save());data=bytearray(bad.arm9);data[0x147A4]^=1;bad.arm9=bytes(data)
            with self.assertRaises(api.PatchMismatch):install_clock(bad,self.payload)

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestClockHud(unittest.TestCase):
    @classmethod
    def setUpClass(cls):TestClock.setUpClass()
    def setUp(self):
        self.c=TestClock('runTest');self.c.setUp();self.c.hud_mode=True
        self.c.f.put(self.c.f.field+8,0x02236000);self.c.f.put(self.c.f.field+0x44,0x02237000)
        self.state=self.c.payload.symbols['gClockHudState']
    def test_optional_native_field_guards_and_balanced_window_string_lifecycle(self):
        c=self.c;f=c.f
        c.execute('EnhancedClockHudShow',f.field);self.assertEqual(c.hud_actions,[])
        f.put(c.extra+28,1);f.put(f.field+0x10,1);c.execute('EnhancedClockHudShow',f.field)
        f.put(f.field+0x10,0);c.field_allowed=False;c.execute('EnhancedClockHudShow',f.field)
        c.field_allowed=True;c.inhibit=4;c.execute('EnhancedClockHudShow',f.field);self.assertEqual(c.hud_actions,[])
        c.inhibit=385;c.execute('EnhancedClockHudShow',f.field);c.execute('EnhancedClockHudShow',f.field)
        self.assertTrue(c.live_window and c.live_string);self.assertEqual(f.get(self.state+28),1)
        c.execute('EnhancedClockHudClose');c.execute('EnhancedClockHudClose')
        self.assertEqual(c.hud_actions,['string','window','clear','remove','delete'])
        self.assertEqual((f.get(self.state+24),f.get(self.state+28),f.get(self.state+32)),(0,1,1))
    def test_field_control_releases_hud_before_native_tasks_and_manager_teardown(self):
        c=self.c;f=c.f;f.put(c.extra+28,1)
        c.execute('EnhancedFieldControl',f.field)
        self.assertTrue(c.live_window);c.start_task=True
        c.execute('EnhancedFieldControl',f.field)
        self.assertFalse(c.live_window or c.live_string);self.assertEqual(c.original_steps,2)
        c.start_task=False;f.put(f.field+0x10,0);c.execute('EnhancedClockHudShow',f.field)
        c.execute('EnhancedClockHudForget',f.manager+4);self.assertTrue(c.live_window)
        c.execute('EnhancedClockHudForget',f.manager);self.assertFalse(c.live_window or c.live_string)
    def test_repeated_hud_frames_leave_npc_flags_and_resources_unchanged(self):
        c=self.c;f=c.f;f.put(c.extra+28,1);before=bytes(f.uc.mem_read(f.objects,0x258))
        for _ in range(64):c.execute('EnhancedClockHudShow',f.field);c.execute('EnhancedClockHudClose')
        self.assertEqual((f.get(self.state+28),f.get(self.state+32),f.get(self.state+36)),(64,64,64))
        self.assertFalse(c.live_window or c.live_string)
        self.assertEqual(bytes(f.uc.mem_read(f.objects,0x258)),before)

    def test_idle_frames_retain_hud_and_redraw_only_when_time_changes(self):
        c=self.c;f=c.f;f.put(c.extra+28,1)
        for _ in range(32):c.execute('EnhancedFieldControl',f.field)
        self.assertEqual((f.get(self.state+28),f.get(self.state+32),f.get(self.state+36)),(1,0,1))
        c.now+=1;c.execute('EnhancedFieldControl',f.field)
        self.assertEqual((f.get(self.state+28),f.get(self.state+36)),(1,2))
        c.execute('EnhancedClockHudClose');self.assertFalse(c.live_window or c.live_string)
    def test_original_task_entry_closes_hud_and_preserves_constructor_semantics(self):
        c=self.c;f=c.f;f.put(c.extra+28,1)
        r=api.ndspy.rom.NintendoDSRom(c.rom.save());install_clock(r,c.payload)
        f.uc.mem_write(0x020504F0,bytes(r.arm9[0x504F0:0x50510]));c.task_entry=True
        c.execute('EnhancedClockHudShow',f.field)
        self.assertEqual(c.execute(0x020504F1,f.field,0x02123457,0x02233000),0x02213200)
        self.assertEqual(f.get(f.field+0x10),0x02213200)
        self.assertEqual(c.task_calls,[(f.field,0x02123457,0x02233000)])
        self.assertFalse(c.live_window or c.live_string);self.assertEqual(c.assertions,0)
        c.execute(0x020504F1,f.field,0x02123459,0x02234000)
        self.assertEqual(c.assertions,1)
    def test_area_name_banner_defers_hud_and_cleans_existing_window(self):
        c=self.c;f=c.f;f.put(c.extra+28,1)
        banner=f.get(f.get(f.field+4)+8);f.put(banner,1)
        c.execute('EnhancedClockHudShow',f.field);self.assertFalse(c.live_window)
        f.put(banner,0);c.execute('EnhancedClockHudShow',f.field);self.assertTrue(c.live_window)
        f.put(banner,1);c.execute('EnhancedClockHudBefore',f.field);self.assertFalse(c.live_window)
