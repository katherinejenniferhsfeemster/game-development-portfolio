"""Render portfolio posters for the GitHub Pages site.

Four posters:
  - scene_iso.png          — voxel isometric render (hero image)
  - atlas_grid.png         — sprite atlas with labeled frames
  - particle_burst.png     — CPU-deterministic particle system
  - engine_matrix.png      — FOSS engine capability matrix
"""

from __future__ import annotations

from pathlib import Path

from art_helpers import (
    generate_iso_scene,
    generate_sprite_atlas,
    generate_particle_burst,
    generate_engine_matrix,
    generate_tilemap,
)


def main() -> None:
    renders = Path(__file__).resolve().parents[2] / "assets" / "renders"
    renders.mkdir(parents=True, exist_ok=True)

    generate_iso_scene(renders / "scene_iso.png")
    print("[ok]", renders / "scene_iso.png")

    # Atlas poster: regenerate atlas + overlay labels
    generate_sprite_atlas(renders / "atlas_grid.png")
    print("[ok]", renders / "atlas_grid.png")

    generate_particle_burst(renders / "particle_burst.png")
    print("[ok]", renders / "particle_burst.png")

    generate_engine_matrix(renders / "engine_matrix.png")
    print("[ok]", renders / "engine_matrix.png")

    # Bonus: tilemap for the Solar 2D case study
    generate_tilemap(renders / "tilemap.png")
    print("[ok]", renders / "tilemap.png")


if __name__ == "__main__":
    main()
