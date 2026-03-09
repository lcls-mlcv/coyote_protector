# Stand-alone LabelMe -> COCO converter (polygons + rectangles + circles)
# No external dependencies beyond Python stdlib.

import os, json, glob, math, sys
from pathlib import Path

# ======== EDIT THESE PATHS ========
LABELME_DIR = r"path/to/labelme_json_files" #can be on local device
OUT_JSON    = r"path/to/output/dataset.json" #can be on local deivice
# Root prefix for COCO "file_name" entries:
ROOT_PREFIX = "path/to/coyote_image_folder_prefix" #on sdf
# ==================================

def polygon_area(points):
    # points: [(x,y), ...]
    area = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i+1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5

def poly_bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_min, y_min = min(xs), min(ys)
    x_max, y_max = max(xs), max(ys)
    return [float(x_min), float(y_min), float(x_max - x_min), float(y_max - y_min)]

def rect_to_polygon(p1, p2):
    # LabelMe rectangle stores two corner points (x1,y1),(x2,y2)
    x1, y1 = p1
    x2, y2 = p2
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

def circle_to_polygon(center, edge, nverts=32):
    cx, cy = center
    ex, ey = edge
    r = math.hypot(ex - cx, ey - cy)
    pts = []
    for k in range(nverts):
        th = 2 * math.pi * k / nverts
        pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    return pts

def to_segmentation(points):
    # COCO expects [x1,y1,x2,y2,...] inside a list
    flat = []
    for x, y in points:
        flat.extend([float(x), float(y)])
    return [flat]

def main():
    in_dir = Path(LABELME_DIR)
    if not in_dir.is_dir():
        print(f"[ERROR] Input folder not found: {LABELME_DIR}", file=sys.stderr)
        sys.exit(1)

    json_paths = sorted(glob.glob(str(in_dir / "*.json")))
    print(f"[INFO] Found {len(json_paths)} LabelMe JSON files in: {LABELME_DIR}")
    if not json_paths:
        sys.exit(1)

    images = []
    annotations = []
    categories = []
    cat_name_to_id = {}
    next_image_id = 1
    next_anno_id = 1
    next_cat_id = 1

    for jp in json_paths:
        with open(jp, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Basic fields in LabelMe JSON
        img_w = int(data.get("imageWidth", 0))
        img_h = int(data.get("imageHeight", 0))
        img_path = data.get("imagePath") or os.path.splitext(os.path.basename(jp))[0]

        # Build desired absolute path: /sdf/.../<basename[.ext]>
        base_name = os.path.basename(img_path)
        name, ext = os.path.splitext(base_name)
        if not ext:
            # Default to .jpg if LabelMe did not store an extension
            base_name = name + ".jpg"
        file_path = f"{ROOT_PREFIX}/{base_name}"

        if img_w == 0 or img_h == 0:
            # Some LabelMe JSONs miss width/height; left as 0 (some tools may complain)
            print(f"[WARN] {jp} has no imageWidth/Height; values are 0.", file=sys.stderr)

        images.append({
            "id": next_image_id,
            "file_name": file_path,  # << absolute path as requested
            "width": img_w,
            "height": img_h
        })

        for shape in data.get("shapes", []):
            label = shape.get("label", "unknown")
            stype = shape.get("shape_type", "polygon")
            pts = shape.get("points", [])

            # Map/ensure category id
            if label not in cat_name_to_id:
                cat_name_to_id[label] = next_cat_id
                categories.append({
                    "id": next_cat_id,
                    "name": label,
                    "supercategory": "none"
                })
                next_cat_id += 1
            cat_id = cat_name_to_id[label]

            # Build polygon points depending on shape_type
            poly_pts = None
            if stype == "polygon" and len(pts) >= 3:
                poly_pts = [(float(x), float(y)) for x, y in pts]
            elif stype == "rectangle" and len(pts) == 2:
                poly_pts = rect_to_polygon(pts[0], pts[1])
            elif stype == "circle" and len(pts) == 2:
                poly_pts = circle_to_polygon(pts[0], pts[1], nverts=40)
            else:
                # Skip unsupported or insufficient points (line, point, etc.)
                continue

            area = polygon_area(poly_pts)
            bbox = poly_bbox(poly_pts)
            seg = to_segmentation(poly_pts)

            annotations.append({
                "id": next_anno_id,
                "image_id": next_image_id,
                "category_id": cat_id,
                "segmentation": seg,
                "area": float(area),
                "bbox": [float(x) for x in bbox],
                "iscrowd": 0
            })
            next_anno_id += 1

        next_image_id += 1

    coco = {
        "images": images,
        "annotations": annotations,
        "categories": categories
    }

    out_path = Path(OUT_JSON)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(coco, f, ensure_ascii=False)

    print(f"[OK] Wrote COCO JSON to: {out_path}")
    print(f"[STATS] images={len(images)} annotations={len(annotations)} categories={len(categories)}")

if __name__ == "__main__":
    main()
