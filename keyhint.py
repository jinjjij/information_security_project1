# finding the keyhint
# from clue.png
# AES-ECB는 128bit, 또는 16 byte 를 블록으로 작동한다.
# 또, 특징상 같은 블록이 input 되면 같은 형태의 output 이 나오기 때문에, 
# clue.png 의 alpha 값은 항상 ff -> 암호화는 RGB대상으로 진행되었음.

from PIL import Image
from collections import defaultdict
from hashlib import blake2b


origin = Image.open("clue.png").convert("RGBA")
w, h = origin.size
print(w,h)
#cropped = origin.crop((0,0,w-2, h))
#w -= 2
raw = origin.tobytes()


def make_color_from_block(b):
    h = blake2b(b, digest_size=3).digest()
    return (h[0], h[1], h[2], 255)

color_map = defaultdict(lambda: None)

# 색 맵 초기화
blk = b'\x01\x02...'
color = color_map.setdefault(blk, make_color_from_block(blk))


def GenerateBlocks(offset, step):

    blockCount = 0
    groups = defaultdict(list)

    for i in range(offset, len(raw), step):
        block = raw[i:i+step]
        groups[block].append(i)
        blockCount += 1


    max_len = len(max(groups.values(), key=len, default=[]))
    sorted_items = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)

    print(len(groups),"/",blockCount)
    print(max_len)
    
    return sorted_items


def generatePixels(step, sorted_blocks, K, mod):
    out_pixels = bytearray(b'\x00\x00\x00\xff' * (w * h))

    # 상위 topK 개의 블록만을 사용
    if mod == "topK":
        for k in range(K):
            block = sorted_blocks[k]

            for pos in block[1]:
                for i in range(0, step, 4):

                    if color_map[block[0]] is None:
                        color_map[block[0]] = make_color_from_block(block[0])
                    out_pixels[pos+i : pos+i+4] = color_map[block[0]]    
        

    elif mod == "threshold":
        plotted_block = 0
        for block in sorted_blocks:
            if len(block[1]) >= K:
                continue
            plotted_block += 1
            for pos in block[1]:
                for i in range(0, step, 4):
                    if color_map[block[0]] is None:
                        color_map[block[0]] = make_color_from_block(block[0])
                    out_pixels[pos+i : pos+i+4] = color_map[block[0]]
        print(plotted_block)

    return out_pixels


# 2픽셀씩 밀려서 오른쪽 두 픽셀 무시.
# 짝수번째 줄만 사용해서 만드는 이미지.
def adjustRow(out_pixels):
    src = memoryview(out_pixels)         # bytes/bytearray 모두 OK
    dst = bytearray(w * h * 4)

    for r in range(h):
        # 홀수 행은 위의 짝수 행을 참조
        src_r = r if (r % 2 == 0) else (r - 1)
        for c in range(w - 2):           # 오른쪽 두 컬럼 무시
            si = (src_r * w + c) * 4     # source index (RGBA)
            di = (r * w + c) * 4         # dest index (RGBA)
            dst[di:di+4] = src[si:si+4]

    return dst


def main():
    step = 16
    blocklist = GenerateBlocks(0, step)
    pixels = generatePixels(step, blocklist, 450, "topK")
    
    out_img = Image.frombytes("RGBA", (w, h), bytes(pixels))
    out_img.save("processed.png")

if __name__ == "__main__":
    main()