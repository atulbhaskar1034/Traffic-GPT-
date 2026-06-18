


"""
Stage 7: Duplicate Detection

Prevents multiple reports for the same illegally parked vehicle.
Uses CLIP embeddings + FAISS vector similarity search.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

from src.utils.embedding_utils import EmbeddingManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DuplicateDetector:
    """Detects duplicate parking violation reports using visual similarity and plate matching."""

    def __init__(self, embedding_manager=None, similarity_threshold=0.92, time_window_hours=24):
        self.embedding_manager = embedding_manager or EmbeddingManager(similarity_threshold=similarity_threshold)
        self.similarity_threshold = similarity_threshold
        self.time_window_hours = time_window_hours
        self._plate_cache = {}

    def check(self, image, plate_number=None, user_id=None, timestamp=None):
        now = timestamp or datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=self.time_window_hours)

        embedding = self.embedding_manager.generate_embedding(image)
        is_visual_dup, sim_score, visual_matches = self.embedding_manager.search_duplicates(embedding, top_k=3)

        is_duplicate = is_visual_dup
        duplicate_type = "visual" if is_visual_dup else None

        if plate_number and plate_number in self._plate_cache:
            cached = self._plate_cache[plate_number]
            if datetime.fromisoformat(cached["timestamp"]) >= cutoff:
                is_duplicate = True
                duplicate_type = "plate" if not duplicate_type else "visual+plate"

        metadata = {"user_id": user_id, "plate_number": plate_number, "timestamp": now.isoformat()}
        self.embedding_manager.add_to_index(embedding, metadata)
        if plate_number:
            self._plate_cache[plate_number] = metadata

        return {
            "is_duplicate": is_duplicate,
            "similarity_score": round(sim_score, 3),
            "duplicate_type": duplicate_type,
        }
