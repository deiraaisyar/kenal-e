"""Hugging Face Gradio Space entry point. Import spaces before torch."""
import os
from pathlib import Path
import time

import spaces
import gradio as gr

from encoder import Encoders, read_image
from reference import ReferenceIndex

ROOT = Path(__file__).resolve().parent


def build_app(encoders, reference):
    @spaces.GPU(duration=20)
    def embed_gpu(image, selected):
        keys = ("vit", "dinov3") if selected == "both" else (selected,)
        return {key: encoders.encode(image, key).tolist() for key in keys}

    @spaces.GPU(duration=20)
    def predict_gpu(image):
        match = reference.match_macro(encoders.encode(image, "vit"))
        dino = None if match["unknown"] else encoders.encode(image, "dinov3")
        return reference.result(match, dino)

    def load_upload(photo):
        try:
            return read_image(photo)
        except (ValueError, OSError) as exc:
            raise gr.Error(str(exc)) from None

    def embed(photo, selected="dinov3"):
        if selected not in ("vit", "dinov3", "both"):
            raise gr.Error("Pilih vit, dinov3, atau both.")
        image = load_upload(photo)
        started = time.monotonic()
        vectors = embed_gpu(image, selected)
        return {"schema_version": "1.0", "models": encoders.describe(),
                "embeddings": vectors, "elapsed_seconds": round(time.monotonic()-started, 3)}

    def predict(photo):
        if reference is None:
            raise gr.Error("Referensi klaster belum tersedia. Endpoint embed tetap dapat digunakan.")
        image = load_upload(photo)
        return predict_gpu(image)

    def health():
        return {"status": "ready", "encoder_ready": True,
                "reference_ready": reference is not None, "models": encoders.describe(),
                "recognition_validated": False}

    with gr.Blocks(title="Still E-Okay — AI", delete_cache=(3600, 3600)) as demo:
        gr.Markdown("# Still E-Okay\nUnggah satu foto barang elektronik untuk melihat kandidat kategorinya.")
        gr.Markdown("Hasil awal memerlukan verifikasi. Kondisi fungsi barang dan harga belum dinilai.")
        photo = gr.File(label="Foto barang", file_types=[".jpg", ".jpeg", ".png", ".webp", ".bmp"], type="filepath")
        analyze = gr.Button("Analisis foto", variant="primary")
        result = gr.JSON(label="Hasil analisis")
        analyze.click(predict, inputs=photo, outputs=result, api_name="predict",
                      concurrency_limit=1, concurrency_id="encoder")
        with gr.Accordion("Encoder dan pemeriksaan API", open=False):
            selected = gr.Dropdown(["dinov3", "vit", "both"], value="dinov3", label="Encoder")
            extract = gr.Button("Ambil embedding")
            embedding = gr.JSON(label="Embedding")
            extract.click(embed, inputs=[photo, selected], outputs=embedding, api_name="embed",
                          concurrency_limit=1, concurrency_id="encoder")
            check = gr.Button("Status layanan")
            status = gr.JSON(label="Status")
            check.click(health, outputs=status, api_name="health", queue=False)
    return demo.queue(max_size=8, default_concurrency_limit=1)


if __name__ == "__main__":
    # Module-level startup placement is required for ZeroGPU CUDA emulation.
    encoders = Encoders()
    reference = ReferenceIndex(ROOT / "artifacts") if (ROOT / "artifacts/reference.npz").exists() else None
    demo = build_app(encoders, reference)
    demo.launch(server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1") if not os.getenv("SPACE_ID") else "0.0.0.0",
                server_port=int(os.getenv("PORT", "7860")), max_file_size="12mb", show_error=False)
