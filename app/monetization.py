"""Server-owned paid-AI policy. Launch switch stays off until store setup passes.

No client flag, price, role, or locally cached receipt can grant entitlement.
Curated/offline practice and security/data-rights tools are never paywalled.
"""
import contextvars
import math
import os
import time

REQUEST_USER = contextvars.ContextVar('ia_paid_request_user', default=None)
REQUEST_FEATURE = contextvars.ContextVar('ia_paid_feature', default='interview')
FEATURE_LIMITS = {'interview': (8, 40), 'resume': (3, 15), 'prep': (4, 20), 'coding': (3, 20), 'negotiation': (4, 20), 'recruiter': (3, 15)}
REGION_BUDGET_USD = {'IN': 1.20, 'US': 6.00}
MAX_INPUT_BYTES = 48000
MAX_OUTPUT_TOKENS = 4000
DAILY_CALLS = 8
MONTHLY_CALLS = 60
ROLLING_YEAR_USD = 1.20
PRODUCT_ID = 'interviewanchor_pro_yearly'
PACKAGE_NAME = 'com.ranjitsahoo.mockrep'


def enabled():
    return os.environ.get('MONETIZATION_ENABLED') == '1'


def paid_record(user):
    from app import entitlements
    ent = entitlements.record_for(user)
    expiry = ent.get('expiry_at')
    # A bounded validity window prevents a stale cached receipt being used forever.
    verified = ent.get('last_verified_at')
    return bool(ent.get('plan_id') == 'pro_yearly' and ent.get('source') == 'play'
                and ent.get('state') in ('active', 'grace')
                and isinstance(expiry, (int, float)) and math.isfinite(expiry) and expiry > time.time()
                and isinstance(verified, (int, float)) and math.isfinite(verified)
                and 0 <= time.time() - verified <= 3600)


def ai_route(method, path):
    """Conservative endpoint boundary, plus the provider-level guard in llm.chat.
    Reading an already generated report remains free; new report generation is
    checked at the model-call boundary. Bank curated reads are free too.
    """
    if method != 'POST':
        return False
    exact = {'/api/detect-country', '/api/resume/review', '/api/match', '/api/session',
             '/api/negotiation', '/api/recruiter/screen', '/api/builder/parse',
             '/api/builder/polish', '/api/builder/summary', '/api/prep',
             '/api/prep/coding', '/api/prep/resume-questions', '/api/star', '/api/company-brief'}
    if path in exact:
        return True
    return ((path.startswith('/api/session/') and path.endswith(('/answer', '/retry')))
            or (path.startswith('/api/negotiation/') and path.endswith('/say'))
            or (path.startswith('/api/coding/problems/') and path.endswith(('/evaluate', '/hint'))))


def validate_user():
    from app import spend
    if not enabled():
        return None
    user = REQUEST_USER.get()
    if not user or not paid_record(user):
        raise spend.PlanRequired("An active verified yearly plan is required for AI tools")
    return user


def reserve_user(c, usd_micro, user, now=None):
    """Called inside spend.reserve's global DB lock/transaction. Fail closed.
    A failed or uncertain provider request consumes its quota reservation.
    """
    if not enabled():
        return None
    from app import spend
    if not user:
        raise spend.PlanRequired('An active verified yearly plan is required for AI tools')
    now = time.time() if now is None else now
    day = time.strftime('%Y-%m-%d', time.gmtime(now))
    month = day[:7]
    c.run('CREATE TABLE IF NOT EXISTS paid_ai_usage (user_id TEXT NOT NULL, day TEXT NOT NULL, n INTEGER NOT NULL, micro BIGINT NOT NULL, PRIMARY KEY(user_id,day))')
    rows = c.run('SELECT day,n,micro FROM paid_ai_usage WHERE user_id=? AND day>=?',
                 (user['id'], time.strftime('%Y-%m-%d', time.gmtime(now - 366 * 86400))))
    daily = sum(r['n'] for r in rows if r['day'] == day)
    monthly = sum(r['n'] for r in rows if r['day'].startswith(month))
    annual = sum(r['micro'] for r in rows)
    c.run('CREATE TABLE IF NOT EXISTS play_regions (user_id TEXT PRIMARY KEY, region TEXT NOT NULL)')
    region_rows = c.run('SELECT region FROM play_regions WHERE user_id=?', (user['id'],))
    region = region_rows[0]['region'] if region_rows else 'IN'
    annual_budget = REGION_BUDGET_USD.get(region, ROLLING_YEAR_USD)
    feature = REQUEST_FEATURE.get()
    if feature not in FEATURE_LIMITS:
        feature = 'interview'
    c.run('CREATE TABLE IF NOT EXISTS paid_feature_usage (user_id TEXT NOT NULL, day TEXT NOT NULL, feature TEXT NOT NULL, n INTEGER NOT NULL, PRIMARY KEY(user_id,day,feature))')
    feature_rows = c.run('SELECT day,n FROM paid_feature_usage WHERE user_id=? AND feature=? AND day>=?', (user['id'], feature, month + '-01'))
    fd = sum(r['n'] for r in feature_rows if r['day'] == day)
    fm = sum(r['n'] for r in feature_rows)
    if fd >= FEATURE_LIMITS[feature][0] or fm >= FEATURE_LIMITS[feature][1]:
        raise spend.QuotaExceeded('This feature AI limit is reached; other remaining allowances and free practice are unchanged')
    if daily >= DAILY_CALLS or monthly >= MONTHLY_CALLS or annual + usd_micro > int(annual_budget * 1e6):
        raise spend.QuotaExceeded('Your plan AI fair-use limit is reached; free practice remains available')
    c.run('INSERT INTO paid_ai_usage(user_id,day,n,micro) VALUES(?,?,1,?) ON CONFLICT(user_id,day) DO UPDATE SET n=paid_ai_usage.n+1,micro=paid_ai_usage.micro+EXCLUDED.micro', (user['id'], day, usd_micro))
    c.run('INSERT INTO paid_feature_usage(user_id,day,feature,n) VALUES(?,?,?,1) ON CONFLICT(user_id,day,feature) DO UPDATE SET n=paid_feature_usage.n+1', (user['id'], day, feature))
    return user['id']


