"""Keep pre-billing functional unit tests independent of the payment boundary.
Production has no disabled-policy switch. Payment-boundary integration tests run
unmodified in test_monetization_launch.py; these older tests exercise internals
with the boundary replaced only in the test process.
"""
import pytest

@pytest.fixture(autouse=True)
def legacy_function_unit_boundary(request, monkeypatch):
    legacy = {'test_app.py', 'test_basic_in.py', 'test_fix_release.py',
              'test_privacy.py', 'test_security_account.py', 'test_validation_privacy.py'}
    if request.path.name in legacy:
        from app import monetization
        monkeypatch.setattr(monetization, 'enabled', lambda: False)
