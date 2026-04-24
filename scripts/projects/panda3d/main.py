"""Runnable Panda 3D app — loads scene.egg and spins the camera."""
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
