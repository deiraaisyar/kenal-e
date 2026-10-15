"""Contract smoke test with an injected encoder; never downloads model weights."""
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from gradio_client import Client, handle_file
from app import build_app
from reference import ReferenceIndex

reference = ReferenceIndex(Path(__file__).resolve().parents[1] / "artifacts")
row = int(np.flatnonzero(reference.macro == 13)[0])

class TestEncoder:
    def encode(self, image, key):
        return reference.vit[row] if key == "vit" else reference.dino[row]
    def describe(self):
        return {"test_double": True}

demo = build_app(TestEncoder(), reference)
try:
    _, url, _ = demo.launch(server_name="127.0.0.1", server_port=7862,
                           prevent_thread_lock=True, quiet=True, max_file_size="12mb")
    client = Client(url, verbose=False)
    assert client.predict(api_name="/health")["encoder_ready"] is True
    with tempfile.TemporaryDirectory() as folder:
        image = Path(folder) / "sample.png"
        Image.new("RGB", (32, 32), "white").save(image)
        output = client.predict(handle_file(str(image)), "both", api_name="/embed")
        assert set(output["embeddings"]) == {"vit", "dinov3"}
        assert all(len(value) == 768 for value in output["embeddings"].values())
        result = client.predict(handle_file(str(image)), api_name="/predict")
        assert result["category"]["id"] == 13
        assert result["status"] == "needs_review"
        assert result["recognized"] is False
        assert result["price"] is None
    print("PASS: health, multipart upload, embed and predict via Gradio client (test encoder).")
finally:
    demo.close()
