import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image
import torch

from encoder import cls_embedding, read_image, tta_images
from reference import ReferenceIndex, normalize


class EncoderTests(unittest.TestCase):
    def test_tta_preserves_dimensions_and_matches_notebook(self):
        img = Image.fromarray(np.arange(12 * 9 * 3, dtype=np.uint8).reshape(9, 12, 3))
        views = tta_images(img)
        self.assertEqual(len(views), 4)
        self.assertTrue(all(view.size == img.size for view in views))
        np.testing.assert_array_equal(np.asarray(views[1]), np.asarray(img)[:, ::-1])
        expected = img.rotate(10, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(128, 128, 128))
        np.testing.assert_array_equal(views[2], expected)

    def test_normalize_views_before_mean_not_raw_mean(self):
        cls = torch.zeros((4, 768))
        cls[0, 0] = 100
        cls[1:, 1] = 1

        class Batch(dict):
            def to(self, device):
                return self

        processor = lambda **kwargs: Batch()
        model = lambda **kwargs: SimpleNamespace(last_hidden_state=cls[:, None, :])
        result = cls_embedding([None]*4, processor, model, "cpu")
        expected = np.zeros(768, dtype=np.float32)
        expected[:2] = [1, 3]
        expected /= np.linalg.norm(expected)
        np.testing.assert_allclose(result, expected, atol=1e-6)

    def test_invalid_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.jpg"
            path.write_text("not an image")
            with self.assertRaises(ValueError):
                read_image(path)

    def test_large_dimensions_rejected_before_decode(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "large.png"
            Image.new("RGB", (5000, 4001)).save(path)
            with self.assertRaisesRegex(ValueError, "20 megapiksel"):
                read_image(path)

    def test_nonfinite_vector_rejected(self):
        with self.assertRaises(ValueError):
            normalize([np.nan, 1.0])
        with self.assertRaises(ValueError):
            normalize([0.0, 0.0])


class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = ReferenceIndex(Path(__file__).resolve().parents[1] / "artifacts")

    def test_target_artifact_matches_final_run(self):
        self.assertEqual(self.index.vit.shape, (3961, 768))
        self.assertEqual(len(set(zip(self.index.macro, self.index.sub))), 88)

    def test_noise_has_no_category_condition_or_price(self):
        result = self.index.result({"unknown": True, "macro_id": 26})
        self.assertEqual(result["status"], "unknown")
        for key in ("category", "subcategory", "condition", "price"):
            self.assertIsNone(result[key])

    def test_low_similarity_rejected(self):
        generator = np.random.default_rng(9)
        match = self.index.match_macro(normalize(generator.normal(size=768)))
        self.assertTrue(match["unknown"])

    def test_candidate_is_never_presented_as_validated_or_priced(self):
        idx = int(np.flatnonzero(self.index.macro == 13)[0])
        match = self.index.match_macro(self.index.vit[idx])
        self.assertEqual(match["macro_id"], 13)
        result = self.index.result(match, self.index.dino[idx])
        self.assertEqual(result["status"], "needs_review")
        self.assertFalse(result["recognized"])
        self.assertEqual(result["category"]["name"], "Papan sirkuit (PCB)")
        self.assertTrue(result["subcategory"]["global_id"].startswith("13_"))
        self.assertIsNone(result["price"])
        self.assertIsNone(result["condition"])


if __name__ == "__main__":
    unittest.main()
