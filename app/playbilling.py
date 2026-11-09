"""Google Play subscription verification. Never accepts a client-provided plan/state/expiry.

Launch remains disabled until merchant/product/API credentials and licensed tests
are complete. Store only backend receipt tokens, never expose them in exports/logs.
"""
import datetime
import hashlib
import os
import time
from urllib.parse import quote

from app import accounts, monetization


class BillingUnavailable(RuntimeError):
    pass


class InvalidPurchase(ValueError):
    pass


def configured():
    return bool(os.environ.get('PLAY_BILLING_ENABLED') == '1'
                and os.environ.get('PLAY_SERVICE_ACCOUNT_FILE')
                and os.environ.get('PLAY_BASE_PLAN_ID'))


def _session():
    if not configured():
        raise BillingUnavailable('Google Play purchase verification is not configured yet')
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    creds = service_account.Credentials.from_service_account_file(
        os.environ['PLAY_SERVICE_ACCOUNT_FILE'],
        scopes=['https://www.googleapis.com/auth/androidpublisher'])
    return AuthorizedSession(creds)


def _token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _base():
    return 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/' + monetization.PACKAGE_NAME


def fetch_purchase(token):
    # No redirects; no receipt/API credential can be forwarded to a different host.
    try:
        with _session() as session:
            r = session.get(_base() + '/purchases/subscriptionsv2/tokens/' + quote(token, safe=''),
                            timeout=15, allow_redirects=False)
            if r.status_code in (400, 404, 410):
                raise InvalidPurchase('Google Play could not verify this purchase')
            if r.status_code != 200:
                raise BillingUnavailable('Google Play verification is temporarily unavailable')
            return r.json()
    except (InvalidPurchase, BillingUnavailable):
        raise
    except Exception as e:
        raise BillingUnavailable('Google Play verification is temporarily unavailable') from e


def acknowledge(token):
    try:
        with _session() as session:
            r = session.post(_base() + '/purchases/subscriptions/' + monetization.PRODUCT_ID
                             + '/tokens/' + quote(token, safe='') + ':acknowledge',
                             json={}, timeout=15, allow_redirects=False)
            if r.status_code not in (200, 204):
                raise BillingUnavailable('Google Play acknowledgement is temporarily unavailable')
    except BillingUnavailable:
        raise
    except Exception as e:
        raise BillingUnavailable('Google Play acknowledgement is temporarily unavailable') from e


def _timestamp(value):
    try:
        return datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    except (AttributeError, TypeError, ValueError):
        raise InvalidPurchase('Google Play returned an invalid expiry')


def inspect_purchase(data, user):
    if data.get('regionCode') not in ('IN', 'US'):
        raise InvalidPurchase('This launch plan is available only in India and the United States')
    lines = data.get('lineItems')
    if not isinstance(lines, list) or len(lines) != 1:
        raise InvalidPurchase('Unexpected subscription product')
    item = lines[0]
    if (item.get('productId') != monetization.PRODUCT_ID
            or item.get('offerDetails', {}).get('basePlanId') != os.environ.get('PLAY_BASE_PLAN_ID')):
        raise InvalidPurchase('Unexpected subscription product or base plan')
    external = data.get('externalAccountIdentifiers', {}).get('obfuscatedExternalAccountId')
    expected = hashlib.sha256(user['id'].encode()).hexdigest()
    if external and external != expected:
        raise InvalidPurchase('This purchase belongs to another app account')
    state = data.get('subscriptionState')
    expiry = _timestamp(item.get('expiryTime'))
    # Cancellation keeps access for remaining paid time. Pending/hold/paused never grant.
    mapping = {'SUBSCRIPTION_STATE_ACTIVE': 'active', 'SUBSCRIPTION_STATE_IN_GRACE_PERIOD': 'grace',
               'SUBSCRIPTION_STATE_CANCELED': 'active', 'SUBSCRIPTION_STATE_ON_HOLD': 'hold',
               'SUBSCRIPTION_STATE_PAUSED': 'hold', 'SUBSCRIPTION_STATE_EXPIRED': 'expired',
               'SUBSCRIPTION_STATE_PENDING': 'free', 'SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED': 'free'}
    if state not in mapping:
        raise InvalidPurchase('Unknown Google Play purchase state')
    mapped = mapping[state] if expiry > time.time() else 'expired'
    return mapped, expiry


def _tables(c):
    c.run('CREATE TABLE IF NOT EXISTS play_receipts (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, token TEXT NOT NULL, created DOUBLE PRECISION NOT NULL)')
    c.run('CREATE TABLE IF NOT EXISTS play_current (user_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL)')
    c.run('CREATE TABLE IF NOT EXISTS play_regions (user_id TEXT PRIMARY KEY, region TEXT NOT NULL)')
    c.run('CREATE TABLE IF NOT EXISTS play_superseded (token_hash TEXT PRIMARY KEY)')


