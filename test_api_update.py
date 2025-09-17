#!/usr/bin/env python3
"""
Test script to validate the updated c2pa-python API usage in app.py
This script tests the key components without requiring Flask or other dependencies.
"""

import json
import io
from c2pa import Builder, C2paSigningAlg, C2paSignerInfo, Signer, C2paError

def test_builder_creation():
    """Test that we can create a Builder with the new API"""
    manifest = {
        "title": "test.jpg",
        "format": "image/jpeg",
        "claim_generator_info": [
            {
                "name": "c2pa test",
                "version": "0.0.1"
            }
        ],
        "assertions": [
            {
                "label": "c2pa.actions",
                "data": {
                    "actions": [
                        {
                            "action": "c2pa.edited",
                            "softwareAgent": {
                                "name": "C2PA Python Example",
                                "version": "0.1.0"
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    try:
        with Builder(manifest) as builder:
            print("✓ Builder creation successful")
            return True
    except Exception as e:
        print(f"✗ Builder creation failed: {e}")
        return False

def test_signer_creation():
    """Test that we can create a Signer with the new API"""
    def dummy_callback(data: bytes) -> bytes:
        return b"dummy_signature"
    
    try:
        signer = Signer.from_callback(
            callback=dummy_callback,
            alg=C2paSigningAlg.ES256,
            certs="-----BEGIN CERTIFICATE-----\ndummy\n-----END CERTIFICATE-----",
            tsa_url="http://timestamp.digicert.com"
        )
        print("✓ Signer creation successful")
        signer.close()
        return True
    except Exception as e:
        print(f"✗ Signer creation failed: {e}")
        return False

def test_signer_info_creation():
    """Test that we can create a C2paSignerInfo with the new API"""
    try:
        signer_info = C2paSignerInfo(
            alg=C2paSigningAlg.ES256,
            sign_cert="-----BEGIN CERTIFICATE-----\ndummy\n-----END CERTIFICATE-----",
            private_key="-----BEGIN PRIVATE KEY-----\ndummy\n-----END PRIVATE KEY-----",
            ta_url=b"http://timestamp.digicert.com"
        )
        print("✓ C2paSignerInfo creation successful")
        return True
    except Exception as e:
        print(f"✗ C2paSignerInfo creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing updated c2pa-python API usage...")
    print("=" * 50)
    
    tests = [
        test_builder_creation,
        test_signer_creation,
        test_signer_info_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! The API update is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
