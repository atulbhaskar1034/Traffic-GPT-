"""
Astram Event Data Loader & Processor

Loads the Bangalore traffic event dataset (8,173 records) from the
Astram traffic management system. This real-world data provides:

1. Known violation hotspots (GPS clusters)
2. Vehicle breakdown locations (often illegally parked)
3. Police station jurisdictions
4. Corridor and junction mapping
5. Historical event patterns for model training context

Dataset: Nov 2023 – Apr 2024, covering all Bangalore corridors.
"""

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CSV_PATH = Path("data/Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv")


@dataclass
class TrafficEvent:
    """Parsed traffic event record from Astram data."""

    id: str
    event_type: str
    latitude: float
    longitude: float
    address: str
    event_cause: str
    requires_road_closure: bool
    start_datetime: Optional[datetime]
    status: str
    description: str
    vehicle_type: Optional[str]
    vehicle_number: Optional[str]
    corridor: str
    priority: str
    police_station: Optional[str]
    zone: Optional[str]
    junction: Optional[str]


class AstramDataLoader:
    """Loads and indexes Astram traffic event data for use across the pipeline.

    Provides:
    - Hotspot analysis (GPS clusters of frequent events)
    - Police station lookup by GPS location
    - Junction/corridor mapping
    - Vehicle breakdown patterns for training data context
    """

    def __init__(self, csv_path: Path = None):
        self.csv_path = csv_path or DEFAULT_CSV_PATH
        self._events: List[TrafficEvent] = []
        self._hotspots: List[dict] = []
        self._police_stations: Dict[str, List[Tuple[float, float]]] = {}
        self._junctions: Dict[str, List[Tuple[float, float]]] = {}
        self._loaded = False

    def load(self) -> "AstramDataLoader":
        """Load and parse the CSV data."""
        if self._loaded:
            return self

        logger.info(f"Loading Astram data from {self.csv_path}")

        with open(self.csv_path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    event = self._parse_row(row)
                    if event:
                        self._events.append(event)
                except Exception as e:
                    logger.debug(f"Skipping malformed row: {e}")

        # Build indices
        self._build_police_station_index()
        self._build_junction_index()
        self._build_hotspots()

        self._loaded = True
        logger.info(
            f"Loaded {len(self._events)} events, "
            f"{len(self._police_stations)} police stations, "
            f"{len(self._junctions)} junctions, "
            f"{len(self._hotspots)} hotspots"
        )
        return self

    def _parse_row(self, row: dict) -> Optional[TrafficEvent]:
        """Parse a CSV row into a TrafficEvent."""
        lat = float(row.get("latitude", 0) or 0)
        lon = float(row.get("longitude", 0) or 0)

        if lat == 0 or lon == 0:
            return None

        # Parse datetime
        start_dt = None
        dt_str = row.get("start_datetime", "")
        if dt_str and dt_str != "NULL":
            try:
                start_dt = datetime.fromisoformat(dt_str.replace("+00", "+00:00"))
            except (ValueError, TypeError):
                pass

        veh_type = row.get("veh_type", "")
        veh_no = row.get("veh_no", "")

        return TrafficEvent(
            id=row.get("id", ""),
            event_type=row.get("event_type", ""),
            latitude=lat,
            longitude=lon,
            address=row.get("address", ""),
            event_cause=row.get("event_cause", ""),
            requires_road_closure=row.get("requires_road_closure", "").upper() == "TRUE",
            start_datetime=start_dt,
            status=row.get("status", ""),
            description=row.get("description", ""),
            vehicle_type=veh_type if veh_type and veh_type != "NULL" else None,
            vehicle_number=veh_no if veh_no and veh_no != "NULL" else None,
            corridor=row.get("corridor", ""),
            priority=row.get("priority", ""),
            police_station=row.get("police_station", "") or None,
            zone=row.get("zone", "") or None,
            junction=row.get("junction", "") or None,
        )

    def _build_police_station_index(self):
        """Build GPS-indexed police station lookup."""
        for event in self._events:
            ps = event.police_station
            if ps and ps != "NULL":
                if ps not in self._police_stations:
                    self._police_stations[ps] = []
                self._police_stations[ps].append((event.latitude, event.longitude))

    def _build_junction_index(self):
        """Build GPS-indexed junction lookup."""
        for event in self._events:
            junc = event.junction
            if junc and junc != "NULL":
                if junc not in self._junctions:
                    self._junctions[junc] = []
                self._junctions[junc].append((event.latitude, event.longitude))

    def _build_hotspots(self, grid_resolution: float = 0.002):
        """Identify violation hotspots by GPS grid clustering.

        Groups events into geographic grid cells and identifies
        cells with high event density as hotspots.

        Args:
            grid_resolution: Grid cell size in degrees (~200m).
        """
        grid: Dict[Tuple[int, int], List[TrafficEvent]] = {}

        for event in self._events:
            grid_x = int(event.latitude / grid_resolution)
            grid_y = int(event.longitude / grid_resolution)
            key = (grid_x, grid_y)
            if key not in grid:
                grid[key] = []
            grid[key].append(event)

        # Hotspots: cells with 5+ events
        for key, events in sorted(grid.items(), key=lambda x: -len(x[1])):
            if len(events) < 5:
                continue

            lats = [e.latitude for e in events]
            lons = [e.longitude for e in events]
            causes = {}
            for e in events:
                causes[e.event_cause] = causes.get(e.event_cause, 0) + 1

            self._hotspots.append({
                "center_lat": sum(lats) / len(lats),
                "center_lon": sum(lons) / len(lons),
                "event_count": len(events),
                "top_cause": max(causes, key=causes.get),
                "causes": causes,
                "sample_address": events[0].address[:100],
            })

    # ─── Public Query API ─────────────────────────────────────

    @property
    def events(self) -> List[TrafficEvent]:
        """All loaded traffic events."""
        return self._events

    @property
    def hotspots(self) -> List[dict]:
        """GPS hotspots sorted by event density."""
        return self._hotspots

    def get_nearby_events(
        self, latitude: float, longitude: float, radius_km: float = 0.5
    ) -> List[TrafficEvent]:
        """Find historical events near a GPS location.

        Args:
            latitude: Query latitude.
            longitude: Query longitude.
            radius_km: Search radius in kilometers.

        Returns:
            List of nearby TrafficEvent records.
        """
        from src.utils.geo_utils import haversine_distance

        results = []
        for event in self._events:
            dist = haversine_distance(latitude, longitude, event.latitude, event.longitude)
            if dist <= radius_km * 1000:
                results.append(event)
        return results

    def get_police_station(self, latitude: float, longitude: float) -> Optional[str]:
        """Find the nearest police station for a GPS location.

        Uses the police station GPS index built from historical events.
        """
        from src.utils.geo_utils import haversine_distance

        best_station = None
        best_distance = float("inf")

        for station, coords in self._police_stations.items():
            # Use centroid of station's event locations
            avg_lat = sum(c[0] for c in coords) / len(coords)
            avg_lon = sum(c[1] for c in coords) / len(coords)
            dist = haversine_distance(latitude, longitude, avg_lat, avg_lon)
            if dist < best_distance:
                best_distance = dist
                best_station = station

        return best_station

    def get_nearest_junction(self, latitude: float, longitude: float) -> Optional[str]:
        """Find the nearest junction for a GPS location."""
        from src.utils.geo_utils import haversine_distance

        best_junction = None
        best_distance = float("inf")

        for junction, coords in self._junctions.items():
            avg_lat = sum(c[0] for c in coords) / len(coords)
            avg_lon = sum(c[1] for c in coords) / len(coords)
            dist = haversine_distance(latitude, longitude, avg_lat, avg_lon)
            if dist < best_distance:
                best_distance = dist
                best_junction = junction

        return best_junction if best_distance < 2000 else None  # Within 2km

    def is_known_hotspot(
        self, latitude: float, longitude: float, radius_km: float = 0.3
    ) -> Tuple[bool, Optional[dict]]:
        """Check if a location is a known traffic event hotspot.

        Args:
            latitude: Query latitude.
            longitude: Query longitude.
            radius_km: Hotspot match radius.

        Returns:
            Tuple of (is_hotspot, hotspot_info).
        """
        from src.utils.geo_utils import haversine_distance

        for hotspot in self._hotspots:
            dist = haversine_distance(
                latitude, longitude,
                hotspot["center_lat"], hotspot["center_lon"]
            )
            if dist <= radius_km * 1000:
                return True, hotspot
        return False, None

    def get_vehicle_type_stats(self) -> Dict[str, int]:
        """Get vehicle type distribution from historical data."""
        stats = {}
        for event in self._events:
            if event.vehicle_type:
                stats[event.vehicle_type] = stats.get(event.vehicle_type, 0) + 1
        return dict(sorted(stats.items(), key=lambda x: -x[1]))

    def get_corridor_stats(self) -> Dict[str, int]:
        """Get corridor-wise event distribution."""
        stats = {}
        for event in self._events:
            if event.corridor:
                stats[event.corridor] = stats.get(event.corridor, 0) + 1
        return dict(sorted(stats.items(), key=lambda x: -x[1]))

    def get_breakdown_locations(self) -> List[Tuple[float, float, str]]:
        """Get all vehicle breakdown GPS locations with vehicle type.

        These locations are prime candidates for illegal parking
        since broken-down vehicles are often left on roads.
        """
        return [
            (e.latitude, e.longitude, e.vehicle_type or "unknown")
            for e in self._events
            if e.event_cause == "vehicle_breakdown"
        ]
