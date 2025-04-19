from OpenGL.GL import *
import ctypes
import numpy as np

# Default vertex shader (used for basic setups)
default_vertex_shader = """
    #version 330 core
    layout(location = 0) in vec3 aPos;
    layout(location = 1) in vec3 aNormal;

    uniform mat4 model;
    uniform mat4 view;
    uniform mat4 projection;

    out vec3 Normal;
    out vec3 FragPos;

    void main() {
        FragPos = vec3(model * vec4(aPos, 1.0));
        Normal = mat3(transpose(inverse(model))) * aNormal;
        gl_Position = projection * view * vec4(FragPos, 1.0);
    }
"""

# Default fragment shader
default_fragment_shader = """
    #version 330 core

    // Input from vertex shader
    in vec3 Normal;
    in vec3 FragPos;

    // Output color
    out vec4 FragColor;

    // Uniforms for material properties
    uniform vec3 color; // Base color of the material
    uniform float roughness;
    uniform float reflectiveness;

    // Lighting structures (from application)
    struct Light {
        vec3 position; // Light position
        vec3 color; // Light color
        float intensity; // Light intensity
        float constant; // Constant attenuation factor
        float linear; // Linear attenuation factor
        float quadratic; // Quadratic attenuation factor
    };

    uniform Light lights[10]; // Array of 10 lights (you can increase this number as needed)
    uniform int lightCount; // Number of lights active in the scene

    void main() {
        vec3 finalColor = vec3(0.0); // Initialize final color as black (no light)

        // Loop over all lights in the scene
        for (int i = 0; i < lightCount; i++) {
            // Calculate direction from fragment to light
            vec3 lightDir = normalize(lights[i].position - FragPos);
            float diff = max(dot(normalize(Normal), lightDir), 0.0); // Diffuse lighting

            // Attenuation calculation: distance-based reduction of light intensity
            float distance = length(lights[i].position - FragPos);
            float attenuation = 1.0 / (lights[i].constant + lights[i].linear * distance + lights[i].quadratic * (distance * distance));

            // Add the light's contribution to the final color (with attenuation and intensity)
            finalColor += diff * lights[i].color * lights[i].intensity * attenuation;
        }

        // Apply the final color to the fragment
        FragColor = vec4(finalColor * color, 1.0); // Modulate final color with material color
    }

"""

class Material:
    def __init__(self, albedo: tuple = (1.0, 1.0, 1.0), roughness: float = 0.5, reflectiveness: float = 0.5, vertex_shader: str = default_vertex_shader, fragment_shader: str = default_fragment_shader):
        # Material properties (color, roughness, reflectiveness)
        self.albedo = albedo
        self.roughness = roughness
        self.reflectiveness = reflectiveness
        self.id = self.bake(vertex_shader, fragment_shader)

    def bake(self, vertex_shader_source: str, fragment_shader_source: str):
        # Compile Vertex Shader
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_shader_source)
        glCompileShader(vertex_shader)
        if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
            print(f"ERROR: Vertex Shader compilation failed\n{glGetShaderInfoLog(vertex_shader)}")
        
        # Compile Fragment Shader
        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_shader_source)
        glCompileShader(fragment_shader)
        if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
            print(f"ERROR: Fragment Shader compilation failed\n{glGetShaderInfoLog(fragment_shader)}")

        # Link shaders into a program
        shader_program = glCreateProgram()
        glAttachShader(shader_program, vertex_shader)
        glAttachShader(shader_program, fragment_shader)
        glLinkProgram(shader_program)

        if not glGetProgramiv(shader_program, GL_LINK_STATUS):
            print(f"ERROR: Shader program linking failed\n{glGetProgramInfoLog(shader_program)}")


        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)
        return shader_program

    def use(self):
        # Use the compiled shader program
        glUseProgram(self.id)
        

    def set_mat4(self, name, mat):
        location = glGetUniformLocation(self.id, name)
        if location == -1:
            print(f"[GL ⚠] Uniform '{name}' not found in shader ID {self.id}. Did you bind the shader? Is the uniform used?")
            raise RuntimeError(f"Uniform '{name}' not found in shader ID {self.id}")
        if isinstance(mat, np.ndarray):
            glUniformMatrix4fv(location, 1, GL_TRUE, mat.astype(np.float32))
        else:
            glUniformMatrix4fv(location, 1, GL_TRUE, np.array(mat.to_list(), dtype=np.float32))



    def set_vec3(self, name, vec):
        # Set a 3D vector uniform (for colors, light directions, etc.)
        glUniform3f(glGetUniformLocation(self.id, name), vec[0], vec[1], vec[2])

    def set_float(self, name, value):
        # Set a float uniform (for roughness, reflectiveness, etc.)
        glUniform1f(glGetUniformLocation(self.id, name), value)

    def set_material_properties(self):
        # Send material properties to shader
        self.set_vec3("color", self.albedo)
        self.set_float("roughness", self.roughness)
        self.set_float("reflectiveness", self.reflectiveness)

class shaderManager:
    def __init__(self):
        # Shader manager that stores all materials
        self.shaders = {}

    def add_shader(self, material_dict: dict):
        # Add material based on dict (can be loaded from JSON)
        self.shaders[material_dict["name"]] = Material(
            albedo=material_dict["albedo"],
            roughness=material_dict["roughness"],
            reflectiveness=material_dict["reflectiveness"],
            vertex_shader= default_vertex_shader if not "vertex" in material_dict else material_dict["vertex"],
            fragment_shader= default_fragment_shader if not "fragment" in material_dict else material_dict["fragment"]
        )

#albedo: tuple = (1.0, 1.0, 1.0), roughness: float = 0.5, reflectiveness: float = 0.5

    def remove_shader(self, shader_name: str):
        # Remove a shader by name
        self.shaders.pop(shader_name)

    def get_shader(self, shader_name: str):
        # Set a specific shader program as active
        if shader_name in self.shaders:
            return self.shaders[shader_name]
            #material.set_material_properties()