def plan_info(user=None):
    return {'enabled': enabled(), 'plan_id': 'pro_yearly', 'product_id': PRODUCT_ID,
            'proposed_price_inr': 499, 'proposed_price_usd': 49, 'allowed_regions': ['IN', 'US'],
            'regional_processing_allowance_usd': REGION_BUDGET_USD, 'feature_model_call_limits': FEATURE_LIMITS,
            'max_input_bytes': MAX_INPUT_BYTES, 'max_output_tokens': MAX_OUTPUT_TOKENS, 'duration': 'one year', 'renewal_type': 'prepaid_non_renewing',
            'active': paid_record(user) if user else False,
            'daily_model_calls': DAILY_CALLS, 'monthly_model_calls': MONTHLY_CALLS,
            'rolling_year_model_budget_usd': ROLLING_YEAR_USD,
            'purchase_available': bool(enabled() and os.environ.get('PLAY_SALES_READY') == '1' and os.environ.get('PLAY_RTDN_READY') == '1' and os.environ.get('PLAY_LICENSE_TESTS_PASSED') == '1' and os.environ.get('PLAY_POLICY_APPROVED') == '1' and os.environ.get('PLAY_PRICES_VERIFIED') == '1' and os.environ.get('PLAY_FUNDED_RESERVE_VERIFIED') == '1' and __import__('app.playbilling', fromlist=['configured']).configured())}


def feature_for(path):
    if '/recruiter/' in path: return 'recruiter'
    if '/negotiation' in path: return 'negotiation'
    if '/coding/' in path or path.endswith('/prep/coding'): return 'coding'
    if '/resume' in path or '/builder/' in path or path == '/api/match': return 'resume'
    if '/prep' in path or path in ('/api/star', '/api/company-brief'): return 'prep'
    return 'interview'


def prepare_purchase(user):
    """Permanent, conservative cohort holds. Canceled checkout does not free a slot
    automatically: the owner reconciles it against Play before reopening capacity.
    """
    from app import accounts
    if paid_record(user):
        raise ValueError('Your yearly plan is already active. Do not buy twice.')
    if not plan_info(user)['purchase_available']:
        raise ValueError('Sales are not enabled yet')
    with accounts.Conn() as c:
        c.run('CREATE TABLE IF NOT EXISTS launch_admission (user_id TEXT PRIMARY KEY, created DOUBLE PRECISION NOT NULL)')
        c.run('CREATE TABLE IF NOT EXISTS admission_gate (id INTEGER PRIMARY KEY, marker INTEGER NOT NULL)')
        c.run('INSERT INTO admission_gate(id,marker) VALUES(1,0) ON CONFLICT(id) DO NOTHING')
        if c.pg:
            c.run('SELECT id FROM admission_gate WHERE id=1 FOR UPDATE')
        else:
            c.c.commit()
            c.run('BEGIN IMMEDIATE')
        if c.run('SELECT user_id FROM launch_admission WHERE user_id=?', (user['id'],)):
            return {'ok': True}
        count = c.run('SELECT COUNT(*) AS n FROM launch_admission')[0]['n']
        if count >= min(2, max(0, int(os.environ.get('PLAY_LAUNCH_COHORT', '0')))):
            raise ValueError('The limited launch is full. No payment has started. Free practice remains available.')
        from app import spend
        spend._init(c)
        used = c.run('SELECT COALESCE(SUM(micro),0) AS n FROM spend')[0]['n'] / 1e6
        if used + (count + 1) * max(REGION_BUDGET_USD.values()) > spend.TOTAL_CAP:
            raise ValueError('Launch processing capacity is not funded. No payment has started.')
        c.run('INSERT INTO launch_admission(user_id,created) VALUES(?,?)', (user['id'], time.time()))
    return {'ok': True}
