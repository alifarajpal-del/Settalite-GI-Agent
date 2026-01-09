"""
Test suite for coordinate parser
Run: python scripts/test_coords_parser.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.coords_parser import parse_coords, normalize_latlon, is_valid_coords


def test_parser():
    """Run all coordinate parser tests."""
    tests = [
        # Test 1: Simple decimal comma-separated
        ("31.9522, 35.2332", (31.9522, 35.2332), "Decimal comma-separated"),
        
        # Test 2: Simple decimal space-separated
        ("31.9522 35.2332", (31.9522, 35.2332), "Decimal space-separated"),
        
        # Test 3: Decimal with extra text
        ("Location: 31.9522, 35.2332 (Jerusalem)", (31.9522, 35.2332), "Decimal with noise"),
        
        # Test 4: DMS format with symbols
        ('31°57\'08"N 35°14\'00"E', (31.952222, 35.233333), "DMS with symbols"),
        
        # Test 5: DMS format with spaces
        ("31 57 08 N, 35 14 00 E", (31.952222, 35.233333), "DMS with spaces"),
        
        # Test 6: DMS with decimal seconds
        ('31°57\'08.5"N 35°14\'00.2"E', (31.952361, 35.233389), "DMS with decimal seconds"),
        
        # Test 7: Google Maps URL with @
        ("https://www.google.com/maps/@31.9522,35.2332,15z", (31.9522, 35.2332), "Google Maps @ URL"),
        
        # Test 8: Google Maps URL with ?q=
        ("https://maps.google.com/?q=31.9522,35.2332", (31.9522, 35.2332), "Google Maps query URL"),
        
        # Test 9: Google Maps URL with ?ll=
        ("https://www.google.com/maps?ll=31.9522,35.2332", (31.9522, 35.2332), "Google Maps ll URL"),
        
        # Test 10: Negative coordinates (South/West)
        ("-33.8688, 151.2093", (-33.8688, 151.2093), "Negative decimal (Sydney)"),
        
        # Test 11: DMS with South/West
        ('33°52\'08"S 151°12\'33"E', (-33.868889, 151.209167), "DMS South"),
        
        # Test 12: Edge case - near zero
        ("0.1, 0.1", (0.1, 0.1), "Near-zero coordinates"),
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 70)
    print("COORDINATE PARSER TEST SUITE")
    print("=" * 70)
    print()
    
    for i, (input_str, expected, description) in enumerate(tests, 1):
        try:
            result = parse_coords(input_str)
            
            # Compare with tolerance for DMS conversions (±0.0001 degrees = ~11m)
            lat_match = abs(result[0] - expected[0]) < 0.0001
            lon_match = abs(result[1] - expected[1]) < 0.0001
            
            if lat_match and lon_match:
                print(f"✓ Test {i:2d}: PASS - {description}")
                print(f"           Input:    {input_str[:50]}")
                print(f"           Expected: {expected}")
                print(f"           Got:      {result}")
                passed += 1
            else:
                print(f"✗ Test {i:2d}: FAIL - {description}")
                print(f"           Input:    {input_str}")
                print(f"           Expected: {expected}")
                print(f"           Got:      {result}")
                print(f"           Delta:    lat={abs(result[0]-expected[0]):.6f}, lon={abs(result[1]-expected[1]):.6f}")
                failed += 1
        except Exception as e:
            print(f"✗ Test {i:2d}: ERROR - {description}")
            print(f"           Input:    {input_str}")
            print(f"           Expected: {expected}")
            print(f"           Error:    {str(e)}")
            failed += 1
        
        print()
    
    # Test validation function
    print("-" * 70)
    print("VALIDATION TESTS")
    print("-" * 70)
    print()
    
    validation_tests = [
        ((31.9522, 35.2332), True, "Valid coordinates"),
        ((91.0, 35.2332), False, "Invalid latitude > 90"),
        ((31.9522, 181.0), False, "Invalid longitude > 180"),
        ((-91.0, 35.2332), False, "Invalid latitude < -90"),
    ]
    
    for coords, expected_valid, description in validation_tests:
        result = is_valid_coords(*coords)
        if result == expected_valid:
            print(f"✓ {description}: {coords} → {result}")
            passed += 1
        else:
            print(f"✗ {description}: {coords} → Expected {expected_valid}, got {result}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = test_parser()
    sys.exit(0 if success else 1)
