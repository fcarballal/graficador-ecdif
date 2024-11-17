import numpy as np
from scipy.integrate import odeint
import glfw
import glfw.GLFW as GLFW_CONSTANTS
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time
import math

from flujo2DParams import *

################################
###### FUNCIONES GLOBALES ######
################################

#Esta función es el método numérico para dar un paso en la solución de la ecuación diferencial.
def paso(x, y, t, deltaT, met=METODO_NUMERICO):
    if met == "E_AD":
        der_x, der_y = flujo_funcion(x,y, t)
        return  x + deltaT*der_x, y + deltaT*der_y
    elif met == "H":
        der_x, der_y = flujo_funcion(x,y,t)
        x1 = x + deltaT*der_x
        y1 = y + deltaT*der_y
        der_x1, der_y1 = flujo_funcion(x1, y1, t + deltaT)
        der_xf = (der_x + der_x1)/2
        der_yf = (der_y + der_y1)/2
        return x + deltaT*der_xf, y + deltaT*der_yf
    elif met == "SP":
        def func(y,t):
            x1, y1 = flujo_funcion(y[0],y[1], t)
            return [x1,y1]
        for i in range(x.size):    
            y0 = [x[i],y[i]]
            tiempos = [t, t + deltaT]
            sol = odeint(func, y0, tiempos)
            x[i] = sol[1,0]
            y[i] = sol[1,1]
        return x,y


def create_shader_program(vertex_filepath: str, fragment_filepath: str) -> int:
    vertex_module = create_shader_module(vertex_filepath, GL_VERTEX_SHADER)
    fragment_module = create_shader_module(fragment_filepath, GL_FRAGMENT_SHADER)

    shader = compileProgram(vertex_module, fragment_module)

    if not MAC:
        glDeleteShader(vertex_module)
        glDeleteShader(fragment_module)

    return shader

def create_shader_module(filepath: str, module_type: int) -> int:
    source_code = ""
    with open(filepath, "r") as file:
        source_code = file.readlines()
    
    return compileShader(source_code, module_type)

def triangulito(x, y, delta):
    return np.array((x - delta, y - delta, 0.0, ATENUACION_COLOR, ATENUACION_COLOR, ATENUACION_COLOR,
                     x + delta, y - delta, 0.0, ATENUACION_COLOR, ATENUACION_COLOR, ATENUACION_COLOR,
                     x, y + delta, 0.0, ATENUACION_COLOR, ATENUACION_COLOR, ATENUACION_COLOR),
                     dtype = np.float32)

def circulo(xc, yc, r, rojo, verde, azul, disc_circ):
    grilla = np.linspace(0, 2*np.pi, disc_circ)
    x = xc + r*np.cos(grilla)
    y = yc + r*np.sin(grilla)
    res = np.zeros((disc_circ + 1,6), dtype = np.float32)
    res[0,0] = xc
    res[0,1] = yc
    res[1:,0] = x
    res[1:,1] = y
    res[:,3] = rojo
    res[:,4] = verde
    res[:,5] = azul
    return res.flatten()

def circunferencia(xc, yc, r, rojo, verde, azul, disc_circ):
    grilla = np.linspace(0, 2*np.pi, disc_circ)
    res = np.zeros((disc_circ,6), dtype = np.float32)
    res[:,0] = xc + r*np.cos(grilla)
    res[:,1] = yc + r*np.sin(grilla)
    res[:,3] = rojo
    res[:,4] = verde
    res[:,5] = azul
    return res.flatten()


g_escala = ESCALA
def event_scroll(win, x, y):
    global g_escala
    g_escala = g_escala*(1-y/8)


################################
############ CLASE #############
################################

