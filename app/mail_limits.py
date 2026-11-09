"""Persistent email flood protection; account security remains available for free.
Recipient addresses are hashed, not stored. Uncertain sends retain reservations.
"""
import hashlib
import os
import time


def reserve(recipient):
    enabled = os.environ.get('EMAIL_LIMITS_ENABLED', '1' if os.environ.get('DATABASE_URL') else '0') == '1'
    if not enabled:
        return
    from app import accounts
    now = time.time()
    day = time.strftime('%Y-%m-%d', time.gmtime(now))
    hour = time.strftime('%Y-%m-%dT%H', time.gmtime(now))
    key = hashlib.sha256(recipient.strip().lower().encode()).hexdigest()
    try:
        with accounts.Conn() as c:
            c.run('CREATE TABLE IF NOT EXISTS email_send_gate (id INTEGER PRIMARY KEY, n INTEGER NOT NULL)')
            c.run('INSERT INTO email_send_gate(id,n) VALUES(1,0) ON CONFLICT(id) DO NOTHING')
            c.run('CREATE TABLE IF NOT EXISTS email_send_counts (bucket TEXT PRIMARY KEY, n INTEGER NOT NULL)')
            if c.pg:
                c.run('SELECT id FROM email_send_gate WHERE id=1 FOR UPDATE')
            else:
                c.c.commit(); c.run('BEGIN IMMEDIATE')
            for bucket, cap in ((day+':all', 250), (day+':'+key, 6), (hour+':'+key, 3)):
                rows = c.run('SELECT n FROM email_send_counts WHERE bucket=?', (bucket,))
                if rows and rows[0]['n'] >= cap:
                    raise RuntimeError('Verification email limit reached; try again later')
            for bucket in (day+':all', day+':'+key, hour+':'+key):
                c.run('INSERT INTO email_send_counts(bucket,n) VALUES(?,1) ON CONFLICT(bucket) DO UPDATE SET n=email_send_counts.n+1', (bucket,))
            # UTC ISO prefix makes old counters safe to delete without retaining addresses.
            cutoff = time.strftime('%Y-%m-%d', time.gmtime(now - 3*86400))
            c.run('DELETE FROM email_send_counts WHERE bucket < ?', (cutoff,))
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError('Verification email limits are temporarily unavailable') from e
