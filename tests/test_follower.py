"""Native party-follower permission/lifecycle and isolated saved-option tests."""
from pathlib import Path
import struct,sys,unittest
import test_settings as api
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from gameplay.follower import install_follower
from gameplay.field import verify_field_files,thumb_call

@unittest.skipUnless(api.AVAILABLE,'Install native ARM test dependencies.')
class TestFollower(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=api.build_payload();cls.roms=[]
        for g in ('heartgold','soulsilver'):
            p=ROOT/f'build/baseline/{g}-visual-plus-full-baseline.nds'
            if not p.exists():raise unittest.SkipTest('Build both local baselines first.')
            cls.roms.append(api.ndspy.rom.NintendoDSRom(p.read_bytes()))
    def setUp(self):
        self.permission=1;self.allowed=True;self.alive=1;self.removed=[];self.initialized=[];self.native_queries=[]
        owner=self
        class Fixture(api.TestSettings):
            def hook(f,uc,address,size,ctx):
                if 0x022059AC<=address<0x02205A34:return # Real native deferred lifecycle.
                regs=(api.UC_ARM_REG_R0,api.UC_ARM_REG_R1,api.UC_ARM_REG_R2,api.UC_ARM_REG_R3)
                a,b,c,d=[uc.reg_read(r) for r in regs]
                if address==0x0205F1E4:owner.assertEqual(a,f.manager);result=f.field
                elif address==0x02069FF4:owner.native_queries.append((a,b));result=owner.permission
                elif address==0x0203E13C:result=int(owner.allowed)
                elif address==0x02074904:owner.assertEqual(a,f.save);result=f.save+0x100
                elif address==0x02054358:result=owner.alive
                elif address==0x0205C67C:result=658
                elif address==0x0205C688:result=401
                elif address==0x0205C654:result=1
                elif address==0x02069F7C:result=152
                elif address==0x0205E3CC:
                    owner.assertEqual(a,owner.mon);owner.removed.append(a);f.put(a,0);result=0
                elif address==0x020699F8:
                    owner.assertEqual((a,b,c,d),(f.manager,658,401,1))
                    owner.assertEqual(struct.unpack('<I',uc.mem_read(uc.reg_read(api.UC_ARM_REG_SP),4))[0],33)
                    owner.assertEqual(f.get(owner.extra+20),0)
                    owner.initialized.append(a)
                    if owner.permission:
                        f.put(f.field+0xE4,owner.mon);uc.mem_write(f.field+0xFA,b'\x01');f.put(owner.mon,1);f.put(owner.mon+8,0xFD)
                    result=owner.mon if owner.permission else 0
                elif address==0x021F9048:owner.assertEqual(a,owner.mon);result=0
                else:return super().hook(uc,address,size,ctx)
                uc.reg_write(api.UC_ARM_REG_R0,result);uc.reg_write(api.UC_ARM_REG_PC,uc.reg_read(api.UC_ARM_REG_LR))
        Fixture.payload=self.payload;self.f=Fixture('runTest');self.f.setUp();self.f.reload()
        f=self.f;self.extra=self.payload.symbols['gEnhancedExtraOptions'];self.state=self.payload.symbols['gFollowerState']
        self.mon=0x02223000;self.avatar=0x02224000;self.location=0x02225000
        f.put(f.field+0x40,self.avatar);f.put(f.field+0x44,0x02226000);f.put(f.field+0x20,self.location);f.put(self.location,33)
        f.put(f.field+0xE4,self.mon);f.uc.mem_write(f.field+0xFA,b'\x01');f.put(self.mon,1);f.put(self.mon+8,0xFD)
        r=api.ndspy.rom.NintendoDSRom(self.roms[0].save());install_follower(r,self.payload)
        o=api.ndspy.code.loadOverlayTable(r.arm9OverlayTable,lambda oid,fid:r.files[fid],{1})[1]
        f.uc.mem_write(0x022059AC,bytes(o.data[0x022059AC-o.ramAddress:0x02205A34-o.ramAddress]))
    def execute(self,name,*args):return self.f.execute(name,*args)
    def test_default_and_native_permission_rules_forward_unchanged(self):
        self.execute('EnhancedFollowerUpdate',self.f.field)
        self.assertEqual((self.removed,self.initialized),([],[]))
        for native in (0,1):
            self.permission=native
            self.assertEqual(self.execute('EnhancedFollowerPermission',50,121),native)
        self.assertEqual(self.native_queries,[(50,121),(50,121)])
        self.f.put(self.extra+20,1)
        self.assertEqual(self.execute('EnhancedFollowerPermission',152,33),0)
        self.assertEqual(len(self.native_queries),2)
    def test_real_native_remove_then_recreate_never_touches_other_objects(self):
        f=self.f;wild_before=bytes(f.uc.mem_read(f.objects,0x258))
        self.execute('EnhancedFollowerUpdate',f.field);f.put(self.extra+20,1)
        self.execute('EnhancedFollowerUpdate',f.field)
        self.assertEqual(self.removed,[self.mon]);self.assertEqual(bytes(f.uc.mem_read(f.field+0xF9,2)),b'\0\0')
        for _ in range(3):self.execute('EnhancedFollowerUpdate',f.field)
        self.assertEqual(self.removed,[self.mon])
        f.put(self.extra+20,0);self.execute('EnhancedFollowerUpdate',f.field)
        self.assertEqual(self.initialized,[f.manager]);self.assertEqual(bytes(f.uc.mem_read(f.field+0xFA,1)),b'\1')
        self.assertEqual((f.get(self.state+16),f.get(self.state+20)),(1,1))
        self.assertEqual(bytes(f.uc.mem_read(f.objects,0x258)),wild_before)
    def test_busy_task_and_unsupported_avatar_defer_without_losing_transition(self):
        f=self.f;self.execute('EnhancedFollowerUpdate',f.field);f.put(self.extra+20,1)
        self.allowed=False;self.execute('EnhancedFollowerUpdate',f.field);self.assertEqual(self.removed,[])
        self.allowed=True;f.put(f.field+0x10,1);self.execute('EnhancedFollowerUpdate',f.field);self.assertEqual(self.removed,[])
        f.put(f.field+0x10,0);f.put(self.avatar+0x18,9);self.execute('EnhancedFollowerUpdate',f.field);self.assertEqual(self.removed,[])
        f.put(self.avatar+0x18,0);self.execute('EnhancedFollowerUpdate',f.field);self.assertEqual(self.removed,[self.mon])
    def test_reenable_respects_native_map_permission_and_empty_healthy_party(self):
        f=self.f;f.put(self.extra+20,1);self.execute('EnhancedFollowerUpdate',f.field)
        self.permission=0;f.put(self.extra+20,0);self.execute('EnhancedFollowerUpdate',f.field)
        self.assertEqual(f.get(self.state+20),0);self.assertEqual(bytes(f.uc.mem_read(f.field+0xFA,1)),b'\0')
        f.put(self.extra+20,1);self.execute('EnhancedFollowerUpdate',f.field)
        self.alive=0;f.put(self.extra+20,0);self.execute('EnhancedFollowerUpdate',f.field)
        self.assertEqual(len(self.initialized),1)
    def test_follower_initialization_loads_owned_journal_before_permission(self):
        f=self.f;data=bytearray(api.record(f.owner,7,(1,1,1,1,1,1,1,0,1,0,0,1)))
        import zlib
        struct.pack_into('<I',data,212,256);struct.pack_into('<I',data,252,zlib.crc32(data[:252])&0xFFFFFFFF)
        f.install(0,bytes(data));f.put(f.state+8,0)
        self.assertEqual(self.execute('EnhancedFollowerField',f.manager),f.field)
        self.assertEqual(f.get(self.extra+20),1)
        self.assertEqual(self.execute('EnhancedFollowerPermission',152,33),0)
        self.assertEqual(self.native_queries,[])
    def test_both_rom_hooks_change_only_audited_calls_and_reject_context_mutation(self):
        for original in self.roms:
            r=api.ndspy.rom.NintendoDSRom(original.save());main,overlays=install_follower(r,self.payload)
            self.assertEqual({m.address for m in main},{0x02069A04,0x02069B7A,0x02069A64,0x02069BCE})
            self.assertEqual([(o.overlay,o.patch.address) for o in overlays],[(1,0x02205A10)])
            verify_field_files(original,r,overlays)
            changed={i for m in main for i in range(m.address-0x02000000,m.address-0x02000000+4)}
            self.assertTrue(all(a==b or i in changed for i,(a,b) in enumerate(zip(original.arm9,r.arm9))))
            damaged=api.ndspy.rom.NintendoDSRom(original.save());a=bytearray(damaged.arm9);a[0x69FF4]^=1;damaged.arm9=bytes(a)
            with self.assertRaises(api.PatchMismatch):install_follower(damaged,self.payload)
