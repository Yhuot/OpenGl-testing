from __future__ import annotations
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from itertools import *
from OpenGL.GLU import *
from Graphics.Utils.shader_utils import Material
from typing import Optional, List
from glm import *
import numpy as np

class Shape():
    def __init__(self, material: str = "default"):
        self.material = material
        self.object: Optional[Object] = None
        pass

class Triangle(Shape):
    def __init__(self, object: Object, vertices: List[vec3]):

        super().__init__()
        self.object = object
        self.position = vec3(0, 0, 0)
        self.rotation = vec3(0, 0, 0)
        self.scale = vec3(1, 1, 1)

        # 🧊 Compute normal
        u = vertices[1] - vertices[0]
        v = vertices[2] - vertices[0]
        normal = normalize(cross(u, v))

        data = []
        for vtx in vertices:
            data += [vtx.x, vtx.y, vtx.z]
            data += [normal.x, normal.y, normal.z]

        self.vertex_count = 3
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        vertex_data = np.array(data, dtype=np.float32)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

        # position
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # normal
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * 4, ctypes.c_void_p(3 * 4))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def get_model_matrix(self):
        model = mat4(1.0)
        model = translate(model, vec3(self.position.x, self.position.y, self.position.z))
        model = rotate(model, radians(self.rotation.x), vec3(1, 0, 0))
        model = rotate(model, radians(self.rotation.y), vec3(0, 1, 0))
        model = rotate(model, radians(self.rotation.z), vec3(0, 0, 1))
        model = scale(model, vec3(self.scale.x, self.scale.y, self.scale.z))
        return np.array(model.to_list(), dtype=np.float32)

    def draw(self):
        material = self.object.rootNode.shaders.get_shader(self.material)
        # Set the model matrix for the current object
        model = self.get_model_matrix()
        material.set_mat4("model", model)
        # Optionally pass color to shader
        glUniform3f(glGetUniformLocation(material.id, b"color"), 1.0, 1.0, 1.0)

        # Bind and draw the object
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        glBindVertexArray(0)

class Plane(Shape):
    def __init__(self, object: Object, position: vec3 = vec3(0, 0, 0), vertices: List[vec3] = [vec3(-1, -1, 0), vec3( 1, -1, 0), vec3( 1,  1, 0), vec3(-1,  1, 0)], rotation: vec3 = vec3(0, 0, 0), scale: vec3 = vec3(1, 1, 1,)):
        super().__init__()
        self.object = object
        # Panel size defines width and height (a square panel, for simplicity)
        self.position = position
        self.scale = scale
        self.rotation = rotation
        self.vertices = vertices
        
        # Create two triangles to form the panel (quad)
        self.triangles = [
            Triangle(self.object, vertices=[self.vertices[0], self.vertices[1], self.vertices[2]]),  # Bottom triangle
            Triangle(self.object, vertices=[self.vertices[0], self.vertices[2], self.vertices[3]])   # Top triangle
        ]

    def updateTriangles(self):
        self.triangles[0].vertices = [self.vertices[0], self.vertices[1], self.vertices[2]]
        self.triangles[1].vertices = [self.vertices[0], self.vertices[2], self.vertices[3]]
        self.triangles[0].color = self.color
        self.triangles[1].color = self.color

    def moveVertice(self, which: int, by: vec3):
        self.vertices[which] += by
        self.updateTriangles()

    def moveVertice_to(self, which: int, to: vec3):
        self.vertices[which] = to
        self.updateTriangles()

    def rotate(self, by: vec3):
        self.rotation += by

    def rotate_to(self, to: vec3):
        self.rotation = to

    def draw(self):
        glPushMatrix()
        
        # Apply world transformations (position, rotation, etc.)
        glTranslatef(self.position.x, self.position.y, self.position.z)
        glRotatef(self.rotation.x, 1, 0, 0)
        glRotatef(self.rotation.y, 0, 1, 0)
        glRotatef(self.rotation.z, 0, 0, 1)
        glScalef(self.scale.x, self.scale.y, self.scale.z)
        
        # Draw the two triangles of the panel
        for triangle in self.triangles:
            triangle.draw()

        glPopMatrix()

class Cube(Shape):
    def __init__(self, object: Object, position: vec3 = vec3(0, 0, 0), rotation: vec3 = vec3(0, 0, 0), color: tuple = (1.0, 1.0, 1.0), scale: vec3 = vec3(1, 1, 1,)):
        super().__init__()
        self.object = object
        # Panel size defines width and height (a square panel, for simplicity)
        self.position = position
        self.rotation = rotation
        self.color = color
        self.scale = scale

        vertices = [
            vec3(-1, -1, 1),  # Bottom-left-front
            vec3( 1, -1, 1),  # Bottom-right-front
            vec3( 1,  1, 1),  # Top-right-front
            vec3(-1,  1, 1),  # Top-left-front
            vec3(-1, -1, -1),  # Bottom-left-back
            vec3( 1, -1, -1),  # Bottom-right-back
            vec3( 1,  1, -1),  # Top-right-back
            vec3(-1,  1, -1)   # Top-left-back
        ]
        
        # Create two triangles to form the panel (quad)
        self.planes = [
            Plane(self.object, vertices=[vertices[6], vertices[7], vertices[3], vertices[2]]), # top plane
            Plane(self.object, vertices=[vertices[5], vertices[4], vertices[0], vertices[1]]), # bottom plane
            Plane(self.object, vertices=[vertices[1], vertices[0], vertices[3], vertices[2]]), # front plane
            Plane(self.object, vertices=[vertices[5], vertices[4], vertices[7], vertices[6]]), # back plane
            Plane(self.object, vertices=[vertices[7], vertices[3], vertices[0], vertices[4]]), # left plane
            Plane(self.object, vertices=[vertices[6], vertices[2], vertices[1], vertices[5]])  # right plane
        ]

    def updatePlanes(self):
        self.planes[0].vertices = [vertices[7], vertices[6], vertices[3], vertices[2]]
        self.planes[1].vertices = [vertices[4], vertices[5], vertices[0], vertices[1]]
        for i in self.planes:
            #i.color = self.color
            i.updateTriangles()

    def moveVertice(self, which: int, by: vec3):
        vertices[which] += by
        self.updatePlanes()

    def moveVertice_to(self, which: int, to: vec3):
        vertices[which] = to
        self.updatePlanes()

    def rotate(self, by: vec3):
        self.rotation += by

    def rotate_to(self, to: vec3):
        self.rotation = to

    def draw(self):
        glPushMatrix()
        
        # Apply world transformations (position, rotation, etc.)
        glTranslatef(self.position.x, self.position.y, self.position.z)
        glRotatef(self.rotation.x, 1, 0, 0)
        glRotatef(self.rotation.y, 0, 1, 0)
        glRotatef(self.rotation.z, 0, 0, 1)
        glScalef(self.scale.x, self.scale.y, self.scale.z)
        
        # Draw the two triangles of the panel
        for planes in self.planes:
            planes.draw()

        glPopMatrix()

