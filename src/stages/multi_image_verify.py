"""
Stage 10: Multi-Image Verification

Cross-validates front and side images for consistency.
Checks vehicle identity, location proximity, and temporal consistency.
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from src.utils.embedding_utils import EmbeddingManager
from src.utils.geo_utils import haversine_distance
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MultiImageVerifier:
    """Cross-view consistency checker for multi-image reports."""

    def __init__(self, embedding_manager=None, max_distance_m=20, max_time_diff_min=5, min_similarity=0.75):
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.max_distance_m = max_distance_m
        self.max_time_diff_min = max_time_diff_min
        self.min_similarity = min_similarity

    def verify(self, image1, image2, gps1=None, gps2=None, ts1=None, ts2=None, plate1=None, plate2=None) -> dict:
        emb1 = self.embedding_manager.generate_embedding(image1)
        emb2 = self.embedding_manager.generate_embedding(image2)
        similarity = float(np.dot(emb1, emb2))

        location_ok = True
        if gps1 and gps2:
            dist = haversine_distance(gps1[0], gps1[1], gps2[0], gps2[1])
            location_ok = dist <= self.max_distance_m

        time_ok = True
        if ts1 and ts2:
            time_ok = abs((ts1 - ts2).total_seconds()) <= self.max_time_diff_min * 60

        plate_ok = True
        if plate1 and plate2:
            plate_ok = plate1 == plate2

        consistent = similarity >= self.min_similarity and location_ok and time_ok and plate_ok

        result = {
            "consistent": consistent,
            "visual_similarity": round(similarity, 3),
            "location_consistent": location_ok,
            "time_consistent": time_ok,
            "plate_consistent": plate_ok,
        }
        logger.info(f"Multi-image verification: {result}")
        return result
