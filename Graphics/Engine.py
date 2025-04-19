from __future__ import annotations
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from itertools import *
from OpenGL.GLU import *
from Graphics.Utils.shader_utils import *
from Graphics.Utils import Shapes
from typing import Optional, List, Dict
from glm import *


class PointLight:
    def __init__(self, position, color, intensity, radius):
        self.position = position
        self.color = color
        self.intensity = intensity
        self.radius = radius

class Object:
    def __init__(self, rootNode: Root, name: str, activeCamera: Optional[Camera] = None, parent: Optional['Object'] = None, position: vec3 = vec3(0, 0, 0), angle: vec3 = vec3(0, 0, 0), scale: vec3 = vec3(1, 1, 1)):
        self.rootNode = rootNode
        self.name: str = name
        self.shapes: Dict[str, Shapes.Shape] = {}
        self.activeCamera: Camera = activeCamera
        self.children: Dict[str, Object] = {}  # Correcting this initialization
        self.parent = parent
        self.position = position
        self.scale = scale
        self.angle = angle



    def move(self, amount: vec3):
        self.position += amount
        for name, child in self.children:
            child.move(amount)

    def move_to(self, where: vec3):
        self.position = where
        for name, child in self.children:
            child.move_to(where)

    def apply_scale(self, scale: vec3):  # Renaming scale method to avoid conflict
        self.scale = scale

    def rotate(self, rotation: vec3):  # Fixed typo here (rocation -> rotation)
        self.angle += rotation
        for i, a in self.children:
            a.rotate(rotation)

    def rotate_to(self, rotation: vec3):  # Fixed typo here (rocation -> rotation)
        self.angle = rotation
        for i, a in self.children:
            a.rotate_to(rotation)

    def addChild(self, name: str, position: vec3 = vec3(0.0, 0.0, 0.0), angle: vec3 = vec3(0.0, 0.0, 0.0), scale: vec3 = vec3(1.0, 1.0, 1.0)):
        if not (name in self.children):
            self.children[name] = Object(self.rootNode, name, None, self, position, angle, scale)
        else:
            i = 1
            new_name = name + "_" + str(i)
            while new_name in self.children:
                i += 1
            self.children[new_name] = Object(self.rootNode, new_name, None, self, position, angle, scale)

    def removeChild(self, name: str):
        self.children.pop(name)

    def addShape(self, name: str, shape: Shapes.Shape):
        if not (name in self.shapes):
            self.shapes[name] = shape
            self.shapes[name].object = self
        else:
            i = 1
            new_name = name + "_" + str(i)
            while new_name in self.shapes:
                i += 1
            self.shapes[new_name] = shape
            self.shapes[name].object = self


    def getCamera(self):
        if self.activeCamera != None:
            return self.activeCamera
        else:
            return self.parent.getCamera()

    def draw(self):


        camera: Camera = self.getCamera()

        glPushMatrix()
        glTranslatef(self.position.x, self.position.y, self.position.z)  # Apply translation
        glRotatef(self.angle.x, 1, 0, 0)  # Apply rotation on the X-axis
        glRotatef(self.angle.y, 0, 1, 0)  # Apply rotation on the Y-axis
        glRotatef(self.angle.z, 0, 0, 1)  # Apply rotation on the Z-axis
        glScalef(self.scale.x, self.scale.y, self.scale.z)  # Apply scaling

        # Draw all elements in this object (e.g., cubes, spheres, etc.)
        for shape_name, shape in self.shapes.items():
            shape.draw()

        glPopMatrix()

        for child_name, child in self.children.items():
            child.draw()
        pass

