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

    def apply_matrices(self, shader):
        shader.use()

        # Get matrices
        view = self.get_view_matrix()
        projection = self.get_projection_matrix()

        # Upload to shader
        shader.set_mat4("view", view)
        shader.set_mat4("projection", projection)



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
        pitch_rad = radians(pitch)
        yaw_rad = radians(yaw)

        # Rebuild direction from angles (FPS-style camera control)
        self.direction = normalize(vec3(
            cos(pitch_rad) * sin(yaw_rad),
            sin(pitch_rad),
            -cos(pitch_rad) * cos(yaw_rad)
        ))

class Root:
    def __init__(self, physics_frequency: int = 60, visuals_frequency: int = 60, Width: int = 1366, Height: int = 768, FOV: float = 45.0, RenderDistance: float = 100, BGColor: tuple = (0.31, 0.31, 0.31, 1.0)):
        pygame.init()
        
        self.windowGeometry = (Width, Height)
        self.physics_frequency = physics_frequency
        self.visuals_frequency = visuals_frequency
        self.display = self.windowGeometry
        self.FOV = FOV
        self.BGColor = BGColor

        # OpenGL setup
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 0)  # Disable VSync
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

        self.running = True
        self.cameras: List[Camera] = [Camera(self, 0, width=Width, height=Height, position=vec3(0.0, 0.0, 5.0), active=True)]
        self.activeCamera: int = 0
        self.root = Object(self, "Root", activeCamera=self.cameras[self.activeCamera])

        # ONE CLOCK TO RULE THEM ALL
        self.clock = pygame.time.Clock()
        self.physics_timer = 0.0
        self.visuals_timer = 0.0

        # Precomputed frame time targets in milliseconds
        self.physics_timestep = 1000.0 / self.physics_frequency
        self.visuals_timestep = 1000.0 / self.visuals_frequency


        self.root.addChild("Cube", position=vec3(0.0, 0.0, -5.0))
        self.root.children["Cube"].addShape("Cube", Shapes.Cube(self.root.children["Cube"],vec3(0, 0, 0), vec3(0, 0, 0), (1.0, 1.0, 1.0), vec3(1, 1, 1,)))


        self.main_loop()

    def main_loop(self):
        while self.running:
            delta = self.clock.tick()  # Returns time in ms since last tick
            self.physics_timer += delta
            self.visuals_timer += delta

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # Physics update
            if self.physics_timer >= self.physics_timestep:
                # Call physics update functions here
                self.physics_timer -= self.physics_timestep  # Subtract instead of zeroing for better accuracy

            # Visual update
            if self.visuals_timer >= self.visuals_timestep:
                self.useShader("default")

                # Clear screen and depth buffer
                glClearColor(*self.BGColor)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                # Draw objects here
                self.root.draw()

                # Swap buffers
                pygame.display.flip()
                self.visuals_timer -= self.visuals_timestep
                
        self.stop()

    def useShader(self, name):
        self.get_activeCamera().apply_matrices(self.shaders.get_shader("default"))

    # Utility methods
    def stop(self):
        pygame.quit()

    def addCamera(self, width: int, height: int, fov: float = 45.0, near: float = 0.1, far: float = 100.0,
                  position: vec3 = vec3(0.0, 0.0, 0.0)):
        self.cameras.append(Camera(self, width=width, height=height, fov=fov, near=near, far=far, position=position, id=len(self.cameras)))

    def removeCamera(self, id):
        if 0 <= id < len(self.cameras):
            if self.activeCamera == id:
                print("Cannot delete active camera, dumbass")
            else:
                self.cameras.pop(id)

    def get_activeCamera(self):
        return self.cameras[self.activeCamera]

    def activateCamera(self, id):
        if 0 <= id < len(self.cameras):
            self.cameras[id].active = True
            self.activeCamera = id

    def addObject(self, name: str, position: vec3 = vec3(0.0, 0.0, 0.0), angle: vec3 = vec3(0.0, 0.0, 0.0), scale: vec3 = vec3(1.0, 1.0, 1.0)):
        if not (name in self.root.children):
            self.root.addChild(name, Object(name, None, self.root, position, angle, scale))
        else:
            i = 1
            new_name = f"{name}_{i}"
            while new_name in self.root.children:
                i += 1
                new_name = f"{name}_{i}"
            self.root.addChild(new_name, Object(new_name, None, self.root, position, angle, scale))

    def removeObject(self, name: str):
        self.root.removeChild(name)



# Function to draw a sphere at a given position (x, y, z)
def draw_sphere(x, y, z, radius=0.1, slices=10, stacks=10):
    glPushMatrix()  # Save the current transformation matrix
    glTranslatef(x, y, z)  # Move the sphere to the specified position
    quadric = gluNewQuadric()  # Create a new Quadric object (sphere)
    gluSphere(quadric, radius, slices, stacks)  # Draw the sphere
    glPopMatrix()  # Restore the previous transformation matrix
