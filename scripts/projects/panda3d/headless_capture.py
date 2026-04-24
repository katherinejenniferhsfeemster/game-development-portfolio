"""Headless frame capture for CV training.

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
