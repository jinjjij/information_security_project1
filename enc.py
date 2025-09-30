# pip install pycryptodome
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from typing import Tuple


def _to_bytes(x: bytes | str) -> bytes:
    if isinstance(x, bytes):
        return x
    x = x.strip().lower()
    # Allow '0x' prefix
    if x.startswith("0x"):
        x = x[2:]
    return bytes.fromhex(x)


def split_256bit_key(key256: bytes | str) -> Tuple[bytes, bytes]:
    b = _to_bytes(key256)
    if len(b) != 32:
        raise ValueError("key256 must be exactly 32 bytes (256 bits).")
    return b[:16], b[16:]


def encrypt(
    plaintext: bytes | str,
    key256: bytes | str = None, 
    use_pkcs7: bool = True,
    block_size: int = 16,
) -> bytes:
    P = _to_bytes(plaintext)

    if key256 is not None:
        k1_b, k2_b = split_256bit_key(key256)
    else:
        if k1 is None or k2 is None:
            raise ValueError("Provide either (k1 and k2) or a single key256.")
        k1_b, k2_b = _to_bytes(k1), _to_bytes(k2)

    if len(k1_b) != 16 or len(k2_b) != 16:
        raise ValueError("k1 and k2 must each be 16 bytes (128 bits).")

    cipher1 = AES.new(k1_b, AES.MODE_ECB)
    cipher2 = AES.new(k2_b, AES.MODE_ECB)
    data = (
        pad(P, block_size)
        if use_pkcs7
        else (
            P
            if len(P) % block_size == 0
            else (_ for _ in ()).throw(
                ValueError("Plaintext not multiple of 16 and padding disabled")
            )
        )
    )
    C1 = cipher1.encrypt(data)
    C2 = cipher2.encrypt(C1)
    return C2
