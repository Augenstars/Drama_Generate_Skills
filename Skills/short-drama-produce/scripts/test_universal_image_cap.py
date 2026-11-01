"""Offline universal-cap checks at production and direct compiler boundaries."""
import unittest
from pathlib import Path

import production_tool as prod
from provider_adapters import compile_gpt_image_2_payload
from video_contract_bridge import validate_reference_images


class UniversalProductionImageCapTests(unittest.TestCase):
    def test_every_modality_model_and_adapter_obeys_the_same_image_limit(self):
        for modality in ['image', 'video', 'tts', 'music']:
            for model in ['seedance-2.0', 'seedance-2.5', 'wan-3.0', 'minimax-h3', 'custom', None]:
                with self.subTest(modality=modality, model=model):
                    job = {'modality': modality, 'adapter': 'custom', 'parameters': {'model': model},
                           'references': [f'{i}.png' for i in range(9)]}
                    validate_reference_images(job)
                    job['references'].append('tenth.png')
                    with self.assertRaisesRegex(ValueError, '上限 9 张'):
                        validate_reference_images(job)

    def test_audio_video_references_do_not_take_image_slots(self):
        job = {'references': [f'{i}.png' for i in range(9)] + ['voice.wav', 'clip.mp4']}
        validate_reference_images(job)
        job['references'].append('tenth.webp')
        with self.assertRaisesRegex(ValueError, '上限 9 张'):
            validate_reference_images(job)
        validate_reference_images({'references': [f'{i}.png' for i in range(9)] + ['notes.txt', 'captions.srt']})

    def test_extensionless_and_inline_image_inputs_cannot_bypass_limit(self):
        for refs in [[f'file{i}' for i in range(10)], ['data:image/png;base64,TEST']*10]:
            with self.subTest(refs=refs), self.assertRaisesRegex(ValueError, '上限 9 张'):
                validate_reference_images({'references': refs})
        validate_reference_images({'references': ['voice']*10,
            'reference_bindings': [{'path': 'voice', 'role': 'reference_audio'}]})

    def test_picture_bindings_with_opaque_paths_are_counted(self):
        with self.assertRaisesRegex(ValueError, '上限 9 张'):
            validate_reference_images({'reference_bindings': [{'role': 'reference_image', 'path': f'opaque-{i}'} for i in range(10)]})

    def test_input_representations_are_not_added_twice(self):
        validate_reference_images({'references': [f'{i}.png' for i in range(9)],
            'reference_bindings': [{'role': 'reference_image', 'path': f'{i}.png'} for i in range(9)]})

    def test_generic_prepare_and_saved_job_paths_both_reject_ten(self):
        refs = [f'{i}.png' for i in range(10)]
        raw = {'job_id': 'nine-policy', 'modality': 'image', 'adapter': 'custom',
               'prompt': '测试', 'references': refs, 'outputs': ['制作成果/test.png'], 'parameters': {}}
        with self.assertRaisesRegex(ValueError, '上限 9 张'):
            prod._normalize_job(Path('.').resolve(), raw)
        saved = {key: None for key in prod.STORED_JOB_KEYS}
        saved.update({'schema_version': prod.JOB_SCHEMA, 'job_id': 'nine-policy', 'modality': 'image',
                      'adapter': 'custom', 'prompt': '测试', 'references': refs,
                      'reference_bindings': [], 'source': None, 'source_entry': None})
        with self.assertRaisesRegex(ValueError, '上限 9 张'):
            prod._validate_stored_job(Path('.').resolve(), saved)

    def test_direct_image_compiler_cannot_bypass_shared_policy(self):
        job = {'modality': 'image', 'prompt': '测试', 'references': [f'{i}.png' for i in range(10)],
               'outputs': ['out.png'], 'parameters': {}}
        with self.assertRaisesRegex(ValueError, '上限 9 张'):
            compile_gpt_image_2_payload(job)


if __name__ == '__main__':
    unittest.main()
