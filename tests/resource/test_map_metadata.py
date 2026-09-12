#!/usr/bin/env python3
"""tests/resource/test_map_metadata.py — Regression Test Suite for Map Metadata.

Validates MAP.BIN room metadata recovery, entity spawns, trigger tables,
room adjacency, collision models, SCU DSP microcode specification,
and whole-file byte ownership reduction under T2-MAP-01.
"""

from pathlib import Path
import json
import unittest

from tools.map.map_collision import MapCollisionDecoder
from tools.map.map_entities import MapEntityExtractor
from tools.map.map_triggers import MapTriggerExtractor
from tools.map.map_metadata_parser import MapMetadataParser


class TestMapMetadataRecovery(unittest.TestCase):
    """Test suite for T2-MAP-01 map metadata recovery and structures."""

    @classmethod
    def setUpClass(cls):
        cls.ws_dir = Path("workstreams/T2-MAP-01")
        cls.intervals_path = cls.ws_dir / "map_unknown_intervals.json"
        cls.bounds_path = cls.ws_dir / "room_bounds.json"
        cls.entities_path = cls.ws_dir / "entity_spawn_tables.json"
        cls.adjacency_path = cls.ws_dir / "room_adjacency.json"
        cls.triggers_path = cls.ws_dir / "trigger_tables.json"
        cls.dsp_path = cls.ws_dir / "scu_dsp_map_program.json"
        cls.collision_path = cls.ws_dir / "collision_model.json"
        cls.ownership_v2_path = cls.ws_dir / "map_byte_ownership_v2.json"
        cls.world_graph_path = cls.ws_dir / "world_graph.json"

    def test_canonical_unknown_intervals_frozen(self):
        """Verify the 17 unknown intervals freeze exactly 708,608 bytes."""
        self.assertTrue(self.intervals_path.exists(), "map_unknown_intervals.json missing")
        data = json.loads(self.intervals_path.read_text())
        self.assertEqual(data["total_unknown_bytes"], 708608)
        self.assertEqual(len(data["intervals"]), 17)
        computed_sum = sum(itv["size"] for itv in data["intervals"])
        self.assertEqual(computed_sum, 708608)

    def test_room_bounds_recovery(self):
        """Verify 104 rooms have valid dimensions and camera boundaries."""
        self.assertTrue(self.bounds_path.exists(), "room_bounds.json missing")
        data = json.loads(self.bounds_path.read_text())
        self.assertEqual(data["total_rooms_with_bounds"], 104)
        self.assertEqual(len(data["rooms"]), 104)
        for room in data["rooms"]:
            self.assertGreater(room["room_dimensions"]["width_px"], 0)
            self.assertGreater(room["room_dimensions"]["height_px"], 0)
            self.assertIn("mode_flags", room["camera_constraints"])

    def test_entity_spawn_tables(self):
        """Verify entity spawn table contains >= 1,200 entities across rooms."""
        self.assertTrue(self.entities_path.exists(), "entity_spawn_tables.json missing")
        data = json.loads(self.entities_path.read_text())
        self.assertGreaterEqual(data["total_entities_spawned"], 1200)
        self.assertEqual(data["total_rooms"], 104)

    def test_room_adjacency_and_exits(self):
        """Verify room adjacency contains >= 10 proven exit transitions."""
        self.assertTrue(self.adjacency_path.exists(), "room_adjacency.json missing")
        data = json.loads(self.adjacency_path.read_text())
        self.assertGreaterEqual(data["total_transitions"], 10)
        for exit_rec in data["exits"][:10]:
            self.assertIn("source_room_id", exit_rec)
            self.assertIn("target_room_id", exit_rec)
            self.assertIn("trigger_coords", exit_rec)

    def test_trigger_tables(self):
        """Verify trigger volumes and event links are extracted."""
        self.assertTrue(self.triggers_path.exists(), "trigger_tables.json missing")
        data = json.loads(self.triggers_path.read_text())
        self.assertGreater(data["total_triggers"], 0)
        for trig in data["triggers"][:5]:
            self.assertIn("bounds", trig)
            self.assertIn("event_id", trig)

    def test_scu_dsp_map_specification(self):
        """Verify SCU DSP microcode specification for VDP2 RBG0 rotation."""
        self.assertTrue(self.dsp_path.exists(), "scu_dsp_map_program.json missing")
        data = json.loads(self.dsp_path.read_text())
        self.assertEqual(data["program_metadata"]["instruction_count"], 128)
        self.assertEqual(data["program_metadata"]["size_bytes"], 512)
        self.assertIn("RBG0_A", data["output_registers"])
        self.assertIn("RBG0_X0", data["output_registers"])
        self.assertIn("D0_00", data["input_registers"])

    def test_collision_model_specification(self):
        """Verify collision model specification parameters."""
        self.assertTrue(self.collision_path.exists(), "collision_model.json missing")
        data = json.loads(self.collision_path.read_text())
        self.assertEqual(data["tile_geometry"]["total_tiles_per_stage"], 1536)
        self.assertEqual(data["tile_geometry"]["tile_size_bytes"], 32)
        self.assertEqual(data["provenance"]["decompressed_buffer_size"], 49152)

    def test_byte_ownership_v2_reduction(self):
        """Verify 100% whole-file ownership and 0 remaining UNKNOWN bytes."""
        self.assertTrue(self.ownership_v2_path.exists(), "map_byte_ownership_v2.json missing")
        data = json.loads(self.ownership_v2_path.read_text())
        self.assertEqual(data["total_bytes"], 4036608)
        self.assertEqual(data["unknown_bytes_v1"], 708608)
        self.assertEqual(data["unknown_bytes_v2"], 0)
        self.assertEqual(data["unknown_reduction_bytes"], 708608)
        self.assertEqual(data["reduction_percentage"], 100.0)

        # Interval continuity check
        intervals = data["intervals"]
        self.assertEqual(intervals[0]["start"], 0)
        for i in range(len(intervals) - 1):
            self.assertEqual(
                intervals[i]["end"],
                intervals[i + 1]["start"],
                f"Discontinuity between interval {i} and {i+1}",
            )
        self.assertEqual(intervals[-1]["end"], 4036608)

    def test_world_graph_connectivity(self):
        """Verify world graph connections and properties."""
        self.assertTrue(self.world_graph_path.exists(), "world_graph.json missing")
        data = json.loads(self.world_graph_path.read_text())
        self.assertEqual(data["total_rooms"], 104)
        self.assertGreater(data["total_edges"], 0)
        self.assertGreater(data["connected_rooms"], 50)

    def test_negative_controls(self):
        """Negative controls: invalid buffer size and out-of-bounds access."""
        # Collision decoder rejects wrong buffer size
        with self.assertRaises(ValueError):
            MapCollisionDecoder(bytes(100))

        # Collision decoder rejects out of bounds tile index
        decoder = MapCollisionDecoder(bytes(49152))
        with self.assertRaises(IndexError):
            decoder.get_tile(1536)

        # Parser returns None for truncated / invalid sector
        parser = MapMetadataParser(bytes(4096))
        self.assertIsNone(parser.parse_room_header(bytes(4), 0, 0))


if __name__ == '__main__':
    unittest.main()
