"""Native quick-throw selection, message ABI, consumption and saved-last journal."""
from pathlib import Path
import json,struct,unittest,zlib
import ndspy.code,ndspy.narc
import test_settings as api
from test_item_giver import name_codes
from gameplay.quick_ball import install_quick_ball,CONTEXTS,SITES
from gameplay.field import verify_field_files
ROOT=Path(__file__).resolve().parent.parent

@unittest.skipUnless(api.AVAILABLE,'Install native ARM dependencies.')
class TestQuickBall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=api.build_payload()
        cls.rom=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/'build/baseline/heartgold-visual-plus-full-baseline.nds')
        cls.overlay=ndspy.code.loadOverlayTable(cls.rom.arm9OverlayTable,lambda i,f:cls.rom.files[f],{12})[12]
        cls.payload.symbols['NativeQuickDeleteText']=0x02268685
        bank=ndspy.narc.NARC(cls.rom.getFileByName('a/0/2/7')).files[222]
        cls.names={i:name_codes(bank,i) for i in list(range(1,17))+list(range(492,501))}
    def setUp(self):
        self.bag=0x02220020;self.battle=0x02226000;self.ctx=0x02230000;self.input=0x02235000
        self.party=0x02238000;self.storage=0x02240000;self.string=0x02224000
        self.type=0;self.special=0;self.count=2;self.outcome=0;self.party_count=6;self.full=False
        self.events=[];self.box_reads=0;self.cursor_result=7;self.native_save=2;self.fonts={};self.font_next=0x02260000
        owner=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,context):
                if 0x02078240<=address<0x0207879C or 0x02268684<=address<0x022686BC:return
                a,b,c,d=[uc.reg_read(reg) for reg in (api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)]
                result=0
                if address==0x020270D8:owner.assertEqual(a,f.save);result=owner.storage
                elif address==0x02077D88:owner.assertEqual((b,c),(5,5));result=2
                elif address==0x0223A7E0:owner.assertEqual(a,owner.battle);result=owner.type
                elif address==0x0223B514:result=owner.special
                elif address==0x0223A7F0:result=owner.count
                elif address==owner.payload.symbols['NativeBattleOutcome']&~1:result=owner.outcome
                elif address==0x02074640:owner.assertEqual(a,owner.party);result=owner.party_count
                elif address==0x02073D54:owner.assertEqual(a,owner.storage);owner.box_reads+=1;result=18 if owner.full else 0
                elif address==0x02269A24:owner.events.append(('cursor',a));result=owner.cursor_result
                elif address==0x02025224:owner.events.append(('touch-native',a));result=42
                elif address==0x02263138:owner.events.append(('bag',a,b,c))
                elif address==0x0224EDC0:owner.events.append(('clear',a,b))
                elif address==0x022632C0:owner.events.append(('response',a,b,c))
                elif address==0x020273F0:owner.assertEqual(a,f.save);result=owner.native_save
                elif address==0x02026354:
                    owner.assertEqual((a,b),(64,5));result=owner.string
                elif address==0x02077D40:
                    owner.assertEqual((a,c),(owner.string,5));codes=owner.names[b];n=len(codes)-1
                    uc.mem_write(a,struct.pack('<HHI',64,n,0xB6F8D2EC)+struct.pack('<'+str(n+1)+'H',*codes));owner.events.append(('name',b))
                elif address==0x02268550:
                    owner.assertIn(b,tuple(owner.input+0x4D0+i*20 for i in range(4,8)))
                    args=struct.unpack('<7I',uc.mem_read(uc.reg_read(api.UC_ARM_REG_SP),28));owner.assertEqual(args[:3],(0x010200,2,20023));owner.assertIn((args[3],args[4]),((128,34),(192,16),(32,34),(224,34)));owner.assertEqual(args[5:],(1,0));owner.assertEqual(d,0)
                    n=struct.unpack('<H',uc.mem_read(c+2,2))[0];codes=list(struct.unpack('<'+str(n)+'H',uc.mem_read(c+8,n*2)))
                    owner.assertEqual(f.get(b),0);font=owner.font_next;owner.font_next+=64
                    f.put(b,font);owner.fonts[font]=(b,codes);owner.events.append(('text',font,args[4],codes))
                elif address==0x02013660:owner.assertIn(a,owner.fonts);owner.events.append(('delete',a));del owner.fonts[a]
                elif address==0x02021B5C:owner.events.append(('char-free',a))
                elif address==0x0200604C:owner.events.append(('sound',a))
                else:return super().hook(uc,address,size,context)
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        self.f=Fixture();self.f.payload=self.payload;self.f.setUp();self.f.uc.mem_write(0x02000000,bytes(self.rom.arm9))
        self.f.uc.mem_write(0x02268684,bytes(self.overlay.data[0x02268684-self.overlay.ramAddress:0x022686BC-self.overlay.ramAddress]))
        self.q=self.payload.symbols['gQuickBall'];self.f.execute('EnhancedSettingsEnsure',self.f.field)
        for offset,value in [(0x30,self.ctx),(0x58,self.bag),(0x64,self.storage),(0x68,self.party)]:self.f.put(self.battle+offset,value)
        self.f.put(self.ctx+8,5);self.f.put(self.ctx+0x2D8C,20);self.f.put(self.ctx+0x2E4C,20)
        self.f.put(self.input,self.battle);self.f.uc.mem_write(self.input+0x68B,b'\1')
        self.set_slots([(1,10),(2,20),(3,30),(4,40)]);self.f.execute('EnhancedQuickBegin',self.battle,self.ctx)
    def set_slots(self,values):
        raw=b''.join(struct.pack('<HH',*x) for x in values);self.f.uc.mem_write(self.bag+1728,raw+bytes(96-len(raw)))
    def get(self,index):return self.f.get(self.q+index*4)
    def put(self,index,value):self.f.put(self.q+index*4,value)
    def item(self):return self.f.execute('EnhancedQuickBallItem',self.battle)
    def input_key(self,key):
        self.f.put(0x021D1148,key);result=self.f.execute('EnhancedQuickCursor',self.input);self.f.put(0x021D1148,0);return result
    def test_native_patch_contexts_and_only_four_recorded_sites_in_both_images(self):
        for game in ('heartgold','soulsilver'):
            original=api.ndspy.rom.NintendoDSRom.fromFile(ROOT/f'build/baseline/{game}-visual-plus-full-baseline.nds')
            changed=api.ndspy.rom.NintendoDSRom(original.save());patches=install_quick_ball(changed,self.payload)
            self.assertEqual(len(patches),4);self.assertEqual([p.patch.address for p in patches],[s[0] for s in SITES])
            verify_field_files(original,changed,patches)
            with self.assertRaises(api.PatchMismatch):install_quick_ball(changed,self.payload)
    def test_all_context_mismatches_reject_before_any_file_change(self):
        for oid,address,size,digest in CONTEXTS:
            rom=api.ndspy.rom.NintendoDSRom(self.rom.save())
            if oid:
                o=ndspy.code.loadOverlayTable(rom.arm9OverlayTable,lambda i,f:rom.files[f],{oid})[oid];o.data[address-o.ramAddress]^=1;rom.files[o.fileID]=o.save(compress=False)
            else:
                arm=bytearray(rom.arm9);arm[address-rom.arm9RamAddress]^=1;rom.arm9=bytes(arm)
            files=list(rom.files);table=bytes(rom.arm9OverlayTable)
            with self.assertRaises(api.PatchMismatch):install_quick_ball(rom,self.payload)
            self.assertEqual(rom.files,files);self.assertEqual(rom.arm9OverlayTable,table)
    def test_bag_order_wrap_duplicate_first_stack_empty_and_park_ball_filter(self):
        self.set_slots([(500,5),(4,3),(1,1),(4,2),(0,0),(2,2)])
        self.assertEqual(self.item(),4)
        for direction,expected in [(1,1),(1,2),(1,4),(-1,2),(-1,1),(-1,4)]:
            self.assertEqual(self.f.execute('EnhancedQuickCycle',self.battle,direction),1);self.assertEqual(self.item(),expected)
        self.set_slots([(4,1)]);self.assertEqual(self.f.execute('EnhancedQuickCycle',self.battle,1),0)
        self.set_slots([(500,1)]);self.assertEqual(self.item(),0)
    def test_eligible_single_roamer_only_owner_context_native_restrictions(self):
        self.assertEqual(self.item(),1)
        for t in (1,2,4,8,16,32,64,128,512,1024,0x1000,0x40000000):
            self.type=t;self.assertEqual(self.item(),0,t)
        self.type=256;self.assertEqual(self.item(),1);self.type=0
        for address,value in [(self.ctx+8,6),(self.ctx+0x2D8C,0),(self.ctx+0x2E4C,0),(self.ctx+0x2E70,1<<24),(self.ctx+0x2E80,1<<6),(self.battle+0x64,self.storage+4)]:
            previous=self.f.get(address);self.f.put(address,value);self.assertEqual(self.item(),0);self.f.put(address,previous)
        for attr,value in [('count',4),('outcome',1),('special',0x10),('special',0x20)]:
            before=getattr(self,attr);setattr(self,attr,value);self.assertEqual(self.item(),0);setattr(self,attr,before)
        self.f.owner^=1;self.assertEqual(self.item(),0)
    def test_storage_cache_60_frames_and_throw_revalidation(self):
        self.assertEqual(self.item(),1);self.assertEqual(self.box_reads,1)
        self.full=True
        for frame in (1,59):self.f.put(0x021D1138,frame);self.assertEqual(self.item(),1)
        self.f.put(0x021D1138,60);self.assertEqual(self.item(),0);self.assertEqual(self.box_reads,2)
        self.party_count=5;self.f.put(0x021D1138,120);self.assertEqual(self.item(),1);self.assertEqual(self.box_reads,2)
        self.party_count=6;self.put(5,1);self.events=[];self.f.execute('EnhancedQuickShowBag',self.battle,self.ctx,0)
        self.assertEqual(self.events[-1],('bag',self.battle,self.ctx,0));self.assertEqual(self.get(5),0)
    def test_quick_native_response_has_ball_page_and_does_not_preconsume(self):
        before=bytes(self.f.uc.mem_read(self.bag,0x79C));self.put(5,2)
        self.f.execute('EnhancedQuickShowBag',self.battle,self.ctx,0)
        self.assertEqual(self.events,[('clear',self.ctx,0),('response',self.battle,0,2|(2<<16))])
        self.assertEqual(bytes(self.f.uc.mem_read(self.bag,0x79C)),before);self.assertEqual(self.get(5),0)
        self.assertEqual(self.f.execute('EnhancedQuickTakeBall',self.bag,2,1,5),1)
        self.assertEqual(struct.unpack('<HH',self.f.uc.mem_read(self.bag+1732,4)),(2,19))
        self.assertEqual((self.get(6),self.get(8),self.get(21)),(2,1,1))
    def test_quantity_depletion_falls_back_and_native_failed_take_cannot_change_last(self):
        self.set_slots([(2,1),(4,5)]);self.assertEqual(self.item(),2)
        self.assertEqual(self.f.execute('EnhancedQuickTakeBall',self.bag,2,1,5),1);self.assertEqual(self.item(),4)
        self.assertEqual(self.f.execute('EnhancedQuickTakeBall',self.bag,2,1,5),0);self.assertEqual(self.get(6),2)
    def test_keyboard_touch_cycles_R_feedback_handshake_and_idle_UI_ownership(self):
        self.assertEqual(self.input_key(0),7);self.assertEqual(len(self.fonts),4)
        texts=[e for e in self.events if e[0]=='text'];self.assertEqual(len(texts),4)
        self.assertEqual(self.input_key(0),7);self.assertEqual(len([e for e in self.events if e[0]=='text']),4)
        self.assertEqual(self.input_key(0x200),0xFFFFFFFF);self.assertEqual(self.item(),2)
        self.assertEqual(self.input_key(0x800),0xFFFFFFFF);self.assertEqual(self.item(),1)
        self.f.uc.mem_write(0x021D116C,struct.pack('<4H',220,25,1,1));self.assertEqual(self.input_key(0),0xFFFFFFFF);self.assertEqual(self.item(),2)
        self.f.uc.mem_write(0x021D116C,bytes(8));self.assertEqual(self.input_key(0x100),1)
        self.assertEqual(self.get(5),2);self.assertEqual(len(self.fonts),0)
        self.assertEqual(self.f.writes,[])
    def test_touch_strip_precedes_native_FIGHT_only_while_owned_quick_labels_are_visible(self):
        rects=0x02270000
        self.f.uc.mem_write(0x021D116C,struct.pack('<4H',128,30,1,1))
        self.assertEqual(self.f.execute('EnhancedQuickTouchRect',rects),42)
        self.f.uc.mem_write(0x021D116C,bytes(8));self.input_key(0)
        self.f.uc.mem_write(0x021D116C,struct.pack('<4H',128,30,1,1))
        self.assertEqual(self.f.execute('EnhancedQuickTouchRect',rects),0xFFFFFFFF)
        self.f.uc.mem_write(0x021D116C,struct.pack('<4H',128,80,1,1))
        self.assertEqual(self.f.execute('EnhancedQuickTouchRect',rects),42)
        self.f.uc.mem_write(0x021D116C,struct.pack('<4H',128,30,1,1))
        self.f.uc.mem_write(self.input+0x68B,b'\x0b')
        self.assertEqual(self.f.execute('EnhancedQuickTouchRect',rects),42)
        self.f.uc.mem_write(self.input+0x68B,b'\x01');self.f.execute('NativeQuickDeleteText',self.input)
        self.assertEqual(self.f.execute('EnhancedQuickTouchRect',rects),42)

    def test_initial_and_next_turn_main_variants_show_last_failed_ball_and_route_touches(self):
        self.assertEqual(self.f.execute('EnhancedQuickTakeBall',self.bag,2,1,5),1)
        for menu in (1,2,3,4):
            self.f.uc.mem_write(self.input+0x68B,bytes([menu]))
            self.f.uc.mem_write(0x021D116C,bytes(8))
            self.assertEqual(self.input_key(0),7)
            self.assertEqual((self.get(13),self.get(14)),(2,19))
            self.assertEqual(len(self.fonts),4)
            self.f.uc.mem_write(0x021D116C,struct.pack('<4H',128,30,1,1))
            self.assertEqual(self.f.execute('EnhancedQuickTouchRect',0x02270000),0xFFFFFFFF)
            self.f.execute('NativeQuickDeleteText',self.input)
            self.assertEqual(len(self.fonts),0)
        self.f.uc.mem_write(self.input+0x68B,b'\x0b')
        self.f.uc.mem_write(0x021D116C,bytes(8))
        self.assertEqual(self.input_key(0),7)
        self.assertEqual(len(self.fonts),0)

    def test_original_native_cleanup_reads_the_exact_owned_font_slots_and_frees_each_once(self):
        self.input_key(0)
        self.assertEqual(len(self.fonts),4)
        pointers=[self.f.get(self.input+0x4D0+i*20) for i in range(4,8)]
        self.assertEqual(set(pointers),set(self.fonts))
        self.f.execute('NativeQuickDeleteText',self.input)
        self.assertEqual(len(self.fonts),0)
        self.assertEqual([self.f.get(self.input+0x4D0+i*20) for i in range(4,8)],[0,0,0,0])
        self.assertEqual(len([e for e in self.events if e[0]=='delete']),4)
        self.input_key(0)
        self.assertEqual(len(self.fonts),4)
        self.input_key(0x100)
        self.assertEqual(len(self.fonts),0)
        self.f.execute('NativeQuickDeleteText',self.input)
        self.assertEqual(len([e for e in self.events if e[0]=='delete']),8)

    def test_saved_last_updates_only_after_successful_native_save_and_survives_reload(self):
        self.assertEqual(self.f.execute('EnhancedQuickTakeBall',self.bag,3,1,5),1)
        self.assertEqual(self.f.execute('EnhancedSettingsStore',1,1,1,1,1,1),1)
        self.assertEqual(self.get(7),0);self.f.reload();self.f.execute('EnhancedQuickBegin',self.battle,self.ctx);self.assertEqual(self.get(6),0)
        self.assertEqual(self.f.execute('EnhancedQuickTakeBall',self.bag,4,1,5),1)
        self.native_save=1;self.assertEqual(self.f.execute('EnhancedClockSave',self.f.save),1);self.assertEqual(self.get(7),0)
        self.native_save=2;self.f.fail_write=True;self.assertEqual(self.f.execute('EnhancedClockSave',self.f.save),2);self.assertEqual((self.get(7),self.get(8),self.get(24)),(0,1,1))
        self.f.fail_write=False;self.assertEqual(self.f.execute('EnhancedClockSave',self.f.save),2);self.assertEqual((self.get(7),self.get(8),self.get(23)),(4,0,1))
        self.f.reload();self.f.execute('EnhancedQuickBegin',self.battle,self.ctx);self.assertEqual(self.item(),4);self.assertEqual(self.get(7),4)
    def test_legacy_padding_is_not_a_ball_and_foreign_owner_has_no_last_ball(self):
        values=[1,1,1]+[0]*25+[999];self.f.install(0,api.record(self.f.owner,7,values));self.f.reload();self.assertEqual(self.get(6),0)
        body=bytearray(api.record(self.f.owner,8,[1,1,1]+[0]*25+[2]));struct.pack_into('<I',body,212,2097152);struct.pack_into('<I',body,252,zlib.crc32(body[:252])&0xFFFFFFFF)
        self.f.install(1,body);self.f.reload();self.assertEqual(self.get(6),2)
        self.f.owner^=1;self.f.reload();self.assertEqual(self.get(6),0)
