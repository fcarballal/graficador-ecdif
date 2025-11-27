import numpy as np
import glfw
import glfw.GLFW as GLFW_CONSTANTS
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time
import math

from sols2DParams import *
from sols2DMetNum import *

################################
###### FUNCIONES GLOBALES ######
################################



def create_shader_program(vertex_filepath: str, fragment_filepath: str) -> int:
    vertex_module = create_shader_module(vertex_filepath, GL_VERTEX_SHADER)
    fragment_module = create_shader_module(fragment_filepath, GL_FRAGMENT_SHADER)

    shader = compileProgram(vertex_module, fragment_module)

    return shader

def create_shader_module(filepath: str, module_type: int) -> int:
    source_code = ""
    with open(filepath, "r") as file:
        source_code = file.readlines()
    
    return compileShader(source_code, module_type)

def triangulito(x, y, delta):
    return np.array((x - delta, y - delta, 0.0, ATENUACION_FONDO, ATENUACION_FONDO, ATENUACION_FONDO,
                     x + delta, y - delta, 0.0, ATENUACION_FONDO, ATENUACION_FONDO, ATENUACION_FONDO,
                     x, y + delta, 0.0, ATENUACION_FONDO, ATENUACION_FONDO, ATENUACION_FONDO),
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
        self.colores = np.ones(self.x.size)
        for i in range(self.x.size):
            self.colores[i] = self.colores[i] + i%9
        self.color_actual = 1

        #Estructura para el fondo
        grilla = np.linspace(-1,1,RESOLUCION_FONDO, dtype= np.float32)
        self.datos_fondo = np.zeros((RESOLUCION_FONDO**2, 6), dtype= np.float32)
        self.datos_fondo[:,0] = np.repeat(grilla, RESOLUCION_FONDO)
        self.datos_fondo[:,1] = np.tile(grilla, RESOLUCION_FONDO)
        datos = np.zeros(6*(RESOLUCION_FONDO - 1)**2, dtype = np.uint32)
        iter = 0
        for i in range(RESOLUCION_FONDO - 1):
            for j in range(RESOLUCION_FONDO - 1):
                actual = RESOLUCION_FONDO*i + j
                datos[iter] = actual
                datos[iter+1] = actual + RESOLUCION_FONDO + 1
                datos[iter+2] = actual + RESOLUCION_FONDO
                datos[iter+3] = actual
                datos[iter+4] = actual + 1
                datos[iter+5] = actual + RESOLUCION_FONDO + 1
                iter = iter + 6
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, datos.nbytes, datos, GL_STATIC_DRAW)
        self.elems_fondo = datos
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
                           "m_1":True,
                           "sp":True,
                           "l":True,
                           "k":True}
        self.pausa = True

        self.rastros = False
        self.rastros_datos = 0
        self.cant_lineas = PUNTOS_POR_SEG*DURACION
        self.linea_actual = 0
        self.puntos_rastro = 0

        self.estado_ciclo = 0
        self.dibujo_ciclo = False
        self.ciclo_x = []
        self.ciclo_y = []
        self.ciclo_datos = 0
        self.ciclo_color = 1
        self.area = 0

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
        glBindVertexArray(self.VAO)
        self.shader = create_shader_program("shaders/vertex.txt", "shaders/fragment.txt")
        self.shaderT = create_shader_program("shaders/vertex.txt", "shaders/fragment2.txt")
        


        

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

    #Coordenada x en pantalla   
    def scx(self, x):
        return (x-self.camara_x)/self.escala   

    #Coordenada y en pantalla
    def scy(self, y):
        return (y - self.camara_y)/self.escala

    def procesar_entrada(self):
        if self.estado_ciclo == 0 or self.estado_ciclo == 2:
            global g_escala
            # Ajusto la escala con la variable global que se modifica con interrupciones
            self.escala = g_escala
            
            #Procesamiento de input
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_SPACE) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["sp"]:
                if self.pausa:
                    self.pausa = False
                    self.desfazaje = self.tiempoR - self.tiempo
                    self.deltaT = 0
                else:
                    self.pausa = True
                    self.tiempo = self.tiempoViejo
                self.espero_tecla["sp"] = False
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_SPACE) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["sp"]:
                self.espero_tecla["sp"] = True

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
                g_escala = ESCALA
                self.espero_tecla["c"] = False
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_C) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["c"]:
                self.espero_tecla["c"] = True
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_1) == GLFW_CONSTANTS.GLFW_PRESS:
                self.color_actual = 1
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_2) == GLFW_CONSTANTS.GLFW_PRESS:
                self.color_actual = 2
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_3) == GLFW_CONSTANTS.GLFW_PRESS:
                self.color_actual = 3
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_4) == GLFW_CONSTANTS.GLFW_PRESS:
                self.color_actual = 4
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_5) == GLFW_CONSTANTS.GLFW_PRESS:
                self.color_actual = 5
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_6) == GLFW_CONSTANTS.GLFW_PRESS:
                self.color_actual = 6
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_7) == GLFW_CONSTANTS.GLFW_PRESS:
                self.color_actual = 7
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_8) == GLFW_CONSTANTS.GLFW_PRESS:
                self.color_actual = 8
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_9) == GLFW_CONSTANTS.GLFW_PRESS:
                self.color_actual = 9    
            if glfw.get_mouse_button(self.window, GLFW_CONSTANTS.GLFW_MOUSE_BUTTON_1) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["m_1"]:
                if self.cant_puntos < self.x.size:
                    mouse_x, mouse_y  =glfw.get_cursor_pos(self.window)
                    mouse_x = (mouse_x/SCREEN_WIDTH)*2 - 1 #Lo centro
                    mouse_y = 1 - (mouse_y/SCREEN_HEIGHT)*2 #Lo centro
                    self.x[self.cant_puntos] = self.camara_x + self.escala*mouse_x
                    self.y[self.cant_puntos] = self.camara_y + self.escala*mouse_y
                    self.colores[self.cant_puntos] = self.color_actual
                    self.cant_puntos = self.cant_puntos + 1
                    self.puntos_agregados = self.puntos_agregados + 1
                self.espero_tecla["m_1"] = False
            if glfw.get_mouse_button(self.window, GLFW_CONSTANTS.GLFW_MOUSE_BUTTON_1) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["m_1"]:
                self.espero_tecla["m_1"] = True
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_BACKSPACE) == GLFW_CONSTANTS.GLFW_PRESS:
                self.cant_puntos = 0
                self.rastros = False
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_L) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["l"]:
                if self.rastros:
                    self.rastros = False
                elif self.pausa and self.cant_puntos > 0:
                    self.rastros = True
                    self.puntos_rastro = self.cant_puntos
                    self.linea_actual = 0
                    self.rastros_datos = np.zeros((self.cant_puntos,self.cant_lineas,6),dtype=np.float32)
                    for i in range(self.cant_puntos): #Poner los colores por solución
                        (rojo,verde,azul) = COLORES[self.colores[i]]
                        self.rastros_datos[i,:,3] = rojo
                        self.rastros_datos[i,:,4] = verde
                        self.rastros_datos[i,:,5] = azul
                    self.elems_rastro = np.zeros(self.puntos_rastro*self.cant_lineas*2, dtype = np.uint32) #Elementos
                    for i in range(self.cant_lineas-1):
                        for j in range(self.puntos_rastro):
                            self.elems_rastro[2*self.puntos_rastro*i + 2*j] = self.cant_lineas*j + i
                            self.elems_rastro[2*self.puntos_rastro*i + 2*j + 1] = self.cant_lineas*j + i + 1
                self.espero_tecla["l"] = False
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_L) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["l"]:
                self.espero_tecla["l"] = True

            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_K) == GLFW_CONSTANTS.GLFW_PRESS and self.espero_tecla["k"]:
                if self.estado_ciclo == 0 and self.pausa:
                    self.ciclo_x = []
                    self.ciclo_y = []
                    self.dibujo_ciclo = False
                    self.estado_ciclo = 1
                elif self.estado_ciclo == 2:
                    self.estado_ciclo = 0
                   
                self.espero_tecla["k"] = False
            if glfw.get_key(self.window, GLFW_CONSTANTS.GLFW_KEY_K) == GLFW_CONSTANTS.GLFW_RELEASE and not self.espero_tecla["k"]:
                self.espero_tecla["k"] = True
        elif self.estado_ciclo == 1:
            if glfw.get_mouse_button(self.window, GLFW_CONSTANTS.GLFW_MOUSE_BUTTON_1) == GLFW_CONSTANTS.GLFW_PRESS:
                self.dibujo_ciclo = True
                self.ciclo_color = self.color_actual
                mouse_x, mouse_y  =glfw.get_cursor_pos(self.window)
                mouse_x = (mouse_x/SCREEN_WIDTH)*2 - 1 #Lo centro
                mouse_y = 1 - (mouse_y/SCREEN_HEIGHT)*2 #Lo centro
                x = self.camara_x + self.escala*mouse_x
                y = self.camara_y + self.escala*mouse_y
                if not self.ciclo_x or (self.ciclo_x[-1] - x)**2 + (self.ciclo_y[-1] - y)**2 > EPSILON**2/4:
                    self.ciclo_x.append(x)
                    self.ciclo_y.append(y)

            if glfw.get_mouse_button(self.window, GLFW_CONSTANTS.GLFW_MOUSE_BUTTON_1) == GLFW_CONSTANTS.GLFW_RELEASE and self.dibujo_ciclo == True:
                self.ciclo_x = np.array(self.ciclo_x, dtype=np.float64)
                self.ciclo_y = np.array(self.ciclo_y, dtype=np.float64)
                (rojo,verde,azul) = COLORES[self.ciclo_color]
                self.ciclo_datos = np.zeros(self.ciclo_x.size*6,dtype=np.float32)
                self.ciclo_datos[0:self.ciclo_x.size*6:6] = self.scx(self.ciclo_x)
                self.ciclo_datos[1:self.ciclo_x.size*6:6] = self.scy(self.ciclo_y)
                self.ciclo_datos[3:self.ciclo_x.size*6:6] = rojo
                self.ciclo_datos[4:self.ciclo_x.size*6:6] = verde
                self.ciclo_datos[5:self.ciclo_x.size*6:6] = azul
                self.estado_ciclo = 2
                self.espero_tecla["m_1"] = True


    def fisica(self,tiempoViejo, tiempo, deltaT):
        if self.mov_x != 0: self.camara_x = self.camara_x + self.mov_x*self.escala*deltaT    #Muevo la cámara si es necesario
        if self.mov_y != 0: self.camara_y = self.camara_y + self.mov_y*self.escala*deltaT

        #Actualización de posiciones y rastro
        if not self.pausa:
            if self.rastros and self.linea_actual < self.cant_lineas and time.time()- self.timer_rastro > 1/PUNTOS_POR_SEG:
                self.rastros_datos[:,self.linea_actual,0] = self.x[0:self.puntos_rastro]
                self.rastros_datos[:,self.linea_actual,1] = self.y[0:self.puntos_rastro]
                self.linea_actual = self.linea_actual + 1
                self.timer_rastro = time.time()
            self.x[0:self.cant_puntos] , self.y[0:self.cant_puntos] = paso(self.x[0:self.cant_puntos], self.y[0:self.cant_puntos], tiempoViejo, deltaT)
            if self.estado_ciclo == 2:
                self.area = 0
                self.ciclo_x, self.ciclo_y = paso(self.ciclo_x, self.ciclo_y, tiempoViejo, deltaT)
                i = 0
                while i < self.ciclo_x.size - 1: #Ajustar según separación
                    dist_i2 = (self.ciclo_x[i+1] - self.ciclo_x[i])**2 + (self.ciclo_y[i+1] - self.ciclo_y[i])**2 
                    if dist_i2 > EPSILON**2:
                        self.area = self.area + (self.ciclo_x[i+1] - self.ciclo_x[i])*(self.ciclo_y[i]+self.ciclo_y[i+1])/2
                        self.ciclo_x = np.insert(self.ciclo_x, i+1, (self.ciclo_x[i]+self.ciclo_x[i+1])/2)
                        self.ciclo_y = np.insert(self.ciclo_y, i+1, (self.ciclo_y[i]+self.ciclo_y[i+1])/2)
                        i = i + 2
                    elif dist_i2 < EPSILON**2/100:
                        self.ciclo_x = np.delete(self.ciclo_x,i+1)
                        self.ciclo_y = np.delete(self.ciclo_y, i+1)
                    else:
                        self.area = self.area + (self.ciclo_x[i+1] - self.ciclo_x[i])*(self.ciclo_y[i]+self.ciclo_y[i+1])/2
                        i = i+1
                dist_pu = (self.ciclo_x[-1] - self.ciclo_x[0])**2 + (self.ciclo_y[-1] - self.ciclo_y[0])**2
                if dist_pu > EPSILON**2:
                    self.ciclo_x = np.append(self.ciclo_x, (self.ciclo_x[0]+self.ciclo_x[-1])/2)
                    self.ciclo_y = np.append(self.ciclo_y, (self.ciclo_y[0]+self.ciclo_y[-1])/2)
                elif dist_pu < EPSILON**2/100:
                    self.ciclo_x = np.delete(self.ciclo_x,-1)
                    self.ciclo_y = np.delete(self.ciclo_y, -1)
                self.area = self.area + (self.ciclo_x[0] - self.ciclo_x[-1])*(self.ciclo_y[0]+self.ciclo_y[-1])/2

                (rojo,verde,azul) = COLORES[self.ciclo_color]
                self.ciclo_datos = np.zeros(self.ciclo_x.size*6,dtype=np.float32)
                self.ciclo_datos[0:self.ciclo_x.size*6:6] = self.scx(self.ciclo_x)
                self.ciclo_datos[1:self.ciclo_x.size*6:6] = self.scy(self.ciclo_y)
                self.ciclo_datos[3:self.ciclo_x.size*6:6] = rojo
                self.ciclo_datos[4:self.ciclo_x.size*6:6] = verde
                self.ciclo_datos[5:self.ciclo_x.size*6:6] = azul
            

    def pintar_fondo(self, t):

        if PINTAR_FONDO:
            dx, dy = ec_dif(t, self.escala*self.datos_fondo[:,0] + self.camara_x, self.escala*self.datos_fondo[:,1] + self.camara_y)
            rojo, verde, azul = funcion_color(t, self.escala*self.datos_fondo[:,0] + self.camara_x, self.escala*self.datos_fondo[:,1] + self.camara_y, dx, dy)
            self.datos_fondo[:,3] = rojo
            self.datos_fondo[:,4] = verde
            self.datos_fondo[:,5] = azul
            
            grilla = self.datos_fondo.flatten()
            glBufferData(GL_ARRAY_BUFFER, grilla.nbytes, grilla, GL_STATIC_DRAW)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.elems_fondo.nbytes, self.elems_fondo, GL_STATIC_DRAW)
            glDrawElements(GL_TRIANGLES, 6*(RESOLUCION_FONDO - 1)**2, GL_UNSIGNED_INT, ctypes.c_void_p(0))

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
            (rojo,verde,azul) = COLORES[self.colores[i]]
            if COLOR_UNICO:
                (rojo,verde,azul) = (SOL_ROJO,SOL_VERDE,SOL_AZUL)

            positions = circulo(self.scx(x), self.scy(y), 0.015, rojo,verde,azul, RES_CIRC)
            glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
            glDrawArrays(GL_TRIANGLE_FAN, 0, RES_CIRC + 1)

            positions = circunferencia(self.scx(x), self.scy(y), 0.015, 0, 0, 0, RES_CIRC)
            glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
            glDrawArrays(GL_LINE_STRIP, 0, RES_CIRC)

    def dibujar_rastros(self):
            if self.linea_actual > 1:
                datosPintar = np.copy(self.rastros_datos)
                datosPintar[:,:,0] = self.scx(datosPintar[:,:,0])
                datosPintar[:,:,1] = self.scy(datosPintar[:,:,1])
                glBufferData(GL_ARRAY_BUFFER, self.rastros_datos.nbytes, datosPintar.flatten(), GL_STATIC_DRAW)
                glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.elems_rastro.nbytes, self.elems_rastro, GL_STATIC_DRAW)
                glDrawElements(GL_LINES, 2*self.puntos_rastro*(self.linea_actual - 1), GL_UNSIGNED_INT, ctypes.c_void_p(0))

    def dibujar_ciclo(self):
        self.ciclo_datos[0:self.ciclo_x.size*6:6] = self.scx(self.ciclo_x)
        self.ciclo_datos[1:self.ciclo_x.size*6:6] = self.scy(self.ciclo_y)
        glBufferData(GL_ARRAY_BUFFER, self.ciclo_datos.nbytes, self.ciclo_datos, GL_STATIC_DRAW)
        glDrawArrays(GL_LINE_LOOP, 0, self.ciclo_x.size)

    def run(self):

        self.tiempoR = time.time() #Los con R son tiempo real
        self.tiempoViejoR = self.tiempoR
        self.desfazaje = self.tiempoR
        self.tiempo = 0            #Los sin R son tiempo de la ecuación
        self.tiempoViejo = 0
        
        self.timer_rastro = time.time()
        self.timerfps = self.tiempoR
        fps = 0
        self.deltaT = 0

        while not glfw.window_should_close(self.window):
            self.tiempoR = time.time()
            self.deltaT = self.tiempoR - self.tiempoViejoR
            if not self.pausa:
                self.tiempo = self.tiempoR - self.desfazaje
                self.tiempoViejo = self.tiempoViejoR - self.desfazaje


            self.procesar_entrada() #Proceso el input del teclado y el ratón. También muevo la cámara

            self.fisica(self.tiempoViejo, self.tiempo, self.deltaT) #Las cosas se mueven

            glClear(GL_COLOR_BUFFER_BIT) #Dibujo. Cambiando el orden cambia cual queda arriba
            self.pintar_fondo(self.tiempo)
            self.dibujar_ejes()
            self.dibujar_soluciones()
            if self.rastros : self.dibujar_rastros()
            if self.estado_ciclo == 2 : self.dibujar_ciclo()
            
            if time.time() - self.timerfps < 1:  fps = fps + 1 #FPS      
            else:
                texto = "Frames por segundo (fps) : " + str(fps) +". Separación ejes: " + str(10**math.floor(np.log10(self.escala/2)))
                if self.estado_ciclo == 2:
                    texto = texto + " Área: " + str(np.abs(self.area))
                glfw.set_window_title(self.window, texto)
                self.timerfps = time.time()
                if fps < 1:
                    self.estado_ciclo = 0
                fps = 0

            self.tiempoViejoR = self.tiempoR

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





#Para colapsar puntos que se tocan en el ciclo
"""i = 0
                while i < self.ciclo_x.size - 1: #Colapsar puntos que se tocan
                    j = 0
                    while j < i:
                        dist_ij2 = (self.ciclo_x[i] - self.ciclo_x[j])**2 + (self.ciclo_y[i] - self.ciclo_y[j])**2
                        if dist_ij2 < EPSILON**2/10000:
                            self.ciclo_x = np.concatenate(self.ciclo_x[:j], self.ciclo_x[i:])
                            self.ciclo_y = np.concatenate(self.ciclo_y[:j], self.ciclo_y[i:])
                            j = i+j
                        else:
                            j = j + 1
                    if j == i:
                        i = i + 1
                    else:
                        i = j - i + 1 """