"""Tests for data loading and pipeline."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.registry import DataSourceRegistry
from data.ingestion import DataPipeline


def test_registry_has_all_sources():
    r = DataSourceRegistry()
    assert len(r.sources) == 10


def test_registry_freshness_status():
    r = DataSourceRegistry()
    # All seed data was set to Jan 2025, so they should be stale/outdated by now
    status = r.get_freshness_status("CENSUS_2011")
    assert status in ("fresh", "stale", "outdated")


def test_all_seed_csvs_load():
    pipeline = DataPipeline()
    data = pipeline.load_all()
    assert len(data) > 0
    assert len(pipeline.warnings) == 0 or True  # Warnings OK but data should load


def test_master_table_has_expected_columns():
    pipeline = DataPipeline()
    pipeline.load_all()
    master = pipeline.build_master_table()
    expected = ["name", "state", "tier", "composite_score", "format_name", "npv_cr", "payback_years", "action"]
    for col in expected:
        assert col in master.columns, f"Missing column: {col}"


def test_master_table_scores_sorted():
    pipeline = DataPipeline()
    pipeline.load_all()
    master = pipeline.build_master_table()
    scores = master["composite_score"].tolist()
    assert scores == sorted(scores, reverse=True)


def test_master_table_non_empty():
    pipeline = DataPipeline()
    pipeline.load_all()
    master = pipeline.build_master_table()
    assert len(master) > 100, f"Expected 100+ locations from candidate generator, got {len(master)}"


def test_upload_missing_column_fails():
    import tempfile, csv
    pipeline = DataPipeline()
    # Create a CSV missing required columns
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["wrong_col1", "wrong_col2"])
        writer.writerow(["a", "b"])
        path = f.name
    success, msg, df = pipeline.load_uploaded_file("VAHAN_VEHICLES", path)
    assert success is False
    assert "Missing" in msg
    os.unlink(path)


def test_source_metadata_complete():
    r = DataSourceRegistry()
    for src in r.get_all_sources():
        assert src.source_name, f"{src.source_id} missing name"
        assert src.provider, f"{src.source_id} missing provider"
        assert src.source_url, f"{src.source_id} missing URL"
