"""Procedural art helpers: sprite atlas, voxel isometric render, tilemap.

Everything produced here is deterministic (seeded) so CI regenerates bit-for-bit
identical PNGs. No GPU, no game engine at runtime — just numpy + Pillow.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# ---- Palette (matches the portfolio editorial theme) ----------------------
PALETTE = {
    "teal": (46, 122, 123),
    "teal_deep": (31, 90, 91),
    "amber": (217, 164, 65),
    "amber_deep": (178, 125, 30),
    "ink": (15, 26, 31),
    "paper": (251, 250, 247),
    "paper_2": (242, 239, 232),
    "line": (227, 222, 211),
    "green": (86, 140, 86),
    "green_deep": (60, 98, 60),
    "red": (176, 74, 58),
    "violet": (100, 82, 138),
}


def _rgb(name: str) -> tuple[int, int, int]:
    return PALETTE[name]


# ---- Sprite atlas ---------------------------------------------------------
@dataclass
class Sprite:
    name: str
    w: int
    h: int
    x: int = 0
    y: int = 0


def generate_sprite_atlas(
    out_png: Path,
    n_rows: int = 4,
    n_cols: int = 6,
    tile: int = 96,
    seed: int = 7,
) -> list[Sprite]:
    """Generate a pixel-art sprite sheet of deterministic creatures.

    Each sprite is a little procedural voxel-stack blob with two limbs and an
    eye. Returns the list of Sprite rects for the atlas manifest.
    """
    rng = np.random.default_rng(seed)
    W, H = n_cols * tile, n_rows * tile
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    sprites: list[Sprite] = []

    body_colors = [
        _rgb("teal"), _rgb("amber"), _rgb("green"), _rgb("red"),
        _rgb("violet"), _rgb("teal_deep"), _rgb("amber_deep"), _rgb("green_deep"),
    ]

    idx = 0
    for r in range(n_rows):
        for c in range(n_cols):
            x0, y0 = c * tile, r * tile
            name = f"creature_{idx:02d}"
            # Body: rounded rectangle
            body = body_colors[idx % len(body_colors)]
            pad = 14
            draw.rounded_rectangle(
                (x0 + pad, y0 + pad + 10, x0 + tile - pad, y0 + tile - pad),
                radius=14,
                fill=body,
            )
            # Belly
            belly = tuple(min(255, v + 40) for v in body)
            draw.rounded_rectangle(
                (x0 + pad + 10, y0 + pad + 34, x0 + tile - pad - 10, y0 + tile - pad - 8),
                radius=10,
                fill=belly,
            )
            # Head stripe
            draw.rectangle(
                (x0 + pad + 6, y0 + pad + 22, x0 + tile - pad - 6, y0 + pad + 30),
                fill=_rgb("ink"),
            )
            # Eyes
            eye_y = y0 + pad + 16
            left_x = x0 + pad + 18
            right_x = x0 + tile - pad - 26
            draw.ellipse((left_x, eye_y, left_x + 10, eye_y + 10), fill=_rgb("paper"))
            draw.ellipse((right_x, eye_y, right_x + 10, eye_y + 10), fill=_rgb("paper"))
            # Pupils (randomized direction so no two sprites feel identical)
            dx = int(rng.integers(-2, 3))
            dy = int(rng.integers(-1, 2))
            draw.ellipse(
                (left_x + 2 + dx, eye_y + 2 + dy, left_x + 6 + dx, eye_y + 6 + dy),
                fill=_rgb("ink"),
            )
            draw.ellipse(
                (right_x + 2 + dx, eye_y + 2 + dy, right_x + 6 + dx, eye_y + 6 + dy),
                fill=_rgb("ink"),
            )
            # Feet
            draw.rectangle(
                (x0 + pad + 8, y0 + tile - pad - 4, x0 + pad + 22, y0 + tile - pad + 2),
                fill=_rgb("ink"),
            )
            draw.rectangle(
                (x0 + tile - pad - 22, y0 + tile - pad - 4, x0 + tile - pad - 8, y0 + tile - pad + 2),
                fill=_rgb("ink"),
            )
            sprites.append(Sprite(name=name, w=tile, h=tile, x=x0, y=y0))
            idx += 1

    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    return sprites


# ---- Voxel isometric render ----------------------------------------------
def _project_iso(x: float, y: float, z: float, tile_w: int, tile_h: int) -> tuple[float, float]:
    """Classic 2:1 iso projection. +x = right-down, +y = left-down, +z = up."""
    px = (x - y) * (tile_w / 2)
    py = (x + y) * (tile_h / 2) - z * tile_h
    return px, py


def generate_iso_scene(
    out_png: Path,
    size: tuple[int, int] = (1440, 720),
    seed: int = 3,
) -> None:
    """Render a small isometric voxel scene (buildings, path, props)."""
    rng = np.random.default_rng(seed)
    W, H = size
    img = Image.new("RGBA", (W, H), _rgb("paper") + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    tile_w, tile_h = 48, 24
    cx, cy = W // 2, int(H * 0.28)

    # --- Build a 12x12 height map ---
    N = 12
    hmap = np.zeros((N, N), dtype=int)
    # Ground: 1
    hmap[:, :] = 1
    # Plaza: a small 2x2 cutout near the corner
    hmap[5:7, 5:7] = 0
    # Two building clusters
    hmap[2:5, 2:5] = 3
    hmap[2, 2] = 5  # tower
    hmap[7:10, 6:9] = 2
    hmap[8, 7] = 4
    # Random prop cubes
    for _ in range(8):
        i, j = int(rng.integers(0, N)), int(rng.integers(0, N))
        if hmap[i, j] <= 1:
            hmap[i, j] = int(rng.integers(1, 3))

    # Draw back-to-front (painter's algorithm)
    draws: list[tuple[float, int, int, int]] = []
    for i in range(N):
        for j in range(N):
            h = int(hmap[i, j])
            if h == 0:
                continue
            draws.append((i + j, i, j, h))
    draws.sort(key=lambda t: t[0])

    def _voxel(x: float, y: float, z: float, color: tuple[int, int, int]) -> None:
        # 8 corners of a unit cube in world space
        corners = [
            (x, y, z),       # 0 bottom-back-left
            (x + 1, y, z),   # 1 bottom-back-right
            (x + 1, y + 1, z),  # 2 bottom-front-right
            (x, y + 1, z),   # 3 bottom-front-left
            (x, y, z + 1),   # 4 top-back-left
            (x + 1, y, z + 1),  # 5 top-back-right
            (x + 1, y + 1, z + 1),  # 6 top-front-right
            (x, y + 1, z + 1),  # 7 top-front-left
        ]
        px = [_project_iso(a, b, c, tile_w, tile_h) for a, b, c in corners]
        px = [(cx + p[0], cy + p[1]) for p in px]

        top = [px[4], px[5], px[6], px[7]]
        left = [px[3], px[0], px[4], px[7]]   # +y facing
        right = [px[1], px[2], px[6], px[5]]  # +x facing

        # Shades
        light = tuple(min(255, v + 30) for v in color)
        dark = tuple(max(0, v - 40) for v in color)
        darker = tuple(max(0, v - 70) for v in color)

        draw.polygon(right, fill=dark, outline=_rgb("ink"))
        draw.polygon(left, fill=darker, outline=_rgb("ink"))
        draw.polygon(top, fill=light, outline=_rgb("ink"))

    for _, i, j, h in draws:
        # Pick color by height bucket
        if h >= 4:
            color = _rgb("amber")
        elif h >= 2:
            color = _rgb("teal")
        else:
            color = _rgb("paper_2")
        for z in range(h):
            _voxel(i, j, z, color)

    # Title strip
    draw.rectangle((0, 0, W, 54), fill=_rgb("ink"))
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
    except Exception:  # pragma: no cover
        font = None
    draw.text((24, 18), "Isometric voxel scene  ·  12×12 grid  ·  Python-rendered", fill=_rgb("paper"), font=font)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)


# ---- Tilemap --------------------------------------------------------------
def generate_tilemap(out_png: Path, tile: int = 48, cols: int = 24, rows: int = 14, seed: int = 11) -> np.ndarray:
    """Generate a 2D tilemap PNG + return the integer grid."""
    rng = np.random.default_rng(seed)
    grid = np.zeros((rows, cols), dtype=int)
    # Fill with grass
    grid[:, :] = 1
    # Borders = wall
    grid[0, :] = 0
    grid[-1, :] = 0
    grid[:, 0] = 0
    grid[:, -1] = 0
    # Path
    for c in range(1, cols - 1):
        grid[rows // 2, c] = 2
    # Random trees
    for _ in range(18):
        r, c = int(rng.integers(1, rows - 1)), int(rng.integers(1, cols - 1))
        if grid[r, c] == 1:
            grid[r, c] = 3
    # Random water pond
    for r in range(3, 6):
        for c in range(15, 20):
            grid[r, c] = 4

    W, H = cols * tile, rows * tile
    img = Image.new("RGBA", (W, H), _rgb("paper") + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    colors = {
        0: _rgb("ink"),       # wall
        1: (188, 205, 154),   # grass
        2: _rgb("amber"),     # path
        3: _rgb("green_deep"),  # tree
        4: _rgb("teal"),      # water
    }
    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * tile, r * tile
            t = int(grid[r, c])
            draw.rectangle((x0, y0, x0 + tile, y0 + tile), fill=colors[t])
            if t == 3:
                # tree trunk + leaves
                draw.rectangle(
                    (x0 + tile // 2 - 4, y0 + tile - 16, x0 + tile // 2 + 4, y0 + tile - 4),
                    fill=(120, 80, 40),
                )
                draw.ellipse(
                    (x0 + 6, y0 + 4, x0 + tile - 6, y0 + tile - 14),
                    fill=_rgb("green"),
                    outline=_rgb("green_deep"),
                )
            if t == 2:
                draw.ellipse(
                    (x0 + tile // 2 - 3, y0 + tile // 2 - 3, x0 + tile // 2 + 3, y0 + tile // 2 + 3),
                    fill=_rgb("amber_deep"),
                )
            # grid lines
            draw.rectangle((x0, y0, x0 + tile, y0 + tile), outline=(0, 0, 0, 40))

    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    return grid


# ---- Particle burst -------------------------------------------------------
def generate_particle_burst(out_png: Path, size: tuple[int, int] = (1200, 700), seed: int = 17) -> None:
    rng = np.random.default_rng(seed)
    W, H = size
    img = Image.new("RGBA", (W, H), _rgb("ink") + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Draw several bursts
    centers = [(W * 0.25, H * 0.55), (W * 0.55, H * 0.5), (W * 0.8, H * 0.6)]
    tints = [_rgb("amber"), _rgb("teal"), _rgb("green")]
    for (cx, cy), tint in zip(centers, tints):
        for i in range(400):
            angle = rng.uniform(0, 2 * math.pi)
            speed = rng.uniform(10, 220)
            life = rng.uniform(0.1, 1.0)
            radius = max(1, int(6 * (1 - life) + 1))
            x = cx + math.cos(angle) * speed * life
            y = cy + math.sin(angle) * speed * life - 60 * life * life
            alpha = int(255 * (1 - life))
            color = tint + (alpha,)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    # Soft glow
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle((0, 0, W, 54), fill=_rgb("ink"))
    draw.text((24, 18), "Particle system burst  ·  1200 particles  ·  deterministic seed", fill=_rgb("paper"))

    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)


# ---- Engine comparison matrix ---------------------------------------------
def generate_engine_matrix(out_png: Path, size: tuple[int, int] = (1400, 780)) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    engines = ["Godot 4", "Defold", "Solar 2D", "Panda 3D", "Stride"]
    criteria = [
        "2D runtime",
        "3D runtime",
        "Scripting",
        "Project file\n(text)",
        "Mobile\nexport",
        "License",
        "CI-friendly\n(headless)",
    ]
    # 0 = partial/no, 1 = yes, values kept factual
    data = np.array([
        [1, 1, 1, 1, 1, 1, 1],   # Godot 4
        [1, 0, 1, 1, 1, 1, 1],   # Defold
        [1, 0, 1, 1, 1, 1, 0],   # Solar 2D
        [0, 1, 1, 0, 0, 1, 1],   # Panda 3D
        [1, 1, 1, 1, 1, 1, 1],   # Stride
    ], dtype=float)

    fig, ax = plt.subplots(figsize=(size[0] / 100, size[1] / 100), dpi=100)
    fig.patch.set_facecolor("#FBFAF7")
    ax.set_facecolor("#FBFAF7")

    # custom colormap teal-amber
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "teal_amber",
        [(0.94, 0.93, 0.89), (0.18, 0.48, 0.48)],
    )

    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(len(criteria)))
    ax.set_xticklabels(criteria, fontsize=11, color="#0F1A1F")
    ax.set_yticks(range(len(engines)))
    ax.set_yticklabels(engines, fontsize=13, fontweight="bold", color="#0F1A1F")
    ax.tick_params(length=0)
    ax.set_title("Open-source game engines — capability matrix",
                 fontsize=16, fontweight="bold", color="#0F1A1F", pad=18, loc="left")

    labels = {0: "partial", 1: "yes"}
    for r in range(data.shape[0]):
        for c in range(data.shape[1]):
            v = data[r, c]
            fc = "#FBFAF7" if v > 0.5 else "#0F1A1F"
            ax.text(c, r, labels[int(v)], ha="center", va="center",
                    fontsize=11, fontweight="bold", color=fc)

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=140, facecolor=fig.get_facecolor())
    plt.close()


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[2] / "assets"
    generate_sprite_atlas(base / "renders" / "_atlas_preview.png")
    generate_iso_scene(base / "renders" / "_iso_preview.png")
    generate_tilemap(base / "renders" / "_tilemap_preview.png")
    generate_particle_burst(base / "renders" / "_particle_preview.png")
    generate_engine_matrix(base / "renders" / "_matrix_preview.png")
    print("[ok] art helpers preview rendered")