class Camera:
    def __init__(self, parent: Root, id: int, width: int, height: int, fov: float = 45.0, near: float = 0.1, far: float = 100.0,
                 position: vec3 = vec3(0.0, 0.0, 0.0), active: bool = False):

        self.id: int = id
        self.parent: Root = parent
        self.width = width
        self.height = height
        self.aspect_ratio = width / height
        self.active = active

        self.fov = fov
        self.near = near
        self.far = far

        self.position = position
        self.direction = vec3(0.0, 0.0, -1.0)
        self.up = vec3(0.0, 1.0, 0.0)

    def get_view_matrix(self):
        return lookAt(self.position, self.position + self.direction, self.up)

    def get_projection_matrix(self):
        return perspective(radians(self.fov), self.aspect_ratio, self.near, self.far)

    def apply_matrices(self):
        # Upload matrices to OpenGL — call this before rendering the scene
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.aspect_ratio, self.near, self.far)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        look_target = self.position + self.direction
        #look_target = vec3(0.0, 0.0, -1.0)
        gluLookAt(
            self.position.x, self.position.y, self.position.z,
            look_target.x, look_target.y, look_target.z,
            self.up.x, self.up.y, self.up.z
        )

    def move(self, by: vec3):
        self.position += by

    def move_to(self, to: vec3):
        self.position = to

    def rotate(self, pitch: float, yaw: float, roll: float = 0.0):
        # Create rotation matrices
        yaw_matrix = rotate(mat4(1.0), radians(yaw), self.up)
        right = normalize(cross(self.direction, self.up))
        pitch_matrix = rotate(mat4(1.0), radians(pitch), right)

        # Combine rotations
        rotation = yaw_matrix * pitch_matrix

        # Rotate direction
        rotated_dir = vec4(self.direction, 0.0)
        rotated_dir = rotation * rotated_dir
        self.direction = normalize(vec3(rotated_dir))

    def rotate_to(self, pitch: float, yaw: float, roll: float = 0.0):
        # Create rotation matrices
        yaw_matrix = rotate(mat4(1.0), radians(yaw), self.up)
        right = normalize(cross(vec3(0.0, 0.0, -1.0), self.up))
        pitch_matrix = rotate(mat4(1.0), radians(pitch), right)

        # Combine rotations
        rotation = yaw_matrix * pitch_matrix

        # Rotate direction
        rotated_dir = vec4(self.direction, 0.0)
        rotated_dir = rotation * rotated_dir
        self.direction = normalize(vec3(rotated_dir))

class Root:
    def __init__(self, Width: int = 1366, Height: int = 768, FOV: float = 45.0, RenderDistance: float = 100, BGColor: tuple = (0.31, 0.31, 0.31, 1.0)):
        self.display = None
        self.screen = None
        self.BGColor = BGColor
        # OpenGL states
        self.windowGeometry = (Width, Height)
        self.FOV = FOV
        self.cameras: List[Camera] = [Camera(self, 0, width=1366, height=768, position=vec3(0.0, 0.0, 5.0), active=True)]
        self.activeCamera: int = 0
        self.clock = pygame.time.Clock()
        self.root = Object(self, "Root", activeCamera=self.cameras[self.activeCamera])


    def start(self):
        pygame.init()
        self.display = self.windowGeometry
        self.screen = pygame.display.set_mode(self.display, pygame.DOUBLEBUF | pygame.OPENGL)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        self.shaders = shaderManager()
        self.shaders.add_shader({
                "name": "default",
                "albedo": (1.0, 1.0, 1.0), 
                "roughness": 0.5, 
                "reflectiveness": 0.5
            })

    
    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear screen and depth buffer
        glClearColor(self.BGColor[0], self.BGColor[1], self.BGColor[2], self.BGColor[3])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.root.draw()
        # Swap buffers and cap framerate
        self.cameras[self.activeCamera].apply_matrices()
        pygame.display.flip()

    def addCamera(self, width: int, height: int, fov: float = 45.0, near: float = 0.1, far: float = 100.0,
                 position: vec3 = vec3(0.0, 0.0, 0.0)):
        self.cameras.append(Camera(self, width=width, height=height, fov=fov, near=near, far=far, position=position, id=len(self.cameras)))

    def removeCamera(self, id):
        if id < len(self.cameras) and id > -1 and len(self.cameras) > 0:
            if self.activeCamera == id:
                print("Cannot delete active camera, dumbass")
            else:
                self.cameras.pop(id)

    def get_activeCamera(self):
        return self.cameras[self.activeCamera]

    def activateCamera(self, id):
        if id < len(self.cameras) and id > -1 and len(self.cameras) > 0:
            self.cameras[id].active = True
            self.activeCamera = id

    def addObject(self, name: str, position: vec3 = vec3(0.0, 0.0, 0.0), angle: vec3 = vec3(0.0, 0.0, 0.0), scale: vec3 = vec3(1.0, 1.0, 1.0)):
        if not (name in self.root.children):
            self.root.addChild(name, Object(name, None, self.root, position, angle, scale))
        else:
            i = 1
            new_name = name + "_" + str(i)
            while new_name in self.root.children:
                i += 1
            self.root.addChild(new_name, Object(new_name, None, self.root, position, angle, scale))

    def removeObject(self, name: str):
        self.root.removeChild(name)

    def stop(self):
        pygame.quit()



# Function to draw a sphere at a given position (x, y, z)
def draw_sphere(x, y, z, radius=0.1, slices=10, stacks=10):
    glPushMatrix()  # Save the current transformation matrix
    glTranslatef(x, y, z)  # Move the sphere to the specified position
    quadric = gluNewQuadric()  # Create a new Quadric object (sphere)
    gluSphere(quadric, radius, slices, stacks)  # Draw the sphere
    glPopMatrix()  # Restore the previous transformation matrix
