#!/usr/bin/env python3
"""PNG to SVG converter for pixel art."""

from __future__ import annotations
import argparse
import sys
import os
from typing import Optional, Tuple, Dict, List
from PIL import Image


def find_first_nontransparent_pixel(path: str, *, alpha_min_value: int = 1) -> Optional[Tuple[int, int]]:
    """Return (x, y) of the first non-transparent pixel scanning row-major, or None if none.

    Non-transparent is defined as alpha >= alpha_min_value (0..255).
    """
    with Image.open(path) as im:
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        w, h = im.size
        alpha = im.getchannel("A")
        px = alpha.load()
        for y in range(h):
            for x in range(w):
                if px[x, y] >= alpha_min_value:
                    return (x, y)
    return None


def find_last_nontransparent_pixel(path: str, *, alpha_min_value: int = 1) -> Optional[Tuple[int, int]]:
    """Return (x, y) of the last non-transparent pixel scanning in reverse row-major order, or None if none.

    Non-transparent is defined as alpha >= alpha_min_value (0..255).
    Scans from bottom-right to top-left.
    """
    with Image.open(path) as im:
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        w, h = im.size
        alpha = im.getchannel("A")
        px = alpha.load()
        for y in range(h - 1, -1, -1):
            for x in range(w - 1, -1, -1):
                if px[x, y] >= alpha_min_value:
                    return (x, y)
    return None


def find_leftmost_nontransparent_pixel(path: str, alpha_min_value: int = 128) -> Optional[Tuple[int, int]]:
    """Return (x, y) of the leftmost non-transparent pixel scanning column by column from left, or None if none.

    Non-transparent is defined as alpha >= alpha_min_value (0..255).
    Default is 128 (50% opacity) for 1024x1024 images.
    Scans from left to right, top to bottom within each column.
    """
    with Image.open(path) as im:
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        w, h = im.size
        alpha = im.getchannel("A")
        px = alpha.load()
        for x in range(w):
            for y in range(h):
                if px[x, y] >= alpha_min_value:
                    return (x, y)
    return None


def find_rightmost_nontransparent_pixel(path: str, alpha_min_value: int = 128) -> Optional[Tuple[int, int]]:
    """Return (x, y) of the rightmost non-transparent pixel scanning column by column from right, or None if none.

    """
    with Image.open(path) as im:
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        w, h = im.size
        alpha = im.getchannel("A")
        px = alpha.load()
        for x in range(w - 1, -1, -1):
            for y in range(h):
                if px[x, y] >= alpha_min_value:
                    return (x, y)
    return None


