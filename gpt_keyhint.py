#!/usr/bin/env python3
"""
extract_boundaries_from_clue.py

Usage:
    python extract_boundaries_from_clue.py clue.png --outdir out

Requirements:
    pip install pillow numpy
"""
import argparse
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageDraw
import numpy as np
import hashlib
import sys

BLOCK_BYTES = 16  # AES block size
PIXELS_PER_BLOCK = 4  # RGBA -> 4 bytes/pixel -> 16 bytes = 4 pixels

def vis_xor_adj_raw_to_image(raw_bytes, w, h, channels=4, block_size=BLOCK_BYTES):
    """
    Build an RGB image where each block's color = XOR(prev_block, block) first 3 bytes.
    Returns a PIL.Image (RGB).
    """
    blocks = [ raw_bytes[i:i+block_size] for i in range(0, len(raw_bytes), block_size) ]
    out_buf = bytearray(w * h * 3)
    prev = None
    def block_xor_color(a, b):
        la = len(a); lb = len(b)
        L = max(la, lb)
        res0 = 0
        res1 = 0
        res2 = 0
        # compute first 3 bytes of XOR (or fallback)
        for i in range(3):
            ai = a[i] if i < la else 0
            bi = b[i] if i < lb else 0
            xr = ai ^ bi
            if i == 0: res0 = xr
            elif i == 1: res1 = xr
            else: res2 = xr
        return (res0, res1, res2)
    total_pixels = w * h
    for bi, blk in enumerate(blocks):
        start_byte = bi * block_size
        end_byte = min(start_byte + block_size, len(raw_bytes))
        start_pixel = start_byte // channels
        end_pixel = (end_byte + channels - 1) // channels
        if bi == 0:
            color = (0,0,0)
        else:
            color = block_xor_color(prev, blk)
        prev = blk
        for p in range(start_pixel, end_pixel):
            if p >= total_pixels:
                break
            off = p * 3
            out_buf[off:off+3] = bytes(color)
    return Image.frombytes("RGB", (w, h), bytes(out_buf))

def enhance_and_threshold(img_rgb, median_size=3, thresh=18):
    """
    Convert to grayscale, median filter, compute horizontal diff and threshold.
    Returns binary numpy array (0/255).
    """
    gray = img_rgb.convert("L")
    # median filter to reduce 1-pixel vertical flicker noise
    if median_size and median_size > 1:
        gray = gray.filter(ImageFilter.MedianFilter(size=median_size))
    arr = np.array(gray, dtype=np.int16)
    # horizontal absolute difference
    diff = np.abs(np.diff(arr, axis=1))
    diff = np.pad(diff, ((0,0),(1,0)), mode='constant', constant_values=0)
    # threshold
    mask = (diff >= thresh).astype(np.uint8) * 255
    return mask

def morph_close_pil(mask_arr, kernel_size=3):
    """
    Do morphological closing (dilation then erosion) using PIL MaxFilter/MinFilter.
    mask_arr: numpy uint8 (0/255)
    kernel_size: odd >=3 (PIL MaxFilter uses size)
    Returns numpy uint8 (0/255).
    """
    im = Image.fromarray(mask_arr)
    # MaxFilter/MinFilter sizes are odd integers; they are morphological dilation/erosion-ish
    im_d = im.filter(ImageFilter.MaxFilter(size=kernel_size))
    im_c = im_d.filter(ImageFilter.MinFilter(size=kernel_size))
    return np.array(im_c, dtype=np.uint8)

def find_significant_columns(mask_arr, min_fraction=0.12, expand=1):
    """
    Compute column sums and return list of column indices whose summed edge pixels
    exceed min_fraction * max_sum.
    Optionally expand each found column by 'expand' pixels on both sides.
    """
    col_sum = mask_arr.sum(axis=0)  # sum of 0/255 values
    if col_sum.size == 0:
        return []
    max_s = col_sum.max()
    if max_s == 0:
        return []
    threshold = max_s * min_fraction
    cols = np.where(col_sum >= threshold)[0].tolist()
    # expand and unique-sort
    cols_exp = set()
    for c in cols:
        for x in range(c-expand, c+expand+1):
            if 0 <= x < mask_arr.shape[1]:
                cols_exp.add(x)
    return sorted(cols_exp)

def overlay_columns_on_image(img_path, cols, out_path, line_color=(255,0,0), width=2):
    img = Image.open(img_path).convert("RGBA")
    draw = ImageDraw.Draw(img, 'RGBA')
    w,h = img.size
    for c in cols:
        x0 = max(0, c - width//2)
        x1 = min(w-1, c + width//2)
        # draw translucent red line (or solid)
        draw.rectangle([ (x0,0), (x1,h-1) ], fill=(line_color[0], line_color[1], line_color[2], 200))
    img.save(out_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="input image (clue.png)")
    ap.add_argument("--outdir", default="ecb_edges_out", help="output folder")
    ap.add_argument("--median", type=int, default=5, help="median filter size (odd int)")
    ap.add_argument("--thresh", type=int, default=18, help="horizontal diff threshold")
    ap.add_argument("--morph", type=int, default=5, help="morph close kernel size (odd)")
    ap.add_argument("--colfrac", type=float, default=0.12, help="column selection fraction of max")
    ap.add_argument("--expand", type=int, default=1, help="expand columns by this many px")
    args = ap.parse_args()

    inp = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # load RGBA raw bytes
    img = Image.open(inp).convert("RGBA")
    w,h = img.size
    raw = img.tobytes()
    channels = 4
    print("loaded:", inp, "size:", w, h, "bytes:", len(raw))

    # 1) vis_xor_adj visualization
    vis = vis_xor_adj_raw_to_image(raw, w, h, channels=channels, block_size=BLOCK_BYTES)
    vis_path = outdir / "vis_xor_adj.png"
    vis.save(vis_path)
    print("saved XOR visualization:", vis_path)

    # 2) make mask from visualization
    mask = enhance_and_threshold(vis, median_size=args.median, thresh=args.thresh)
    mask_path = outdir / "mask_edges_raw.png"
    Image.fromarray(mask).save(mask_path)
    print("saved raw mask:", mask_path)

    # 3) morph close
    mask_closed = morph_close_pil(mask, kernel_size=args.morph)
    mask_closed_path = outdir / "mask_edges_closed.png"
    Image.fromarray(mask_closed).save(mask_closed_path)
    print("saved closed mask:", mask_closed_path)

    # 4) find significant columns
    cols = find_significant_columns(mask_closed, min_fraction=args.colfrac, expand=args.expand)
    print("found columns:", cols)
    # save columns
    cols_path = outdir / "columns.txt"
    cols_path.write_text("\n".join(str(c) for c in cols))
    print("saved column list:", cols_path)

    # 5) overlay on original
    overlay_path = outdir / "overlay_lines.png"
    overlay_columns_on_image(inp, cols, overlay_path, width=3)
    print("saved overlay:", overlay_path)

    # 6) optional: save a visualization that highlights mask on vis image
    vis_masked = Image.open(vis_path).convert("RGBA")
    mask_img = Image.fromarray(mask_closed)
    mask_rgb = ImageOps.colorize(Image.fromarray(mask_closed), black="black", white="yellow").convert("RGBA")
    vis_masked.paste(mask_rgb, (0,0), mask_img)
    vis_masked.save(outdir / "vis_with_mask_overlay.png")
    print("saved vis_with_mask_overlay.png")

if __name__ == "__main__":
    main()