class App:


    def __init__(self):
        self.initialize_glfw()
        self.initialize_opengl()
        
        #Cargar los datos iniciales en los vectores self.x, self.y
        x, y = posiciones_iniciales()
        self.cant_puntos = len(x)
        for i in range(PUNTOS_AGREGAR):
            x.append(0)
            y.append(0)
        self.x = np.array(x, dtype = np.float64)
        self.y = np.array(y, dtype = np.float64)

        #Estructura para el fondo
        grilla = np.linspace(-1,1,SEPARACION_FONDO, dtype= np.float32)
        self.datos_fondo = np.zeros((SEPARACION_FONDO**2, 6), dtype= np.float32)
        self.datos_fondo[:,0] = np.repeat(grilla, SEPARACION_FONDO)
        self.datos_fondo[:,1] = np.tile(grilla, SEPARACION_FONDO)
        datos = np.zeros(6*(SEPARACION_FONDO - 1)**2, dtype = np.uint32)
        iter = 0
        for i in range(SEPARACION_FONDO - 1):
            for j in range(SEPARACION_FONDO - 1):
                actual = SEPARACION_FONDO*i + j
                datos[iter] = actual
                datos[iter+1] = actual + SEPARACION_FONDO + 1
                datos[iter+2] = actual + SEPARACION_FONDO
                datos[iter+3] = actual
                datos[iter+4] = actual + 1
                datos[iter+5] = actual + SEPARACION_FONDO + 1
                iter = iter + 6
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, datos.nbytes, datos, GL_STATIC_DRAW)

        self.escala = g_escala
        self.camara_x = 0
        self.camara_y = 0
        self.mov_x = 0
        self.mov_y = 0
        self.puntos_agregados = 0
        self.espero_tecla = {"a":True,
                           "s":True,
                           "d":True,
                           "w":True,
                           "c":True,
                           "m_1":True}
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable( GL_BLEND )
        glUseProgram(self.shader)
        glBindVertexArray(self.VAO)


    def initialize_glfw(self):
        glfw.init()
        glfw.window_hint(
            GLFW_CONSTANTS.GLFW_OPENGL_PROFILE,
            GLFW_CONSTANTS.GLFW_OPENGL_CORE_PROFILE
        )
        glfw.window_hint(GLFW_CONSTANTS.GLFW_CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(GLFW_CONSTANTS.GLFW_CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(GLFW_CONSTANTS.GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE)
        self.window = glfw.create_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Graficador", None, None)
        glfw.make_context_current(self.window)

        glfw.set_scroll_callback(self.window, event_scroll)
        #glfw.set_input_mode(self.window, GLFW_CONSTANTS.GLFW_STICKY_KEYS,GL_TRUE)
    
    def initialize_opengl(self):
        glClearColor(0.0,0.0,0.0,0.0)
        self.VAO = glGenVertexArrays(1)
        self.shader = create_shader_program("shaders/vertex.txt", "shaders/fragment.txt")
        self.shaderT = create_shader_program("shaders/vertex.txt", "shaders/fragment2.txt")
        


        glBindVertexArray(self.VAO)

        pos_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, pos_buffer)
        self.pos_buffer = pos_buffer

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        elm_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,elm_buffer)
        self.elm_buffer = elm_buffer
        
        

    def procesar_entrada(self):
        # Ajusto la escala con la variable global que se modifica con interrupciones
        self.escala = g_escala
        
        #Procesamiento de input
        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_A) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["a"]:
            self.mov_x = self.mov_x - 1
            self.espero_tecla["a"] = False
        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_D) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["d"]:
            self.mov_x = self.mov_x + 1
            self.espero_tecla["d"] = False
        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_S) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["s"]:
            self.mov_y = self.mov_y - 1
            self.espero_tecla["s"] = False
        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_W) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["w"]:
            self.mov_y = self.mov_y + 1
            self.espero_tecla["w"] = False
        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_A) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["a"]:
            self.mov_x = self.mov_x + 1
            self.espero_tecla["a"] = True
        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_D) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["d"]:
            self.mov_x = self.mov_x - 1
            self.espero_tecla["d"] = True
        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_S) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["s"]:
            self.mov_y = self.mov_y + 1
            self.espero_tecla["s"] = True
        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_W) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["w"]:
            self.mov_y = self.mov_y - 1
            self.espero_tecla["w"] = True

        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_C) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["c"]:
            self.camara_x = 0
            self.camara_y = 0
            self.espero_tecla["c"] = False
        if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_C) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["c"]:
            self.espero_tecla["c"] = True

        if glfw.get_mouse_button(self.window, GLFW_CONSTANTS.GLFW_MOUSE_BUTTON_1) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["m_1"]:
            mouse_x, mouse_y  =glfw.get_cursor_pos(self.window)
            mouse_x = (mouse_x/SCREEN_WIDTH)*2 - 1 #Lo centro
            mouse_y = 1 - (mouse_y/SCREEN_HEIGHT)*2 #Lo centro
            self.x[self.cant_puntos] = self.camara_x + self.escala*mouse_x
            self.y[self.cant_puntos] = self.camara_y + self.escala*mouse_y
            self.cant_puntos = self.cant_puntos + 1
            self.puntos_agregados = self.puntos_agregados + 1
            self.espero_tecla["m_1"] = False
        if glfw.get_mouse_button(self.window, GLFW_CONSTANTS.GLFW_MOUSE_BUTTON_1) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["m_1"]:
            self.espero_tecla["m_1"] = True


    def pintar_fondo(self, t):

        if PINTAR_FONDO:
            dx, dy = flujo_funcion(self.escala*self.datos_fondo[:,0] + self.camara_x, self.escala*self.datos_fondo[:,1] + self.camara_y, t)
            rojo, verde, azul = funcion_color(self.escala*self.datos_fondo[:,0] + self.camara_x, self.escala*self.datos_fondo[:,1] + self.camara_y, dx, dy)
            self.datos_fondo[:,3] = rojo
            self.datos_fondo[:,4] = verde
            self.datos_fondo[:,5] = azul
            
            grilla = self.datos_fondo.flatten()
            glBufferData(GL_ARRAY_BUFFER, grilla.nbytes, grilla, GL_STATIC_DRAW)
            glDrawElements(GL_TRIANGLES, 6*(SEPARACION_FONDO - 1)**2, GL_UNSIGNED_INT, ctypes.c_void_p(0))

    def dibujar_ejes(self):
        if PINTAR_EJES:
            if EJES_CON_TRIANGULOS:
                for i in range(0,np.floor(self.escala)):
                    positions1 = triangulito(i/ESCALA,0,0.01)
                    positions2 = triangulito(-i/ESCALA,0,0.01)
                    positions3 = triangulito(0,i/ESCALA,0.01)
                    positions4 = triangulito(0,-i/ESCALA,0.01)
                    positions = np.concatenate((positions1, positions2, positions3, positions4))
                    glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
                    glDrawArrays(GL_TRIANGLES, 0, 12)
            else:
                glUseProgram(self.shaderT)
                colorCentro = 1
                color = 0.5
                epsilon_x = 1/SCREEN_WIDTH
                epsilon_y = 1/SCREEN_HEIGHT
                lineas = np.array([
                [-1,-self.camara_y/self.escala,0,colorCentro,colorCentro,colorCentro],
                [1,-self.camara_y/self.escala,0,colorCentro,colorCentro,colorCentro],
                [-self.camara_x/self.escala,-1,0,colorCentro,colorCentro,colorCentro],
                [-self.camara_x/self.escala,1,0,colorCentro,colorCentro,colorCentro],
                [-1,-self.camara_y/self.escala+epsilon_y,0,colorCentro,colorCentro,colorCentro],
                [1,-self.camara_y/self.escala+epsilon_y,0,colorCentro,colorCentro,colorCentro],
                [-self.camara_x/self.escala+epsilon_x,-1,0,colorCentro,colorCentro,colorCentro],
                [-self.camara_x/self.escala+epsilon_x,1,0,colorCentro,colorCentro,colorCentro],
                [-1,-self.camara_y/self.escala-epsilon_y,0,colorCentro,colorCentro,colorCentro],
                [1,-self.camara_y/self.escala-epsilon_y,0,colorCentro,colorCentro,colorCentro],
                [-self.camara_x/self.escala-epsilon_x,-1,0,colorCentro,colorCentro,colorCentro],
                [-self.camara_x/self.escala-epsilon_x,1,0,colorCentro,colorCentro,colorCentro]], dtype=np.float32)
                glBufferData(GL_ARRAY_BUFFER, lineas.nbytes, lineas, GL_STATIC_DRAW)
                glDrawArrays(GL_LINES,0,12)
                if PINTAR_GRILLA:
                    ancho = math.floor(np.log10(self.escala/2))
                    escalaEjes = self.escala/(10**ancho)
                    for i in range(0,math.ceil(escalaEjes)+1):
                        d = i/escalaEjes
                        lineas = np.array([
                        [-1,d- (self.camara_y/(10**ancho) - np.floor(self.camara_y/(10**ancho)))/(self.escala/(10**ancho)), 0,color,color,color],
                        [1,d- (self.camara_y/(10**ancho) - np.floor(self.camara_y/(10**ancho)))/(self.escala/(10**ancho)), 0,color,color,color],
                        [-1,-d- (self.camara_y/(10**ancho) - np.floor(self.camara_y/(10**ancho)))/(self.escala/(10**ancho)), 0,color,color,color],
                        [1,-d- (self.camara_y/(10**ancho) - np.floor(self.camara_y/(10**ancho)))/(self.escala/(10**ancho)), 0,color,color,color],
                        [d - (self.camara_x/(10**ancho) - np.floor(self.camara_x/(10**ancho)))/(self.escala/(10**ancho)),-1,0,color,color,color],
                        [d- (self.camara_x/(10**ancho) - np.floor(self.camara_x/(10**ancho)))/(self.escala/(10**ancho)),1,0,color,color,color],
                        [-d- (self.camara_x/(10**ancho) - np.floor(self.camara_x/(10**ancho)))/(self.escala/(10**ancho)),-1,0,color,color,color],
                        [-d- (self.camara_x/(10**ancho) - np.floor(self.camara_x/(10**ancho)))/(self.escala/(10**ancho)),1,0,color,color,color]], dtype=np.float32)
                        glBufferData(GL_ARRAY_BUFFER, lineas.nbytes, lineas, GL_STATIC_DRAW)
                        glDrawArrays(GL_LINES,0,8)
                glUseProgram(self.shader)

    def dibujar_soluciones(self):
        for i in range(self.cant_puntos):
            x = self.x[i]
            y = self.y[i]

            positions = circulo((x-self.camara_x)/self.escala, (y - self.camara_y)/self.escala, 0.015, 0, ATENUACION_COLOR, 0, RES_CIRC)
            glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
            glDrawArrays(GL_TRIANGLE_FAN, 0, RES_CIRC + 1)

            positions = circunferencia((x-self.camara_x)/self.escala, (y - self.camara_y)/self.escala, 0.015, 0, 0, 0, RES_CIRC)
            glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
            glDrawArrays(GL_LINE_STRIP, 0, RES_CIRC)

    def run(self):

        if RETRASO > 0:
            glClear(GL_COLOR_BUFFER_BIT)
            self.pintar_fondo(0)
            self.dibujar_ejes()
            self.dibujar_soluciones()
            glfw.swap_buffers(self.window)
            time.sleep(RETRASO)

        desfazaje = time.time()
        tiempo = 0
        tiempoViejo = 0
        timerfps = desfazaje
        fps = 0

        while not glfw.window_should_close(self.window):
            tiempo = time.time() - desfazaje
            deltaT = tiempo - tiempoViejo

            self.procesar_entrada() #Proceso el input del teclado y el ratón. También muevo la cámara

            if self.mov_x != 0: self.camara_x = self.camara_x + self.mov_x*self.escala*deltaT    #Muevo la cámara si es necesario
            if self.mov_y != 0: self.camara_y = self.camara_y + self.mov_y*self.escala*deltaT

            #Actualización de posiciones
            self.x[0:self.cant_puntos] , self.y[0:self.cant_puntos] = paso(self.x[0:self.cant_puntos], self.y[0:self.cant_puntos], tiempoViejo, deltaT)
            
            glClear(GL_COLOR_BUFFER_BIT) #Dibujo
            self.pintar_fondo(tiempo)
            self.dibujar_ejes()
            self.dibujar_soluciones()
            
            if time.time() - timerfps < 1:  fps = fps + 1 #FPS      
            else:
                glfw.set_window_title(self.window, "Frames por segundo: " + str(fps) +". Separación ejes: " + str(10**math.floor(np.log10(self.escala/2))))
                timerfps = time.time()
                fps = 0

            tiempoViejo = tiempo

            glfw.swap_buffers(self.window)
            glfw.poll_events()

    def quit(self):

        glDeleteVertexArrays(1,(self.VAO,))
        glDeleteBuffers(2,(self.pos_buffer, self.elm_buffer))
        glDeleteProgram(self.shader)
        glfw.destroy_window(self.window)
        glfw.terminate()

my_app = App()
my_app.run()
my_app.quit()

