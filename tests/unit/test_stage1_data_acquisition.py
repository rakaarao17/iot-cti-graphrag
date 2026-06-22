"""
Unit Tests for Stage 1: Data Acquisition

Tests for downloading and validating IoT datasets.
"""

import sys
from pathlib import Path
import tempfile

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_config
from src.core.exceptions import DataError


class TestStage1DataAcquisition:
    """Test suite for data acquisition stage."""

    def test_config_has_data_paths(self):
        """Test that config provides data directory paths."""
        config = get_config()
        
        assert hasattr(config, 'DATA_RAW_DIR'), "Config missing DATA_RAW_DIR"
        assert hasattr(config, 'DATA_PROCESSED_DIR'), "Config missing DATA_PROCESSED_DIR"
        assert hasattr(config, 'DATA_SAMPLES_DIR'), "Config missing DATA_SAMPLES_DIR"
        
        assert config.DATA_RAW_DIR.exists(), f"DATA_RAW_DIR does not exist: {config.DATA_RAW_DIR}"
        assert config.DATA_PROCESSED_DIR.exists(), f"DATA_PROCESSED_DIR does not exist: {config.DATA_PROCESSED_DIR}"
        assert config.DATA_SAMPLES_DIR.exists(), f"DATA_SAMPLES_DIR does not exist: {config.DATA_SAMPLES_DIR}"
        
        print("✓ All data directories exist and accessible")

    def test_sample_datasets_present(self):
        """Test that sample datasets are present for quick development."""
        config = get_config()
        samples_dir = config.DATA_SAMPLES_DIR
        
        sample_files = [
            "ciciot2023_sample.csv",
            "iot-23_sample.csv",
            "dev_sample.csv",
        ]
        
        found_samples = list(samples_dir.glob("*.csv"))
        assert len(found_samples) > 0, f"No CSV samples found in {samples_dir}"
        
        print(f"✓ Found {len(found_samples)} sample files in {samples_dir}")

    def test_data_paths_are_writable(self):
        """Test that data directories are writable."""
        config = get_config()
        
        for dir_path in [config.DATA_RAW_DIR, config.DATA_PROCESSED_DIR, config.DATA_SAMPLES_DIR]:
            test_file = dir_path / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                print(f"✓ {dir_path.name} is writable")
            except Exception as e:
                raise AssertionError(f"Cannot write to {dir_path}: {e}")


def main():
    """Run all Stage 1 tests."""
    print("\n" + "=" * 70)
    print("  Stage 1: Data Acquisition - Unit Tests")
    print("=" * 70)
    
    test = TestStage1DataAcquisition()
    
    try:
        print("\n[1/3] Testing config data paths...")
        test.test_config_has_data_paths()
        
        print("\n[2/3] Testing sample datasets...")
        test.test_sample_datasets_present()
        
        print("\n[3/3] Testing directory writeability...")
        test.test_data_paths_are_writable()
        
        print("\n" + "=" * 70)
        print("  Results: 3/3 passed ✓")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
