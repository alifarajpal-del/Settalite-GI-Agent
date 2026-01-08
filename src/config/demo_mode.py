"""Demo mode configuration for Heritage Sentinel Pro."""
from pathlib import Path
import sys

DEMO_MODE = True  # True to enable mock/demo experience
MOCK_DATA_SOURCE = True  # True to rely on mock data service
MOCK_SERVICE = None

if DEMO_MODE:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))

    if MOCK_DATA_SOURCE:
        try:
            from src.services.mock_data_service import MockDataService

            MOCK_SERVICE = MockDataService()
            print("Mock data service loaded successfully")
        except ImportError as exc:
            print(f"Warning: mock data service was not loaded: {exc}")
            DEMO_MODE = False
            MOCK_DATA_SOURCE = False
            MOCK_SERVICE = None
