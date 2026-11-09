"""Launch gates under enabled policy. Original legacy tests run with switch off."""
import time
import pytest
from fastapi.testclient import TestClient
from app import accounts, main, monetization, spend, playbilling, mail_limits


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(accounts, 'DATABASE_URL', '')
    monkeypatch.setattr(accounts, 'SQLITE_PATH', str(tmp_path/'policy.sqlite3'))
    monkeypatch.setenv('MONETIZATION_ENABLED', '1')
    monkeypatch.setenv('PLAY_FUNDED_RESERVE_VERIFIED', '1')
    monkeypatch.setenv('PLAY_BASE_PLAN_ID', 'annual-prepaid')
    monkeypatch.setattr(spend, '_ready', False)
    monkeypatch.setattr(spend, 'TOTAL_CAP', 20)
    monkeypatch.setattr(spend, 'DAILY_CAP', 3)
    monetization.REQUEST_USER.set(None)
    yield
    monetization.REQUEST_USER.set(None)


def paid(uid='paid1', **fields):
    with accounts.Conn() as c:
        c.run('INSERT INTO entitlements(user_id,plan_id,state,expiry_at,source,last_verified_at,schema_version) VALUES(?,?,?,?,?,?,?)',
              (uid, fields.get('plan_id','pro_yearly'), fields.get('state','active'), fields.get('expiry',time.time()+3600),
               fields.get('source','play'), fields.get('verified',time.time()), fields.get('schema',1)))
    return {'id':uid}


@pytest.mark.parametrize('fields', [{'state':'hold'},{'state':'expired'},{'state':'revoked'},{'source':'manual'},
                                   {'plan_id':'free'},{'expiry':0},{'verified':0},{'schema':99},{'expiry':float('nan')}])
def test_no_unverified_entitlement(isolated,fields):
    assert not monetization.paid_record(paid(**fields))


def test_active_and_grace_entitlement(isolated):
    assert monetization.paid_record(paid())
    assert monetization.paid_record(paid('grace',state='grace'))


@pytest.mark.parametrize('path', ['/api/session','/api/session/x/answer','/api/session/x/retry','/api/negotiation/x/say',
                                  '/api/coding/problems/two-sum/hint','/api/coding/problems/two-sum/evaluate','/api/prep/coding','/api/detect-country'])
def test_hidden_cost_paths_require_account(isolated,path):
    assert TestClient(main.app).post(path,json={}).status_code==401


def test_security_and_curated_endpoints_not_paywalled(isolated):
    c=TestClient(main.app)
    assert c.get('/privacy').status_code==200
    assert c.get('/api/bank/roles').status_code==200
    assert c.get('/api/coding/problems').status_code==200
    assert c.get('/api/plan').json()['purchase_available'] is False


def test_provider_guard_rejects_missing_identity(isolated):
    with pytest.raises(spend.BudgetExceeded): spend.reserve(.01)


def test_daily_per_user_not_global_and_restart_safe(isolated):
    u=paid();monetization.REQUEST_USER.set(u)
    for _ in range(8): spend.reserve(.001)
    with pytest.raises(spend.BudgetExceeded): spend.reserve(.001)
    monetization.REQUEST_USER.set(paid('other'))
    spend.reserve(.001)
    monetization.REQUEST_USER.set(u)
    spend._cache.update(t=0)
    with pytest.raises(spend.BudgetExceeded): spend.reserve(.001)


def test_reservation_settlement_updates_user_and_global(isolated):
    monetization.REQUEST_USER.set(paid())
    reservation=spend.reserve(.1);spend.settle(reservation,.01)
    with accounts.Conn() as c:
        assert c.run('SELECT micro FROM paid_ai_usage')[0]['micro']==10001
        assert c.run('SELECT micro FROM spend')[0]['micro']==10001


def test_year_budget_and_uncertain_failure_retains_charge(isolated):
    monetization.REQUEST_USER.set(paid())
    spend.reserve(1.1)
    with pytest.raises(spend.BudgetExceeded): spend.reserve(.2)