def scan_row_blocks(img_path: str, start_y: int, block_size: int, alpha_min_value: int,
                    previous_row_y: Optional[int] = None) -> Optional[Dict]:
    """Scan a horizontal row of blocks starting from the first non-transparent pixel at start_y.

    For pseudo-pixel art, we search for the actual topmost pixel in the row range
    without restricting to block boundaries, allowing proper handling of overlapping/anti-aliased pixels.

    Args:
        img_path: Path to the image file
        start_y: Y coordinate to start searching for the first non-transparent pixel
        block_size: Size of each block (NxN)
        alpha_min_value: Minimum alpha value to consider non-transparent (0-255)
        previous_row_y: Y coordinate of previous row (for reference)

    Returns:
        Dictionary with row data, or None if no non-transparent pixel found at start_y
    """
    def _to_hex(val: int) -> str:
        return f"{val:02X}"

    try:
        with Image.open(img_path) as im_row:
            if im_row.mode != "RGBA":
                im_row = im_row.convert("RGBA")
            wR, hR = im_row.size
            pixR = im_row.load()

            # Find first non-transparent pixel by scanning the full row range
            # Start from leftmost pixel (x=0) and search for topmost visible pixel
            # This properly handles pseudo-pixel art with anti-aliasing/overlapping
            first_x = None
            actual_start_y = start_y
            search_range = min(block_size, hR - start_y)

            # STEP 1: Find the topmost Y coordinate that has any visible pixel
            topmost_y = None
            for dy in range(search_range):
                check_y = start_y + dy
                for x_check in range(wR):
                    if pixR[x_check, check_y][3] >= alpha_min_value:
                        topmost_y = check_y
                        break
                if topmost_y is not None:
                    break

            if topmost_y is None:
                return None

            # STEP 2: Find the leftmost X coordinate at that topmost Y
            for x_search in range(wR):
                if pixR[x_search, topmost_y][3] >= alpha_min_value:
                    first_x = x_search
                    actual_start_y = topmost_y
                    break

            if first_x is None:
                return None

            row_blocks = []
            last_pixel = None
            bi = 0

            # Start the first block at the actual first pixel coordinates
            # This ensures blocks align with real content, not arbitrary grid positions
            start_block_x = first_x
            start_block_y = actual_start_y

            # Scan horizontally, creating blocks starting from the first pixel
            while True:
                origin_x = start_block_x + bi * block_size
                origin_y = actual_start_y  # Use the actual Y where we found content
                if origin_x >= wR:
                    break

                # Collect block pixels
                blk_pixels = []
                blk_color_counts = {}
                visible = 0
                skipped = 0
                actual_w = 0
                actual_h = 0

                for dy in range(block_size):
                    sy = origin_y + dy
                    if sy >= hR:
                        break
                    row_present = False
                    for dx in range(block_size):
                        sx = origin_x + dx
                        if sx >= wR:
                            break
                        rC, gC, bC, aC = pixR[sx, sy]
                        opC = round(aC / 255 * 100, 2)
                        entry = {"x": sx, "y": sy, "r": rC, "g": gC, "b": bC, "a": aC, "opacity_percent": opC}
                        blk_pixels.append(entry)
                        if aC >= alpha_min_value:
                            hxC = f"#{_to_hex(rC)}{_to_hex(gC)}{_to_hex(bC)}{_to_hex(aC)}"
                            blk_color_counts[hxC] = blk_color_counts.get(hxC, 0) + 1
                            visible += 1
                        else:
                            skipped += 1
                        last_pixel = (sx, sy)
                        actual_w = max(actual_w, dx + 1)
                        row_present = True
                    if row_present:
                        actual_h += 1

                # Build color coords
                blk_color_coords: Dict[str, List[Tuple[int, int]]] = {}
                for pC in blk_pixels:
                    if pC['a'] >= alpha_min_value:
                        hxC2 = f"#{_to_hex(pC['r'])}{_to_hex(pC['g'])}{_to_hex(pC['b'])}{_to_hex(pC['a'])}"
                        blk_color_coords.setdefault(hxC2, []).append((pC['x'], pC['y']))

                blk_counts_list = [
                    {
                        "rgba_hex": k,
                        "rgb_hex": k[:7],
                        "a": int(k[-2:], 16),
                        "count": v,
                        "coords": blk_color_coords.get(k, []),
                    }
                    for k, v in sorted(blk_color_counts.items(), key=lambda kv: (-kv[1], kv[0]))
                ]

                # Only include blocks that have at least some visible pixels
                # Don't stop scanning - continue across entire width
                if visible > 0:
                    row_blocks.append({
                        "index": bi,
                        "origin": {"x": origin_x, "y": origin_y},
                        "actual_size": {"w": actual_w, "h": actual_h},
                        "visible_pixels": visible,
                        "skipped_pixels": skipped,
                        "unique_colors": len(blk_counts_list),
                        "color_counts": blk_counts_list,
                    })

                # Always advance to next block (continue scanning entire width)
                bi += 1

            if not row_blocks:
                return None

            # Filter out trailing sparse blocks (anti-aliasing artifacts at the end)
            # Remove blocks from the end that have <50% visible pixels
            while row_blocks:
                last_block = row_blocks[-1]
                total_pixels_in_block = block_size * block_size
                visibility_percent = last_block["visible_pixels"] / total_pixels_in_block
                if visibility_percent < 0.5:
                    row_blocks.pop()
                else:
                    break

            if not row_blocks:
                return None

            # Report the ACTUAL first visible pixel found during scan (lines 165-166)
            # This is the true first non-transparent pixel in this row range,
            # NOT the block-aligned grid coordinate
            # first_x and actual_start_y contain the real pixel coordinates

            # Report the last substantial block's last pixel
            last_block = row_blocks[-1]
            last_block_x = last_block["origin"]["x"] + block_size - 1
            last_block_y = last_block["origin"]["y"] + block_size - 1

            return {
                "block_size": block_size,
                "blocks": row_blocks,
                "total_blocks": len(row_blocks),
                "first_pixel": {"x": first_x, "y": actual_start_y},  # Report ACTUAL pixel found, not block origin
                "last_pixel_visited": (last_block_x, last_block_y),  # Report where substantial content ends
            }
    except Exception as e:
        return None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PNG to SVG pixel art converter")
    
    # Minimal args
    parser.add_argument("--image", "-i", required=True)
    parser.add_argument("--block-size", type=int, default=16)
    parser.add_argument("--emit-all-rows", action="store_true", required=True)
    parser.add_argument("--svg-out", type=str, required=True)
    parser.add_argument("--quiet", "-q", action="store_true")
    
    args = parser.parse_args(argv)
    
    # Validate file
    if not os.path.isfile(args.image):
        print(f"ERROR: File not found: {args.image}", file=sys.stderr)
        return 3
    
    # Hardcoded threshold (50% opacity)
    alpha_min_value = 128
    
    # Find first pixel
    try:
        coord = find_first_nontransparent_pixel(args.image, alpha_min_value=alpha_min_value)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    
    if coord is None:
        print("ERROR: No visible pixels found", file=sys.stderr)
        return 2
    
    x, y = coord
    
    # Find boundaries
    try:
        last_coord = find_last_nontransparent_pixel(args.image, alpha_min_value=alpha_min_value)
        leftmost_coord = find_leftmost_nontransparent_pixel(args.image, alpha_min_value=alpha_min_value)
        rightmost_coord = find_rightmost_nontransparent_pixel(args.image, alpha_min_value=alpha_min_value)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    
    if not last_coord:
        print("ERROR: Could not find image boundaries", file=sys.stderr)
        return 2
    
    # Scan all rows
    all_rows = []
    last_y = last_coord[1]
    current_y = y
    row_number = 1
    
    while current_y <= last_y:
        row_data = scan_row_blocks(args.image, current_y, args.block_size, alpha_min_value, None)
        if row_data:
            row_data["name"] = f"Row{row_number}"
            all_rows.append(row_data)
            row_number += 1
        current_y += args.block_size
    
    if not all_rows:
        print("ERROR: No rows detected", file=sys.stderr)
        return 2
    
    # Generate SVG
    left_ref = leftmost_coord[0] if leftmost_coord else all_rows[0]["blocks"][0]["origin"]["x"]
    top_ref = all_rows[0]["blocks"][0]["origin"]["y"]
    rects = []
    
    for row_idx, row in enumerate(all_rows, start=1):
        for block_idx, rb in enumerate(row["blocks"]):
            if not rb.get("color_counts"):
                continue
            
            top_color = rb["color_counts"][0]
            rgb_hex = top_color["rgb_hex"]
            a_val = top_color["a"]
            fill_opacity = round(a_val / 255.0, 4)
            
            img_x = rb["origin"]["x"]
            img_y = rb["origin"]["y"]
            rect_x = (img_x - left_ref) // args.block_size
            rect_y = (img_y - top_ref) // args.block_size
            
            rects.append(f'  <rect x="{rect_x}" y="{rect_y}" width="1" height="1" '
                        f'fill="{rgb_hex}" fill-opacity="{fill_opacity}" />')
    
    # Calculate canvas size
    right_ref = rightmost_coord[0]
    last_y_coord = last_coord[1]
    canvas_w = int((right_ref - left_ref) / args.block_size) + 1
    canvas_h = int((last_y_coord - top_ref) / args.block_size) + 1
    
    # Write SVG
    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" '
        f'width="{canvas_w}" height="{canvas_h}" style="shape-rendering:crispEdges;">\n'
        + '\n'.join(rects) +
        '\n</svg>'
    )
    
    try:
        with open(args.svg_out, "w", encoding="utf-8") as f:
            f.write(svg_content)
    except Exception as e:
        print(f"ERROR: Failed to write SVG: {e}", file=sys.stderr)
        return 3
    
    if not args.quiet:
        print(f"  SVG written: {args.svg_out}")
        print(f"  Canvas: {canvas_w}×{canvas_h}")
        print(f"  Rows: {len(all_rows)}")
        print(f"  Blocks: {len(rects)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
