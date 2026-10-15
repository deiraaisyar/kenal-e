"""Notebook-compatible CLS encoders. DINOv3 is required; no DINOv2 fallback."""
import os
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError
import torch
import torch.nn.functional as F

MODELS = {
    "vit": ("google/vit-base-patch16-224-in21k", "b4569560a39a0f1af58e3ddaf17facf20ab919b0"),
    "dinov3": ("facebook/dinov3-vitb16-pretrain-lvd1689m", "5931719e67bbdb9737e363e781fb0c67687896bc"),
}
TTA_VIEWS = ("identity", "hflip", "rotate+10", "rotate-10")
MAX_BYTES = 12 * 1024 * 1024
MAX_PIXELS = 20_000_000


def read_image(path):
    if not path:
        raise ValueError("Unggah satu foto terlebih dahulu.")
    if Path(path).stat().st_size > MAX_BYTES:
        raise ValueError("Ukuran foto maksimal 12 MB.")
    try:
        with Image.open(path) as img:
            if img.width * img.height > MAX_PIXELS:
                raise ValueError("Resolusi foto maksimal 20 megapiksel.")
            # Same RGB conversion as the notebook, without new EXIF/cropping rules.
            return img.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("File tidak dapat dibaca sebagai gambar.") from exc


def tta_images(img):
    return [
        img,
        img.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
        img.rotate(10, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(128, 128, 128)),
        img.rotate(-10, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(128, 128, 128)),
    ]


@torch.inference_mode()
def cls_embedding(images, processor, model, device):
    inputs = processor(images=images, return_tensors="pt").to(device)
    cls = model(**inputs).last_hidden_state[:, 0, :]
    views = F.normalize(cls, p=2, dim=1)
    # For ViT this is one view; DINOv3 has four normalized views.
    result = F.normalize(views.mean(dim=0, keepdim=True), p=2, dim=1)
    vector = result[0].float().cpu().numpy()
    if vector.shape != (768,) or not np.isfinite(vector).all():
        raise RuntimeError("Encoder menghasilkan embedding yang tidak valid.")
    return vector


class Encoders:
    def __init__(self):
        from transformers import AutoImageProcessor, AutoModel

        zero = os.getenv("SPACES_ZERO_GPU", "").lower() in ("1", "true", "yes")
        self.device = "cuda" if zero or torch.cuda.is_available() else "cpu"
        if self.device == "cpu":
            torch.set_num_threads(min(2, os.cpu_count() or 1))
        self.processors, self.models = {}, {}
        for key, (model_id, revision) in MODELS.items():
            options = {"revision": revision, "token": os.getenv("HF_TOKEN") or None}
            self.processors[key] = AutoImageProcessor.from_pretrained(
                model_id, backend="pil" if key == "vit" else "torchvision", **options
            )
            self.models[key] = AutoModel.from_pretrained(
                model_id, **options
            ).to(self.device).eval()

    def encode(self, image, key):
        if key not in MODELS:
            raise ValueError("Encoder harus vit atau dinov3.")
        images = tta_images(image) if key == "dinov3" else [image]
        return cls_embedding(images, self.processors[key], self.models[key], self.device)

    def describe(self):
        return {key: {"model_id": model_id, "revision": revision,
                      "dimensions": 768, "tta_views": list(TTA_VIEWS) if key == "dinov3" else ["identity"]}
                for key, (model_id, revision) in MODELS.items()}