def receipt(state='SUBSCRIPTION_STATE_ACTIVE',ack='ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'):
    from datetime import datetime,timezone,timedelta
    return {'regionCode':'IN','subscriptionState':state,'acknowledgementState':ack,'lineItems':[{
        'productId':monetization.PRODUCT_ID,'offerDetails':{'basePlanId':'annual-prepaid'},
        'expiryTime':(datetime.now(timezone.utc)+timedelta(days=365)).isoformat()}]}


def test_forged_receipt_and_wrong_product_never_grant(isolated,monkeypatch):
    monkeypatch.setattr(playbilling,'configured',lambda:True)
    d=receipt();d['lineItems'][0]['productId']='wrong'
    monkeypatch.setattr(playbilling,'fetch_purchase',lambda token:d)
    with pytest.raises(playbilling.InvalidPurchase): playbilling.verify({'id':'u'},'token-valid-length')
    assert not monetization.paid_record({'id':'u'})


def test_first_claim_binding_restore_and_idempotency(isolated,monkeypatch):
    monkeypatch.setattr(playbilling,'configured',lambda:True)
    monkeypatch.setattr(playbilling,'fetch_purchase',lambda token:receipt())
    assert playbilling.verify({'id':'a'},'test-purchase-token')['state']=='active'
    assert playbilling.verify({'id':'a'},'test-purchase-token')['state']=='active'
    with pytest.raises(playbilling.InvalidPurchase): playbilling.verify({'id':'b'},'test-purchase-token')
    assert not monetization.paid_record({'id':'b'})


@pytest.mark.parametrize('state', ['SUBSCRIPTION_STATE_ON_HOLD','SUBSCRIPTION_STATE_PAUSED','SUBSCRIPTION_STATE_EXPIRED','SUBSCRIPTION_STATE_PENDING'])
def test_hold_pending_expired_no_paid_access(isolated,monkeypatch,state):
    monkeypatch.setattr(playbilling,'configured',lambda:True)
    monkeypatch.setattr(playbilling,'fetch_purchase',lambda token:receipt(state))
    playbilling.verify({'id':'a'},'test-purchase-token')
    assert not monetization.paid_record({'id':'a'})


def test_ack_failure_never_grants_access(isolated,monkeypatch):
    monkeypatch.setattr(playbilling,'configured',lambda:True)
    monkeypatch.setattr(playbilling,'fetch_purchase',lambda token:receipt(ack='ACKNOWLEDGEMENT_STATE_PENDING'))
    def fail(token): raise playbilling.BillingUnavailable('test failure')
    monkeypatch.setattr(playbilling,'acknowledge',fail)
    with pytest.raises(playbilling.BillingUnavailable): playbilling.verify({'id':'a'},'test-purchase-token')
    assert not monetization.paid_record({'id':'a'})


def test_email_limit_free_security_and_hashed_storage(isolated,monkeypatch):
    monkeypatch.setenv('EMAIL_LIMITS_ENABLED','1')
    for _ in range(3): mail_limits.reserve('private@example.com')
    with pytest.raises(RuntimeError): mail_limits.reserve('private@example.com')
    mail_limits.reserve('other@example.com')
    with accounts.Conn() as c:
        assert all('@' not in r['bucket'] for r in c.run('SELECT bucket FROM email_send_counts'))


def test_region_must_be_verified_google_data(isolated,monkeypatch):
    d=receipt();d['regionCode']='CA'
    with pytest.raises(playbilling.InvalidPurchase): playbilling.inspect_purchase(d,{'id':'u'})
    d.pop('regionCode')
    with pytest.raises(playbilling.InvalidPurchase): playbilling.inspect_purchase(d,{'id':'u'})


