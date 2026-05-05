from app.db.init_db import create_tables  # registers all models
from app.db.session import SessionLocal
from app.models.api_key import ApiKey
from app.models.user import User  # noqa - needed for relationship resolution
from app.models.audit_log import AuditLog  # noqa
from app.models.nonce import Nonce  # noqa
from app.core.security import verify_api_key

# PASTE YOUR RAW KEY HERE
RAW_KEY = "sv_live_04783d4cb980d6e700f7a2e2084841e96a9683a3"

print(f"Testing raw key: {RAW_KEY}")
print(f"Key length: {len(RAW_KEY)}")
print(f"First 8 chars (prefix we'll search for): '{RAW_KEY[:8]}'")
print()

db = SessionLocal()

# Show ALL active keys in DB
all_keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()
print(f"Found {len(all_keys)} active keys in DB:")
for k in all_keys:
    print(f"  - prefix='{k.prefix}' last_four='{k.last_four}' zone='{k.zone}' name='{k.name}'")
print()

# Search by prefix exactly like the verify endpoint does
candidates = db.query(ApiKey).filter(
    ApiKey.prefix == RAW_KEY[:8],
    ApiKey.is_active == True
).all()
print(f"Candidates matching prefix '{RAW_KEY[:8]}': {len(candidates)}")

if not candidates:
    print()
    print("THE ISSUE: No keys in DB match this prefix.")
    print("Stored prefixes vs searched prefix:")
    for k in all_keys:
        print(f"  stored='{k.prefix}' vs searched='{RAW_KEY[:8]}' match={k.prefix == RAW_KEY[:8]}")
else:
    for c in candidates:
        result = verify_api_key(RAW_KEY, c.key_hash)
        print(f"  Trying key '{c.name}': verify result = {result}")

db.close()