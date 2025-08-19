from typing import List
from langchain.embeddings.base import Embeddings

class MathBERTEmbeddings(Embeddings):
    def __init__(self, model_id: str, device: str, max_length: int = 512, batch_size: int = 16):
        self.model_id = model_id            # <-- removed stray comma
        self.device = device
        self.max_length = max_length
        self.batch_size = batch_size
        # lazy-loaded
        self._tokenizer = None
        self._model = None

    def _ensure_loaded(self):
        if self._model is not None:
            return
        # Lazy import transformers here
        from transformers import AutoTokenizer, AutoModel
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self._model = AutoModel.from_pretrained(self.model_id, use_safetensors=True)
        # Lazy import torch here
        import torch
        self._model.to(self.device)
        self._model.eval()

    def _encode(self, texts: List[str]) -> List[List[float]]:
        # Lazy import torch here (no module-level import)
        import torch
        self._ensure_loaded()

        embs = []
        with torch.inference_mode():  # instead of @torch.no_grad()
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                inputs = self._tokenizer(
                    batch, padding=True, truncation=True,
                    max_length=self.max_length, return_tensors="pt"
                ).to(self.device)

                h = self._model(**inputs).last_hidden_state  # [B, T, H]
                mask = inputs["attention_mask"].unsqueeze(-1).float()
                pooled = (h * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)  # mean pool
                pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)        # L2 norm
                embs.append(pooled.cpu())

        return torch.cat(embs, dim=0).tolist()

    # LangChain interface
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._encode(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._encode([text])[0]
