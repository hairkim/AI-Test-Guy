from langchain.embeddings.base import Embeddings
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List

#embedding model
class MathBERTEmbeddings(Embeddings):
    def __init__(self, model_id: str, device: str, max_length: int = 512, batch_size: int = 16):
        self.model_id = model_id,
        self.device = device,
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
        self.model = AutoModel.from_pretrained(model_id, use_safetensors=True)  # force safetensors
        self.model.to(device)
        self.device = device
        self.max_length = max_length
        self.batch_size = batch_size

    @torch.no_grad()
    def _encode(self, texts: List[str]) -> List[List[float]]:
        embs = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            inputs = self.tokenizer(
                batch, padding=True, truncation=True, max_length=self.max_length, return_tensors="pt"
            ).to(self.device)

            h = self.model(**inputs).last_hidden_state        # [B, T, H]
            mask = inputs["attention_mask"].unsqueeze(-1).float()
            pooled = (h * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)   # mean pool
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)         # L2 norm
            embs.append(pooled.cpu())
        return torch.cat(embs, dim=0).tolist()

    # LangChain Embeddings interface
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._encode(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._encode([text])[0]