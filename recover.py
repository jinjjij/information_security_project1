from enc import (_to_bytes)
from Crypto.Cipher import AES

block_size = 16
Pstring = "This is a top secret message. Do not share it with anyone!"
Cstring = "3e40001d1bc6d179551288606d9404914c002383a158dbc45748957a845b3195eaf9ac3f1e34dc2ef8888c70399ec0acbed366b8e1fcc8b501f5763fe91862a3"

P = Pstring.encode()
C = _to_bytes(Cstring)

P_block = P[:16]
C_block = C[:16]

K1 = _to_bytes("a3f19c8d4e6b72f0e2377ecff7")
K2 = _to_bytes("5e8b41c2d9f07a36e2377ecff7")


MCandidate = {}
finalCandidate = []

K_space = 1 << 24

for i in range(K_space):
    if(i%1000000 == 0):
        print(i)
    K1_right3 = i.to_bytes(3, 'big')
    cipher1 = AES.new(K1+K1_right3, AES.MODE_ECB)
    middle = cipher1.encrypt(P_block)
    MCandidate[middle] = K1_right3

for i in range(K_space):
    if(i%1000000 == 0):
        print(i)
    K2_right3 = i.to_bytes(3, 'big')
    cipher2 = AES.new(K2+K2_right3, AES.MODE_ECB)
    middle = cipher2.decrypt(C_block)
    if middle in MCandidate:
        finalCandidate.append((MCandidate[middle], K2_right3))

if not finalCandidate:
    print("no candidates")
else:
    k1_suffix = finalCandidate[0][0]   # bytes(3)
    k2_suffix = finalCandidate[0][1]   # bytes(3)
    print(f"k1 : {k1_suffix.hex()}  k2 : {k2_suffix.hex()}")
