from app.core.security import (
    hash_password,
    verify_password,
    generate_raw_key,
    hash_api_key,
    verify_api_key,
    extract_key_parts,
    create_access_token,
    decode_token,
    generate_nonce,
    nonce_expires_at,
)

# Password
h = hash_password('mysecret')
assert verify_password('mysecret', h)
assert not verify_password('wrong', h)
print('Password hashing: OK')

# API key
raw = generate_raw_key()
hashed = hash_api_key(raw)
assert verify_api_key(raw, hashed)
prefix, last_four = extract_key_parts(raw)
assert prefix == 'sv_live_'
assert last_four == raw[-4:]
print(f'API key generation: OK  ({raw[:16]}...{last_four})')

# JWT
token = create_access_token('some-user-uuid')
payload = decode_token(token)
assert payload['sub'] == 'some-user-uuid'
assert payload['type'] == 'access'
print(f'JWT: OK  (jti={payload["jti"][:8]}...)')

# Nonce
nonce = generate_nonce()
assert len(nonce) == 36
print(f'Nonce: OK  ({nonce})')

print()
print('Sprint 2: ALL CHECKS PASSED')