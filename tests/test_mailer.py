"""Offline transport contract tests. No real provider calls or messages."""
import json
from unittest.mock import Mock
import pytest
from app import mailer


@pytest.fixture(autouse=True)
def isolated_mail(monkeypatch):
    monkeypatch.setattr(mailer, 'HOST', '')
    monkeypatch.setattr(mailer, 'BREVO_API_KEY', '')
    monkeypatch.setattr(mailer, 'FROM', 'InterviewAnchor <verified@example.com>')


def transport(monkeypatch, status=201, body=None):
    conn = Mock()
    conn.getresponse.return_value.status = status
    conn.getresponse.return_value.read.return_value = json.dumps(
        body if body is not None else {'messageId': '<test-accepted>'}).encode()
    factory = Mock(return_value=conn)
    monkeypatch.setattr(mailer.http.client, 'HTTPSConnection', factory)
    monkeypatch.setattr(mailer, 'BREVO_API_KEY', 'unit-test-not-a-key')
    return factory, conn


def test_disabled_does_not_send():
    assert not mailer.enabled()
    with pytest.raises(RuntimeError, match='not configured'):
        mailer.send('test@example.com', 'Code', '123456')


def test_brevo_fixed_https_endpoint_and_plain_text(monkeypatch):
    factory, conn = transport(monkeypatch)
    assert mailer.enabled()
    mailer.send('test@example.com', 'Code', '123456')
    assert factory.call_args.args == ('api.brevo.com',)
    assert factory.call_args.kwargs['timeout'] == 15
    args, kwargs = conn.request.call_args
    assert args == ('POST', '/v3/smtp/email')
    assert kwargs['headers']['api-key'] == 'unit-test-not-a-key'
    data = json.loads(kwargs['body'])
    assert data == {'sender': {'name': 'InterviewAnchor', 'email': 'verified@example.com'},
                    'to': [{'email': 'test@example.com'}], 'subject': 'Code', 'textContent': '123456'}
    conn.close.assert_called_once()


@pytest.mark.parametrize('status', [301, 400, 401, 429, 500])
def test_provider_errors_are_sanitized_and_not_retried(monkeypatch, status):
    _, conn = transport(monkeypatch, status, {'secret': 'must-not-leak'})
    with pytest.raises(RuntimeError, match='provider rejected delivery') as error:
        mailer.send('test@example.com', 'Code', '123456')
    assert 'must-not-leak' not in str(error.value)
    assert conn.request.call_count == 1
    conn.close.assert_called_once()


def test_unconfirmed_send_is_failure(monkeypatch):
    _, conn = transport(monkeypatch, body={})
    with pytest.raises(RuntimeError, match='did not confirm'):
        mailer.send('test@example.com', 'Code', '123456')
    conn.close.assert_called_once()


def test_no_header_injection(monkeypatch):
    _, conn = transport(monkeypatch)
    with pytest.raises(ValueError):
        mailer.send('test@example.com\nBcc: another@example.com', 'Code', '123456')
    conn.request.assert_not_called()


def test_sender_required(monkeypatch):
    _, conn = transport(monkeypatch)
    monkeypatch.setattr(mailer, 'FROM', 'noreply@localhost')
    with pytest.raises(RuntimeError, match='sender not configured'):
        mailer.send('test@example.com', 'Code', '123456')
    conn.request.assert_not_called()


def test_resend_does_not_claim_success_on_transport_failure(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    monkeypatch.setattr(mailer, 'enabled', lambda: True)
    monkeypatch.setattr(mailer, 'send', Mock(side_effect=RuntimeError('private-provider-error')))
    r = c.post('/api/auth/register', json={'agree': True, 'age18': True,
             'email': 'delivery-failed@example.com', 'password': 'longenough1'})
    assert r.status_code == 200
    assert c.get('/api/auth/me').json()['email_verified'] is False
    r = c.post('/api/auth/resend-verification')
    assert r.status_code == 503
    assert 'private-provider-error' not in r.text
