from enc import (_to_bytes, split_256bit_key)
from Crypto.Util.Padding import unpad
from Crypto.Cipher import AES

Cstring = "f0f1f84d807d9bfdf416a18ac5ab9c3b1a7a06e7b69e020d435ac230c6f1695e50dc5a139d217332f270363bdccffe1b"
key256 = "a3f19c8d4e6b72f0e2377ecff747b2cd5e8b41c2d9f07a36e2377ecff78e725f"

def decrypt(
    ciphertext: bytes | str,
    key256: bytes | str = None, 
    block_size: int = 16,
) -> bytes:
    C = _to_bytes(ciphertext)

    if key256 is not None:
        k1_b, k2_b = split_256bit_key(key256)
    else:
        return -1
    
    cipher1 = AES.new(k1_b, AES.MODE_ECB)
    cipher2 = AES.new(k2_b, AES.MODE_ECB)

    P2 = cipher2.decrypt(C)
    P1 = cipher1.decrypt(P2)
    P = unpad(P1, block_size)
    return P

print(decrypt(Cstring, key256).decode("utf-8"))