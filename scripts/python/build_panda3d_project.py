"""Generate a Panda 3D project: scene graph JSON + EGG asset + Python runtime.

Panda 3D has two native scene formats:
  * .egg  — the classic text-based scene graph (hand-readable).
  * .bam  — the binary runtime format (compiled from .egg).

We emit:
  * `scripts/projects/panda3d/main.py`   — runnable Panda 3D app.
  * `scripts/projects/panda3d/scene.egg` — voxel scene as Panda .egg text.
  * `scripts/projects/panda3d/headless_capture.py` — offscreen buffer capture.
  * `scripts/projects/panda3d/scene_graph.json`    — portable scene tree.
  * `scripts/projects/panda3d/Config.prc`          — runtime config.

The .egg is built from the same 12x12 voxel world as the Godot scene, so the
two projects capture the same visual content in different toolchains.
"""

from __future__ import annotations

from pathlib import Path
import json
import numpy as np


CONFIG_PRC = """# Config.prc — Panda 3D runtime config.
window-title AI Dataset Sandbox
win-size 1280 720
show-frame-rate-meter #t
sync-video #f
framebuffer-multisample 1
multisamples 4
"""

MAIN_PY = '''"""Runnable Panda 3D app — loads scene.egg and spins the camera."""
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, LVector4, loadPrcFile
from pathlib import Path

loadPrcFile(str(Path(__file__).parent / "Config.prc"))


class DatasetApp(ShowBase):
    def __init__(self) -> None:
        super().__init__()
        self.disableMouse()
        self.camera.setPos(20, -24, 18)
        self.camera.lookAt(6, 6, 0)

        scene = self.loader.loadModel(str(Path(__file__).parent / "scene.egg"))
        scene.reparentTo(self.render)

        amb = AmbientLight("amb")
        amb.setColor(LVector4(0.35, 0.35, 0.40, 1))
        self.render.setLight(self.render.attachNewNode(amb))

        sun = DirectionalLight("sun")
        sun.setColor(LVector4(1.0, 0.95, 0.85, 1))
        sunNp = self.render.attachNewNode(sun)
        sunNp.setHpr(-30, -60, 0)
        self.render.setLight(sunNp)

        self.taskMgr.add(self._spin, "spin")

    def _spin(self, task):
        self.render.setH(task.time * 10.0)
        return task.cont


if __name__ == "__main__":
    DatasetApp().run()
'''

HEADLESS_CAPTURE = '''"""Headless frame capture for CV training.

Uses Panda's offscreen framebuffer to render N frames of the rotating scene
and save them as PNGs, without opening a display. Works under Xvfb-free CI.
"""
from pathlib import Path
from panda3d.core import (
    GraphicsPipeSelection, FrameBufferProperties, WindowProperties,
    GraphicsOutput, Texture, loadPrcFileData, PNMImage,
)
loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")

from direct.showbase.ShowBase import ShowBase


class CaptureApp(ShowBase):
    def __init__(self, n_frames: int = 120, out_dir: Path = Path("captures")) -> None:
        super().__init__(windowType="offscreen")
        scene = self.loader.loadModel(str(Path(__file__).parent / "scene.egg"))
        scene.reparentTo(self.render)
        self.camera.setPos(20, -24, 18)
        self.camera.lookAt(6, 6, 0)

        out_dir.mkdir(parents=True, exist_ok=True)
        for i in range(n_frames):
            self.render.setH(i * 3.0)
            self.graphicsEngine.renderFrame()
            tex = self.win.getScreenshot()
            if tex:
                img = PNMImage()
                tex.store(img)
                img.write(str(out_dir / f"frame_{i:04d}.png"))


if __name__ == "__main__":
    CaptureApp(n_frames=120).userExit()
'''


def _egg_cube(cx: float, cy: float, cz: float, color: tuple[float, float, float]) -> str:
    """Emit an .egg <Group> with a unit cube centered at (cx,cy,cz)."""
    # 8 corners
    verts = []
    for dx, dy, dz in [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                       (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]:
        verts.append((cx + dx, cy + dy, cz + dz))
    # 6 faces, CCW winding
    faces = [
        (0, 1, 2, 3),  # bottom
        (4, 7, 6, 5),  # top
        (0, 4, 5, 1),  # -y
        (1, 5, 6, 2),  # +x
        (2, 6, 7, 3),  # +y
        (3, 7, 4, 0),  # -x
    ]
    out = ["<Group> cube_%d_%d_%d {" % (int(cx), int(cy), int(cz))]
    out.append("  <VertexPool> vp {")
    for i, v in enumerate(verts):
        out.append("    <Vertex> %d { %.3f %.3f %.3f }" % (i, *v))
    out.append("  }")
    for fi, face in enumerate(faces):
        out.append("  <Polygon> {")
        out.append("    <RGBA> { %.3f %.3f %.3f 1 }" % color)
        out.append("    <VertexRef> { %d %d %d %d <Ref> { vp } }" % face)
        out.append("  }")
    out.append("}")
    return "\n".join(out)


def build_egg_scene() -> tuple[str, list[dict]]:
    rng = np.random.default_rng(3)
    N = 12
    hmap = np.ones((N, N), dtype=int)
    hmap[2:5, 2:5] = 3
    hmap[2, 2] = 5
    hmap[7:10, 6:9] = 2
    hmap[8, 7] = 4
    for _ in range(8):
        i, j = int(rng.integers(0, N)), int(rng.integers(0, N))
        if hmap[i, j] <= 1:
            hmap[i, j] = int(rng.integers(1, 3))

    palette_high = (0.851, 0.643, 0.255)   # amber
    palette_mid = (0.182, 0.482, 0.484)    # teal
    palette_low = (0.949, 0.937, 0.910)    # paper_2

    bodies: list[str] = []
    graph_nodes: list[dict] = []
    for i in range(N):
        for j in range(N):
            h = int(hmap[i, j])
            if h == 0:
                continue
            for z in range(h):
                color = palette_high if h >= 4 else palette_mid if h >= 2 else palette_low
                bodies.append(_egg_cube(float(i), float(j), float(z), color))
                graph_nodes.append({
                    "id": f"vox_{i}_{j}_{z}",
                    "pos": [i, j, z],
                    "color": list(color),
                })

    egg = (
        '<CoordinateSystem> { Z-Up }\n\n'
        '<Comment> { "Generated by build_panda3d_project.py" }\n\n'
        + "\n".join(bodies)
        + "\n"
    )
    return egg, graph_nodes


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "projects" / "panda3d"
    root.mkdir(parents=True, exist_ok=True)

    (root / "Config.prc").write_text(CONFIG_PRC, encoding="utf-8")
    (root / "main.py").write_text(MAIN_PY, encoding="utf-8")
    (root / "headless_capture.py").write_text(HEADLESS_CAPTURE, encoding="utf-8")

    egg, graph = build_egg_scene()
    (root / "scene.egg").write_text(egg, encoding="utf-8")
    (root / "scene_graph.json").write_text(
        json.dumps({"nodes": graph, "count": len(graph)}, indent=2),
        encoding="utf-8",
    )

    print(f"[ok] Panda3D project at {root} — {len(graph)} voxels in scene.egg")


if __name__ == "__main__":
    main()