def verify(user, token):
    if not configured():
        raise BillingUnavailable('Purchases are not available yet')
    if not isinstance(token, str) or not 10 <= len(token) <= 4096 or any(ord(x) < 33 for x in token):
        raise InvalidPurchase('Invalid purchase token')
    hashed = _token_hash(token)
    # Serialize verification and acknowledgement in one durable gate. This is a
    # deliberately small launch, and prevents stale concurrent results overwriting
    # revocation or a linked replacement. No external response grants outside it.
    with accounts.Conn() as c:
        _tables(c)
        c.run('CREATE TABLE IF NOT EXISTS play_gate (id INTEGER PRIMARY KEY, marker INTEGER NOT NULL)')
        c.run('INSERT INTO play_gate(id,marker) VALUES(1,0) ON CONFLICT(id) DO NOTHING')
        if c.pg:
            c.run('SELECT id FROM play_gate WHERE id=1 FOR UPDATE')
        else:
            c.c.commit()
            c.run('BEGIN IMMEDIATE')
        if c.run('SELECT token_hash FROM play_superseded WHERE token_hash=?', (hashed,)):
            raise InvalidPurchase('This purchase was replaced by a newer subscription')
        existing = c.run('SELECT user_id FROM play_receipts WHERE token_hash=?', (hashed,))
        if existing and existing[0]['user_id'] != user['id']:
            raise InvalidPurchase('Restore using the InterviewAnchor account that bought this plan')
        data = fetch_purchase(token)
        state, expiry = inspect_purchase(data, user)
        linked = data.get('linkedPurchaseToken')
        if linked:
            old = c.run('SELECT user_id FROM play_receipts WHERE token_hash=?', (_token_hash(linked),))
            if old and old[0]['user_id'] != user['id']:
                raise InvalidPurchase('Linked subscription belongs to another app account')
        if state in ('active', 'grace') and data.get('acknowledgementState') == 'ACKNOWLEDGEMENT_STATE_PENDING':
            acknowledge(token)
        elif state in ('active', 'grace') and data.get('acknowledgementState') != 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED':
            raise InvalidPurchase('Unknown purchase acknowledgement state')
        if state == 'free':
            current = c.run('SELECT token_hash FROM play_current WHERE user_id=?', (user['id'],))
            if current and current[0]['token_hash'] == hashed:
                c.run("UPDATE entitlements SET state='hold',last_verified_at=? WHERE user_id=?", (time.time(), user['id']))
            return {'ok': False, 'state': 'pending', 'plan_id': 'free'}
        c.run('INSERT INTO play_receipts(token_hash,user_id,token,created) VALUES(?,?,?,?) ON CONFLICT(token_hash) DO NOTHING',
              (hashed, user['id'], token, time.time()))
        c.run('INSERT INTO play_regions(user_id,region) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET region=EXCLUDED.region', (user['id'], data['regionCode']))
        if linked:
            c.run('INSERT INTO play_superseded(token_hash) VALUES(?) ON CONFLICT(token_hash) DO NOTHING', (_token_hash(linked),))
        c.run('INSERT INTO play_current(user_id,token_hash) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET token_hash=EXCLUDED.token_hash', (user['id'], hashed))
        c.run('INSERT INTO entitlements(user_id,plan_id,state,expiry_at,source,last_verified_at,schema_version) VALUES(?,?,?,?,?,?,1) ON CONFLICT(user_id) DO UPDATE SET plan_id=EXCLUDED.plan_id,state=EXCLUDED.state,expiry_at=EXCLUDED.expiry_at,source=EXCLUDED.source,last_verified_at=EXCLUDED.last_verified_at,schema_version=1',
              (user['id'], 'pro_yearly', state, expiry, 'play', time.time()))
    return {'ok': True, 'state': state, 'expiry_at': expiry, 'plan_id': 'pro_yearly'}


def refresh(user):
    with accounts.Conn() as c:
        _tables(c)
        rows = c.run('SELECT p.token FROM play_receipts p JOIN play_current x ON p.token_hash=x.token_hash WHERE x.user_id=?', (user['id'],))
    if not rows:
        return None
    try:
        return verify(user, rows[0]['token'])
    except InvalidPurchase:
        with accounts.Conn() as c:
            c.run("UPDATE entitlements SET state='revoked',last_verified_at=? WHERE user_id=?", (time.time(), user['id']))
        raise


def process_notification(authorization, body):
    """Only authenticated Pub/Sub pushes for already-bound receipts. The message
    cannot grant a plan or select an app user; re-read the Publisher API instead.
    """
    import base64
    import json
    audience = os.environ.get('PLAY_RTDN_AUDIENCE')
    sender = os.environ.get('PLAY_RTDN_SERVICE_EMAIL')
    if not audience or not sender or not authorization.startswith('Bearer '):
        raise InvalidPurchase('Notification authentication required')
    try:
        from google.oauth2 import id_token
        from google.auth.transport.requests import Request
        claims = id_token.verify_oauth2_token(authorization[7:], Request(), audience=audience)
        if claims.get('email') != sender or claims.get('email_verified') is not True:
            raise ValueError('Invalid notification identity')
        raw = base64.b64decode(body['message']['data'], validate=True)
        if len(raw) > 16384:
            raise ValueError('Notification too long')
        message = json.loads(raw)
        if message.get('packageName') != monetization.PACKAGE_NAME:
            raise ValueError('Wrong package')
        if 'testNotification' in message:
            return {'ok': True}
        notification = message.get('subscriptionNotification') or message.get('voidedPurchaseNotification') or {}
        token = notification['purchaseToken']
        if not isinstance(token, str) or not 10 <= len(token) <= 4096:
            raise ValueError('Invalid receipt')
    except Exception as e:
        raise InvalidPurchase('Invalid notification') from e
    with accounts.Conn() as c:
        _tables(c)
        rows = c.run('SELECT user_id FROM play_receipts WHERE token_hash=?', (_token_hash(token),))
    if not rows or rows[0]['user_id'].startswith('deleted:'):
        return {'ok': True}  # no new account disclosures or grants from a push
    try:
        verify({'id': rows[0]['user_id']}, token)
    except InvalidPurchase:
        # Replaced receipt is harmless; malformed current receipt must fail closed.
        with accounts.Conn() as c:
            current = c.run('SELECT token_hash FROM play_current WHERE user_id=?', (rows[0]['user_id'],))
            if current and current[0]['token_hash'] == _token_hash(token):
                c.run("UPDATE entitlements SET state='revoked',last_verified_at=? WHERE user_id=?", (time.time(), rows[0]['user_id']))
    return {'ok': True}
