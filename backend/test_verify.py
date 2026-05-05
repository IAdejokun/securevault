from app.core.security import generate_raw_key, hash_api_key, verify_api_key

# Generate a key just like your endpoint does
raw = generate_raw_key("sv_pub_")
print(f"Generated raw key: {raw}")
print(f"Length: {len(raw)} characters")

# Hash it
hashed = hash_api_key(raw)
print(f"Hash: {hashed}")

# Verify with the SAME raw key
result = verify_api_key(raw, hashed)
print(f"Verify with same key: {result}")

# Verify with a different key
result2 = verify_api_key("sv_pub_wrongkey1234567890", hashed)
print(f"Verify with wrong key: {result2}")