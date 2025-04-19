from Graphics import Engine
from Graphics.Utils import Shapes
from glm import *
import time

MainRoot = Engine.Root()

MainRoot.start()

i = 0
tempo = 300
frametime = 16.7

MainRoot.root.addChild("Cube", position=vec3(0.0, 0.0, -5.0))
MainRoot.root.children["Cube"].addShape("Cube", Shapes.Cube(MainRoot.root.children["Cube"],vec3(0, 0, 0), vec3(0, 0, 0), (1.0, 1.0, 1.0), vec3(1, 1, 1,)))

while i < tempo * 1000 / frametime:
    MainRoot.update()
    MainRoot.get_activeCamera().rotate(0, 1, 0)
    time.sleep(frametime/1000)