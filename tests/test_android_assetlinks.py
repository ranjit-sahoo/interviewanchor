import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

PLAY_CERT = 'C7:25:D1:72:F4:BC:6B:4A:BD:DC:78:AE:BF:B1:EB:B3:99:48:D4:AE:B7:CD:C5:CD:65:DC:F4:D4:CA:DC:26:65'
UPLOAD_CERT = '73:D6:AA:AD:49:89:1B:FE:84:5A:9F:AF:0F:9B:DD:CA:7F:7A:24:D6:A5:24:48:4E:A6:8E:D1:D1:D6:B5:02:70'

def test_distribution_and_upload_keys_are_associated():
    response = TestClient(app).get('/.well-known/assetlinks.json', follow_redirects=False)
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/json'
    assert response.headers['cache-control'] == 'public, max-age=300'
    data = response.json()
    assert len(data) == 1
    assert data[0]['relation'] == ['delegate_permission/common.handle_all_urls']
    target = data[0]['target']
    assert target['namespace'] == 'android_app'
    assert target['package_name'] == 'com.ranjitsahoo.mockrep'
    assert PLAY_CERT in target['sha256_cert_fingerprints']
    assert UPLOAD_CERT in target['sha256_cert_fingerprints']
    assert len(target['sha256_cert_fingerprints']) == len(set(target['sha256_cert_fingerprints']))

def test_one_authoritative_assetlinks_route():
    from app.hub import router
    assert len([r for r in app.routes if getattr(r, 'path', None) == '/.well-known/assetlinks.json']) == 1
    assert not any(getattr(r, 'path', None) == '/.well-known/assetlinks.json' for r in router.routes)

def test_android_origin_matches_association():
    manifest = Path('android-twa/app/src/main/AndroidManifest.xml').read_text()
    statements = Path('android-twa/app/src/main/res/values/strings.xml').read_text()
    assert 'https://mockrep.onrender.com/practice' in manifest
    assert 'https://mockrep.onrender.com' in statements
