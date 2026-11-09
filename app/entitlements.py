"""Server-verified paid AI, with free practice and data rights preserved."""

PLANS = {
    "pro_yearly": {"campaigns": 100, "invites_per_campaign": 200, "resumes_per_run": 100, "team_members": 10, "api": True},
    "free": {"campaigns": 100, "invites_per_campaign": 200, "resumes_per_run": 100, "team_members": 10, "api": True},
    # "pro": {...}  later: raise the numbers, nothing else needs to change.
}


def limit(user: dict, key: str):
    return PLANS.get((user or {}).get("plan") or "free", PLANS["free"]).get(key)


def role_of(user) -> str:
    return (user or {}).get("role") or "guest"


# ---------- inert monetization seams (no paid plans, no ads; Ranjit decides the split later) ----------
ENT_SCHEMA_VERSION = 1
ENT_STATES = {"free", "active", "grace", "hold", "expired", "revoked"}
ENT_SOURCES = {"none", "play", "web", "manual"}
ENT_DEFAULT = {"plan_id": "free", "state": "free", "expiry_at": None, "source": "none",
               "last_verified_at": None, "schema_version": ENT_SCHEMA_VERSION}
# Never gated by plan state or flags, in any state including expired/revoked:
_ALWAYS = {"privacy", "data_export", "account_deletion", "security", "reporting"}
ADS = {"enabled": False}  # ad container seam: renders nothing; not remotely settable today


def record_for(user):
    """Entitlement record for a user. Missing row, unknown plan/state/source, forward schema
    version, or any storage error all read as the free default - never a lockout, never raises."""
    ent = dict(ENT_DEFAULT)
    try:
        uid = (user or {}).get("id")
        if not uid:
            return ent
        from app import accounts
        with accounts.Conn() as c:
            rows = c.run("SELECT plan_id, state, expiry_at, source, last_verified_at, schema_version "
                         "FROM entitlements WHERE user_id=?", (uid,))
        if not rows:
            return ent
        r = rows[0]
        if (r.get("plan_id") not in PLANS or r.get("state") not in ENT_STATES
                or r.get("source") not in ENT_SOURCES or r.get("schema_version") != ENT_SCHEMA_VERSION):
            return ent
        if r.get("plan_id") in PLANS:
            ent["plan_id"] = r["plan_id"]
        if r.get("state") in ENT_STATES:
            ent["state"] = r["state"]
        if r.get("source") in ENT_SOURCES:
            ent["source"] = r["source"]
        if isinstance(r.get("schema_version"), int) and 1 <= r["schema_version"] <= ENT_SCHEMA_VERSION:
            ent["schema_version"] = r["schema_version"]
        ent["expiry_at"] = r.get("expiry_at")
        ent["last_verified_at"] = r.get("last_verified_at")
    except Exception:
        return dict(ENT_DEFAULT)
    return ent


def allowed(user, feature: str) -> bool:
    """Plan-to-feature reader. Unknown plan ids or features fall back to the free set,
    never to a lockout. Privacy, export, deletion, security and reporting are always allowed."""
    if feature in _ALWAYS:
        return True
    from app import monetization
    if feature in {'question_bank', 'resume_builder', 'org_hub'}:
        return True
    ai_features = {'interview', 'negotiation', 'resume_review', 'jd_match', 'prep',
                   'star', 'brief', 'coding', 'recruiter_screen'}
    return feature in ai_features and monetization.paid_record(user)
