"""Tests for Astram data loader and integration."""

import pytest

from src.data.astram_loader import AstramDataLoader


@pytest.fixture(scope="module")
def astram():
    """Load Astram data once for all tests."""
    loader = AstramDataLoader()
    return loader.load()


class TestAstramDataLoader:
    def test_loads_all_records(self, astram):
        assert len(astram.events) > 8000
        assert len(astram.events) <= 8200

    def test_events_have_gps(self, astram):
        for event in astram.events[:100]:
            assert event.latitude > 12.0
            assert event.longitude > 77.0

    def test_vehicle_types_present(self, astram):
        types = {e.vehicle_type for e in astram.events if e.vehicle_type}
        assert "bmtc_bus" in types
        assert "heavy_vehicle" in types
        assert "private_car" in types

    def test_hotspots_detected(self, astram):
        assert len(astram.hotspots) > 0
        top = astram.hotspots[0]
        assert top["event_count"] >= 5
        assert "center_lat" in top
        assert "center_lon" in top

    def test_police_station_lookup(self, astram):
        # Yelahanka area (known from data)
        station = astram.get_police_station(13.10, 77.58)
        assert station is not None
        assert isinstance(station, str)

    def test_nearby_events(self, astram):
        # Mekhri Circle area (known hotspot)
        nearby = astram.get_nearby_events(12.999, 77.580, radius_km=1.0)
        assert len(nearby) > 0

    def test_breakdown_locations(self, astram):
        breakdowns = astram.get_breakdown_locations()
        assert len(breakdowns) > 4000  # ~4,896 breakdowns
        lat, lon, vtype = breakdowns[0]
        assert lat > 12.0
        assert lon > 77.0

    def test_corridor_stats(self, astram):
        stats = astram.get_corridor_stats()
        assert "Non-corridor" in stats
        assert "Mysore Road" in stats

    def test_vehicle_type_stats(self, astram):
        stats = astram.get_vehicle_type_stats()
        assert "bmtc_bus" in stats
        assert stats["bmtc_bus"] > 1000

    def test_junction_lookup(self, astram):
        # Near Silk Board junction area
        junction = astram.get_nearest_junction(12.917, 77.623)
        assert junction is None or isinstance(junction, str)

    def test_hotspot_check(self, astram):
        # Check a location that should be a hotspot
        if astram.hotspots:
            top = astram.hotspots[0]
            is_hot, info = astram.is_known_hotspot(top["center_lat"], top["center_lon"])
            assert is_hot is True
            assert info is not None
