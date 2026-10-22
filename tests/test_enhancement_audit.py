import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('audit_enhancements', ROOT / 'scripts/audit_enhancements.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class TestEnhancementAudit(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'enhancements/inventory.json').read_text())

    def test_inventory_is_internally_valid(self):
        self.assertEqual(audit.validate_inventory(self.data), [])

    def test_new_upstream_option_cannot_silently_disappear(self):
        keys = {k for r in self.data['features'] for k in r['emerald_keys']}
        self.assertIn('Missing Emerald option: newly_added_option',
                      audit.validate_inventory(self.data, keys | {'newly_added_option'}))

    def test_duplicate_key_cannot_hide_missing_feature(self):
        data = copy.deepcopy(self.data)
        data['features'][1]['emerald_keys'].append('speed')
        self.assertIn('Option assigned more than once: speed', audit.validate_inventory(data))

    def test_both_option_sources_are_parsed(self):
        with tempfile.TemporaryDirectory() as temporary:
            src = Path(temporary) / '3ds_port/src'
            src.mkdir(parents=True)
            (src / '3ds_extras.c').write_text('{CTR_EXTRAS_ENHANCEMENTS, CTR_TEXT("EXP", "EXP"), "exp_catch", 2},\n')
            (src / '3ds_settings.c').write_text('void CtrSettings_ApplyLine(void) { sscanf(line, "voxel_pitch=%d", &v); }\nvoid CtrSettings_Load(void) {}')
            self.assertEqual(audit.emerald_keys(Path(temporary)), {'exp_catch', 'voxel_pitch'})

    def test_incorrect_implementation_status_rejected(self):
        data = copy.deepcopy(self.data)
        data['features'][0]['implementation'] = 'probably_working'
        self.assertTrue(audit.validate_inventory(data))


if __name__ == '__main__':
    unittest.main()
