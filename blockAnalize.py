from PIL import Image
from collections import defaultdict


origin = Image.open("clue.png").convert("RGBA")
w, h = origin.size
print(w,h)
raw = origin.tobytes()


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


def read_png_header(path):
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Not a PNG")

        # IHDR
        length = int.from_bytes(f.read(4), "big")
        ctype  = f.read(4)
        if ctype != b"IHDR" or length != 13:
            raise ValueError("Malformed PNG: missing IHDR")

        data = f.read(13)
        _crc = f.read(4)  # skip CRC

    width  = int.from_bytes(data[0:4], "big")
    height = int.from_bytes(data[4:8], "big")
    bit_depth   = data[8]
    color_type  = data[9]   # 0,2,3,4,6
    compression = data[10]  # 일반적으로 0
    filter_m    = data[11]  # 0
    interlace   = data[12]  # 0(없음) or 1(Adam7)

    color_map = {
        0: "Grayscale",
        2: "Truecolor RGB",
        3: "Indexed (Palette)",
        4: "Grayscale + Alpha",
        6: "Truecolor RGBA",
    }
    interlace_name = "Adam7" if interlace == 1 else "None"

    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,       # 1/2/4/8/16 (컬러 타입에 따라 허용치 다름)
        "color_type": color_type,     # 0/2/3/4/6
        "color_name": color_map.get(color_type, f"Unknown({color_type})"),
        "interlace": interlace_name,
        "compression": compression,
        "filter": filter_m,
    }

info = read_png_header("clue.png")
print(info)


GenerateBlocks(0, 16)