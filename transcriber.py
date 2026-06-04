import torch
from faster_whisper import WhisperModel

from logger import get_logger


def _get_device_and_model():
    if torch.cuda.is_available():
        return "cuda", "large-v3", "float16"
    return "cpu", "medium", "int8"


class Transcriber:
    def __init__(self):
        self.model = None
        self.device = None
        self.model_size = None

    def load(self):
        device, model_size, compute_type = _get_device_and_model()
        self.device = device
        self.model_size = model_size
        get_logger().info("[Transcriber] Loading model %s on %s...", model_size, device)
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        get_logger().info("[Transcriber] Model loaded.")

    def reload(self):
        self.model = None
        self.load()

    def transcribe(self, audio_path: str) -> str:
        if self.model is None:
            raise RuntimeError("Модель не загружена. Вызовите load() сначала.")
        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            language=None,
            vad_filter=True,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text
