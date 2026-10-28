"""Prevent cleanup from losing inputs, working builds or verification bytes."""
from pathlib import Path
import hashlib
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts import cleanup_builds as clean


def digest(data):
    return hashlib.sha256(data).hexdigest()


class TestBuildCleanup(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='cleanup-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root/'native').mkdir()
        (self.root/'native/config.h').write_text('project marker')
        self.source = self.root/'original.nds'
        self.source.write_bytes(b'original-input')
        self.decoder = self.root/'xdelta-test'
        self.decoder.write_text('#!'+sys.executable+'\nimport sys,shutil\nshutil.copyfile(sys.argv[-2],sys.argv[-1])\n')
        self.decoder.chmod(0o755)
        for number in range(1, 6): self.artifact(number)
        self.live = patch.object(clean, 'live_verification', return_value=False)
        self.live.start()
        self.addCleanup(self.live.stop)

    def artifact(self, number):
        path = self.root/f'build/candidates/heartgold-visual-plus-gameplay-milestone-{number:02}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        data = f'generated-{number}'.encode()
        path.with_suffix('.nds').write_bytes(data)
        path.with_suffix('.xdelta').write_bytes(data)
        path.write_text(json.dumps({'kind':'experimental-gameplay-milestone','game':'heartgold',
            'output_sha256':digest(data),'patch_sha256':digest(data),
            'source_rom_sha256':digest(self.source.read_bytes())}))
        return path

    def run_cleanup(self, **kwargs):
        return clean.cleanup(self.root, sources=[self.source], decoder=str(self.decoder),
                             compress=False, **kwargs)

    def test_preview_changes_nothing_and_keeps_two_newest(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = self.run_cleanup()
        self.assertEqual(result['kept_milestones'], [4,5])
        self.assertEqual(len(result['removed_roms']), 3)
        self.assertEqual(before, {p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_apply_proves_restoration_before_pruning_and_keeps_patches_reports_inputs_saves(self):
        save = self.root/'build/candidates/my-save.sav';save.write_bytes(b'precious-save')
        baseline = self.root/'build/baseline/reference.nds';baseline.parent.mkdir();baseline.write_bytes(b'baseline')
        result = self.run_cleanup(apply=True)
        self.assertEqual(len(result['removed_roms']), 3)
        for number in range(1,6):
            stem = self.root/f'build/candidates/heartgold-visual-plus-gameplay-milestone-{number:02}'
            self.assertEqual(stem.with_suffix('.nds').exists(), number>=4)
            self.assertTrue(stem.with_suffix('.json').is_file())
            self.assertTrue(stem.with_suffix('.xdelta').is_file())
        self.assertEqual(self.source.read_bytes(), b'original-input')
        self.assertEqual(save.read_bytes(), b'precious-save')
        self.assertEqual(baseline.read_bytes(), b'baseline')

    def test_latest_verified_milestone_retained_even_with_newer_experiments(self):
        p = self.root/'enhancements/milestone-1-verification.json';p.parent.mkdir()
        p.write_text(json.dumps({'kind':'bounded-local-gameplay-verification','milestone':1}))
        self.assertEqual(self.run_cleanup(apply=True)['kept_milestones'], [1,4,5])
        self.assertTrue(self.artifact_path(1).with_suffix('.nds').is_file())

    def artifact_path(self, n):
        return self.root/f'build/candidates/heartgold-visual-plus-gameplay-milestone-{n:02}.json'

    def test_generated_rom_with_user_save_is_retained(self):
        rom=self.artifact_path(1).with_suffix('.nds')
        rom.with_suffix('.sav').write_bytes(b'user-progress')
        result=self.run_cleanup(apply=True)
        self.assertTrue(rom.is_file())
        self.assertEqual(rom.with_suffix('.sav').read_bytes(),b'user-progress')
        self.assertIn(str(rom.relative_to(self.root)),result['deferred'])

    def test_changed_patch_or_output_is_left_untouched(self):
        one, two = self.artifact_path(1), self.artifact_path(2)
        one.with_suffix('.xdelta').write_bytes(b'changed patch')
        two.with_suffix('.nds').write_bytes(b'changed output')
        result=self.run_cleanup(apply=True)
        self.assertEqual(len(result['deferred']),2)
        self.assertTrue(one.with_suffix('.nds').is_file())
        self.assertEqual(two.with_suffix('.nds').read_bytes(),b'changed output')

    def test_bad_decoder_cannot_delete_original_generated_rom(self):
        self.decoder.write_text('#!'+sys.executable+'\nimport sys\nopen(sys.argv[-1],"wb").write(b"wrong")\n')
        with self.assertRaisesRegex(ValueError,'could not reproduce'):self.run_cleanup(apply=True)
        self.assertEqual(self.artifact_path(1).with_suffix('.nds').read_bytes(), b'generated-1')

    def test_changed_registered_input_is_not_used_for_pruning(self):
        registry=self.root/'local_data/cleanup/inputs.json';registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps({'sources':{digest(b'original-input'):str(self.source)}}))
        self.source.write_bytes(b'changed source')
        with self.assertRaisesRegex(ValueError,'Original ROM changed'):
            clean.cleanup(self.root,decoder=str(self.decoder),apply=True,compress=False)
        self.assertTrue(self.artifact_path(1).with_suffix('.nds').exists())

    def test_registered_source_is_never_deleted_even_inside_generated_directory(self):
        original=self.artifact_path(1).with_suffix('.nds')
        result=clean.cleanup(self.root,sources=[self.source,original],decoder=str(self.decoder),apply=True,compress=False)
        self.assertTrue(original.is_file())
        self.assertIn(str(original.relative_to(self.root)),result['deferred'])

    def test_symlinked_rom_and_unknown_files_are_not_touched(self):
        path=self.artifact_path(1).with_suffix('.nds');path.unlink();path.symlink_to(self.source)
        unknown=self.root/'build/candidates/unknown.nds';unknown.write_bytes(b'unknown')
        self.run_cleanup(apply=True)
        self.assertTrue(path.is_symlink());self.assertEqual(self.source.read_bytes(),b'original-input')
        self.assertEqual(unknown.read_bytes(),b'unknown')

    def test_redirected_build_root_refused(self):
        other=self.root/'other';(self.root/'build').rename(other);(self.root/'build').symlink_to(other,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'redirected'):self.run_cleanup(apply=True)

    def test_live_verification_defers_pruning(self):
        with patch.object(clean,'live_verification',return_value=True):
            result=self.run_cleanup(apply=True)
        self.assertEqual(result['removed_roms'],[])
        self.assertEqual(len(result['deferred']),3)

    def test_restore_exact_bytes_and_refuse_different_existing_output(self):
        self.run_cleanup(apply=True)
        report=self.artifact_path(1)
        clean.restore_rom(report,self.root,decoder=str(self.decoder))
        self.assertEqual(report.with_suffix('.nds').read_bytes(),b'generated-1')
        report.with_suffix('.nds').write_bytes(b'newer-work')
        with self.assertRaisesRegex(ValueError,'different existing'):
            clean.restore_rom(report,self.root,decoder=str(self.decoder))
        self.assertEqual(report.with_suffix('.nds').read_bytes(),b'newer-work')

    def test_failed_compression_never_replaces_evidence(self):
        source=self.root/'evidence.bin';source.write_bytes(b'E'*131072)
        def corrupt(command,**kwargs):Path(command[-1]).write_bytes(b'bad copy')
        with patch.object(clean.subprocess,'run',side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,'preserve bytes'):clean.compress_copy(source,self.root)
        self.assertEqual(source.read_bytes(),b'E'*131072)

    @unittest.skipUnless(sys.platform=='darwin','macOS transparent compression')
    def test_real_filesystem_compression_preserves_path_bytes_and_hash(self):
        source=self.root/'evidence.bin';data=b'evidence'+bytes(2*1024*1024);source.write_bytes(data)
        saved=clean.compress_copy(source,self.root)
        self.assertGreater(saved,0)
        self.assertEqual(source.read_bytes(),data)
        self.assertEqual(clean.sha(source),digest(data))
        self.assertEqual(clean.compress_copy(source,self.root),0)

    def test_missing_process_inventory_is_conservatively_busy(self):
        self.live.stop()
        with patch.object(clean.subprocess,'check_output',side_effect=OSError('unavailable')):
            self.assertTrue(clean.live_verification())

    def test_build_cleanup_runs_for_success_and_failure_without_masking_failure(self):
        with patch.object(clean,'cleanup',return_value={'reclaimed_bytes':0,'kept_milestones':[4,5]}) as run:
            with clean.after_build(self.source,str(self.decoder)):pass
            with self.assertRaisesRegex(RuntimeError,'build failed'):
                with clean.after_build(self.source,str(self.decoder)):raise RuntimeError('build failed')
        self.assertEqual(run.call_count,2)
        with patch.object(clean,'cleanup',side_effect=ValueError('cleanup error')):
            with self.assertRaisesRegex(RuntimeError,'original failure'):
                with clean.after_build(self.source):raise RuntimeError('original failure')
