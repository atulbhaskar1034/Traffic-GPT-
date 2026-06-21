"""
Embedding utility functions for the GRIDLOCK pipeline.

Handles image embedding generation (CLIP/DINOv2) and FAISS
vector similarity search for duplicate report detection.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingManager:
    """Manages image embeddings and FAISS similarity search.

    Generates image embeddings using CLIP ViT-B/32 and stores them
    in a FAISS index for efficient nearest-neighbor lookup.
    """

    def __init__(
        self,
        model_name: str = "ViT-B-32",
        pretrained: str = "openai",
        faiss_index_path: Optional[Path] = None,
        similarity_threshold: float = 0.92,
    ):
        """Initialize the embedding manager.

        Args:
            model_name: CLIP model variant.
            pretrained: Pretrained weights source.
            faiss_index_path: Path to existing FAISS index file.
            similarity_threshold: Cosine similarity threshold for duplicate detection.
        """
        self.model_name = model_name
        self.pretrained = pretrained
        self.faiss_index_path = faiss_index_path
        self.similarity_threshold = similarity_threshold

        self._model = None
        self._preprocess = None
        self._tokenizer = None
        self._index = None
        self._metadata: List[dict] = []

    def _load_model(self):
        """Lazy-load the CLIP model on first use."""
        if self._model is not None:
            return

        import open_clip
        import torch

        self._model, _, self._preprocess = open_clip.create_model_and_transforms(
            self.model_name, pretrained=self.pretrained
        )
        self._model.eval()
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = self._model.to(self._device)
        logger.info(f"Loaded CLIP model {self.model_name} on {self._device}")

    def _load_faiss_index(self):
        """Load or create a FAISS index."""
        if self._index is not None:
            return

        import faiss

        if self.faiss_index_path and Path(self.faiss_index_path).exists():
            self._index = faiss.read_index(str(self.faiss_index_path))
            logger.info(f"Loaded FAISS index from {self.faiss_index_path}")
        else:
            # Create a new flat L2 index (512-d for ViT-B/32)
            self._index = faiss.IndexFlatIP(512)  # Inner product for cosine sim
            logger.info("Created new FAISS index (512-d, Inner Product)")

    def generate_embedding(self, image: np.ndarray) -> np.ndarray:
        """Generate a normalized embedding for a single image.

        Args:
            image: BGR numpy array (OpenCV format).

        Returns:
            Normalized embedding vector (512-d float32).
        """
        import torch
        from PIL import Image as PILImage

        from src.utils.image_utils import bgr_to_rgb

        self._load_model()

        # Convert BGR numpy → RGB PIL → preprocessed tensor
        rgb = bgr_to_rgb(image)
        pil_image = PILImage.fromarray(rgb)
        tensor = self._preprocess(pil_image).unsqueeze(0).to(self._device)

        with torch.no_grad():
            embedding = self._model.encode_image(tensor)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)

        return embedding.cpu().numpy().astype(np.float32).flatten()

    def search_duplicates(
        self,
        embedding: np.ndarray,
        top_k: int = 5,
    ) -> Tuple[bool, float, List[dict]]:
        """Search for duplicate images in the FAISS index.

        Args:
            embedding: Query embedding vector.
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            Tuple of (is_duplicate, max_similarity, matching_metadata).
        """
        self._load_faiss_index()

        if self._index.ntotal == 0:
            return False, 0.0, []

        # Ensure correct shape for FAISS
        query = embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self._index.search(query, min(top_k, self._index.ntotal))

        max_sim = float(scores[0][0]) if len(scores[0]) > 0 else 0.0
        is_duplicate = max_sim >= self.similarity_threshold

        matches = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx >= 0 and idx < len(self._metadata):
                matches.append({**self._metadata[idx], "similarity": float(score)})

        return is_duplicate, max_sim, matches

    def add_to_index(self, embedding: np.ndarray, metadata: dict):
        """Add an embedding to the FAISS index.

        Args:
            embedding: Normalized embedding vector.
            metadata: Associated metadata (user_id, timestamp, plate, etc.).
        """
        self._load_faiss_index()
        vector = embedding.reshape(1, -1).astype(np.float32)
        self._index.add(vector)
        self._metadata.append(metadata)
        logger.debug(f"Added embedding to FAISS index. Total: {self._index.ntotal}")

    def save_index(self, path: Optional[Path] = None):
        """Persist the FAISS index to disk.

        Args:
            path: File path to save the index. Uses default if None.
        """
        import faiss

        save_path = path or self.faiss_index_path
        if save_path and self._index is not None:
            faiss.write_index(self._index, str(save_path))
            logger.info(f"Saved FAISS index to {save_path} ({self._index.ntotal} vectors)")