def test_us_allowance_not_client_region(isolated):
    u=paid();u['region']='US';monetization.REQUEST_USER.set(u)
    with pytest.raises(spend.QuotaExceeded): spend.reserve(1.3)
    with accounts.Conn() as c:
        c.run('CREATE TABLE IF NOT EXISTS play_regions (user_id TEXT PRIMARY KEY, region TEXT NOT NULL)')
        c.run('INSERT INTO play_regions(user_id,region) VALUES(?,?)',(u['id'],'US'))
    spend.reserve(1.3)


def test_feature_quota_under_shared_cap(isolated):
    monetization.REQUEST_USER.set(paid())
    t=monetization.REQUEST_FEATURE.set('resume')
    try:
        for _ in range(3):spend.reserve(.001)
        with pytest.raises(spend.QuotaExceeded):spend.reserve(.001)
    finally:monetization.REQUEST_FEATURE.reset(t)
    spend.reserve(.001)


def test_paid_policy_hard_off_and_cohort_full(isolated,monkeypatch):
    with pytest.raises(ValueError):monetization.prepare_purchase({'id':'u'})
    monkeypatch.setattr(monetization,'plan_info',lambda user:{'purchase_available':True})
    monkeypatch.setenv('PLAY_LAUNCH_COHORT','2')
    assert monetization.prepare_purchase({'id':'u'})['ok']
    assert monetization.prepare_purchase({'id':'u'})['ok']
    assert monetization.prepare_purchase({'id':'v'})['ok']
    with pytest.raises(ValueError):monetization.prepare_purchase({'id':'third'})


def test_cohort_never_admits_unfunded_us_max(isolated,monkeypatch):
    monkeypatch.setattr(monetization,'plan_info',lambda user:{'purchase_available':True})
    monkeypatch.setenv('PLAY_LAUNCH_COHORT','2')
    monkeypatch.setattr(spend,'TOTAL_CAP',5)
    with pytest.raises(ValueError):monetization.prepare_purchase({'id':'u'})


def test_replaced_receipt_cannot_restore_old_entitlement(isolated,monkeypatch):
    monkeypatch.setattr(playbilling,'configured',lambda:True)
    monkeypatch.setattr(playbilling,'fetch_purchase',lambda token:receipt())
    playbilling.verify({'id':'u'},'old-purchase-token')
    d=receipt();d['linkedPurchaseToken']='old-purchase-token'
    monkeypatch.setattr(playbilling,'fetch_purchase',lambda token:d)
    playbilling.verify({'id':'u'},'new-purchase-token')
    with pytest.raises(playbilling.InvalidPurchase):playbilling.verify({'id':'u'},'old-purchase-token')


def test_notification_requires_oidc_before_body(isolated):
    with pytest.raises(playbilling.InvalidPurchase):playbilling.process_notification('',{})
    assert TestClient(main.app).post('/api/billing/play/notifications',json={}).status_code==401


def test_paid_provider_input_limit_no_charge(isolated,monkeypatch):
    from app import llm
    monetization.REQUEST_USER.set(paid())
    with pytest.raises(llm.LLMError,match='input_limit'):llm.chat([{'role':'user','content':'x'*48001}])
    with accounts.Conn() as c:
        assert not c.run("SELECT name FROM sqlite_master WHERE type='table' AND name='paid_ai_usage'")


def test_zero_funding_stops_provider_before_reservation(isolated,monkeypatch):
    monkeypatch.delenv('PLAY_FUNDED_RESERVE_VERIFIED',raising=False)
    monetization.REQUEST_USER.set(paid())
    with pytest.raises(spend.BudgetExceeded,match='funding'):spend.reserve(.000001)


def test_zero_budget_stops_even_prepaid_credits(isolated,monkeypatch):
    monkeypatch.setattr(spend,'TOTAL_CAP',0)
    monkeypatch.setattr(spend,'DAILY_CAP',0)
    monetization.REQUEST_USER.set(paid())
    with pytest.raises(spend.BudgetExceeded):spend.reserve(.000001)
