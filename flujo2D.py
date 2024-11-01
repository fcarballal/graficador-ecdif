import numpy as np
from scipy.integrate import odeint
import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time


#Si se pinta el fondo con colores o no
PINTAR_FONDO = True

#Tamaño de la grilla con la que se pinta el fondo. Cuanto mayor, mejor resolución y peor rendimiento
SEPARACION_FONDO = 300

PINTAR_EJES = True
PINTAR_GRILLA = True

#Al ponerlo en True, en vez de pintar todo el eje, solo pone triángulos blancos en los enteros
EJES_CON_TRIANGULOS = False



# Hace más suave los colores. Con 0 queda todo negro.
ATENUACION_COLOR = 1

#Lo que se ve en la ventana es  -ESCALA < x < ESCALA , -ESCALA < y < ESCALA
ESCALA = 5

#Cantidad de triángulos en los que se descomponen los círculos
RES_CIRC = 30

#Posición inicial
X0 = 0
Y0 = 0

#Parámetros de Van Der Pol
MU = 1
A = 1
OMEGA = 3




#Resolución de la pantalla
SCREEN_WIDTH = 750
SCREEN_HEIGHT = 750



#Función de la ecuación diferencial. Si se cambia, todas las funciones no lineales que se usen deben ser de la biblioteca numpy.
#Eso es importante porque debe funcionar componente a componente en el caso de que x,y sean arreglos (vectores).
def flujo_funcion(x,y,t):
    return  np.copy(y) ,MU*(1-x*x)*y - x + A*np.sin(OMEGA*t)


#Función que transforma el valor de la derivada en colores. Cada color es un número entre 0 y 1 (el verde está fijo en 0 por ahora).
def funcion_color(dx, dy):
    ady = np.abs(dy)
    color = ady/(1 + ady)
    rojo = np.heaviside(dy,0)*color
    verde = 0*ady
    azul = np.heaviside(-dy,0)*color
    return ATENUACION_COLOR*rojo, ATENUACION_COLOR*verde, ATENUACION_COLOR*azul



#Esta función es el método numérico para dar un paso en la solución de la ecuación diferencial. Los métodos son:
#E_AD: Método de Euler hacia adelante
#H: Método de Heun
#SP: Usa el solver de Scipy
#La pongo acá por si a alguien le interesa, pero para modificarla hay que entender de métodos numéricos
def paso(x, y, t, deltaT, met="SP"):

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
        y0 = [x,y]
        tiempos = [t, t + deltaT]
        sol = odeint(func, y0, tiempos)
        return sol[1,0], sol[1,1]

#Acá se elige el método numérico que se usa, de entre las opciones de la función "paso"
METODO_NUMERICO = "SP"



#####
#DE ACÁ PARA ABAJO RECOMIENDO NO MODIFICAR SALVO QUE ENTIENDAN COMO FUNCIONA OPENGL
#DE ACÁ PARA ABAJO RECOMIENDO NO MODIFICAR SALVO QUE ENTIENDAN COMO FUNCIONA OPENGL
#DE ACÁ PARA ABAJO RECOMIENDO NO MODIFICAR SALVO QUE ENTIENDAN COMO FUNCIONA OPENGL
#####



def create_shader_program(vertex_filepath: str, fragment_filepath: str) -> int:
    vertex_module = create_shader_module(vertex_filepath, GL_VERTEX_SHADER)
    fragment_module = create_shader_module(fragment_filepath, GL_FRAGMENT_SHADER)

    shader = compileProgram(vertex_module, fragment_module)

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
class App:


    def __init__(self):
        self.initialize_pygame()
        self.initialize_opengl()
        
        self.x = X0
        self.y = Y0

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



    def initialize_pygame(self):
        pg.init()
        pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.OPENGL|pg.DOUBLEBUF)
    
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
        
        

            


    def pintar_fondo(self, t):

        if PINTAR_FONDO:
            dx, dy = flujo_funcion(ESCALA*self.datos_fondo[:,0], ESCALA*self.datos_fondo[:,1], t)
            rojo, verde, azul = funcion_color(dx, dy)
            self.datos_fondo[:,3] = rojo
            self.datos_fondo[:,4] = verde
            self.datos_fondo[:,5] = azul
            
            grilla = self.datos_fondo.flatten()
            glBufferData(GL_ARRAY_BUFFER, grilla.nbytes, grilla, GL_STATIC_DRAW)
            glDrawElements(GL_TRIANGLES, 6*(SEPARACION_FONDO - 1)**2, GL_UNSIGNED_INT, ctypes.c_void_p(0))

    def ejes(self):
        if EJES_CON_TRIANGULOS:
            for i in range(0,np.floor(ESCALA)):
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
            lineas = np.array([
            [-1,0,0,colorCentro,colorCentro,colorCentro],
            [1,0,0,colorCentro,colorCentro,colorCentro],
            [0,-1,0,colorCentro,colorCentro,colorCentro],
            [0,1,0,colorCentro,colorCentro,colorCentro]], dtype=np.float32)
            glLineWidth(2)
            glBufferData(GL_ARRAY_BUFFER, lineas.nbytes, lineas, GL_STATIC_DRAW)
            glDrawArrays(GL_LINES,0,4)
            if PINTAR_GRILLA:
                for i in range(1,np.floor(ESCALA)):
                    d = i/ESCALA
                    lineas = np.array([
                    [-1,d,0,color,color,color],
                    [1,d,0,color,color,color],
                    [-1,-d,0,color,color,color],
                    [1,-d,0,color,color,color],
                    [d,-1,0,color,color,color],
                    [d,1,0,color,color,color],
                    [-d,-1,0,color,color,color],
                    [-d,1,0,color,color,color]], dtype=np.float32)
                    glLineWidth(1)
                    glBufferData(GL_ARRAY_BUFFER, lineas.nbytes, lineas, GL_STATIC_DRAW)
                    glDrawArrays(GL_LINES,0,8)
            glUseProgram(self.shader)

    def run(self):
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable( GL_BLEND )
        glUseProgram(self.shader)
        glBindVertexArray(self.VAO)

        

        tiempo0 = time.time()
        tiempo = tiempo0
        tiempoViejo = tiempo0

        timerfps = tiempo0
        fps = 0
        running = True
        while running:
            tiempo = time.time()
            deltaT = tiempo - tiempoViejo
            glClear(GL_COLOR_BUFFER_BIT)

            self.pintar_fondo(tiempo - tiempo0)
            if PINTAR_EJES:
                self.ejes()

            self.x , self.y = paso(self.x, self.y, tiempo - tiempo0, deltaT, met=METODO_NUMERICO)
            positions = circulo(self.x/ESCALA, self.y/ESCALA, 0.015, 0, ATENUACION_COLOR, 0, RES_CIRC)
            glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
            glDrawArrays(GL_TRIANGLE_FAN, 0, RES_CIRC + 1)

            positions = circunferencia(self.x/ESCALA, self.y/ESCALA, 0.015, 0, 0, 0, RES_CIRC)
            glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)
            glLineWidth(1.5)
            glDrawArrays(GL_LINE_STRIP, 0, RES_CIRC)
            

            if time.time() - timerfps < 1:
                fps = fps + 1
            else:
                pg.display.set_caption("Frames por segundo: " + str(fps))
                timerfps = time.time()
                fps = 0

            for event in pg.event.get():
                if (event.type == pg.QUIT):
                    running = False

            tiempoViejo = tiempo

            pg.display.flip()

    def quit(self):

        glDeleteVertexArrays(1,(self.VAO,))
        glDeleteBuffers(2,(self.pos_buffer, self.elm_buffer))
        glDeleteProgram(self.shader)
        pg.quit()

my_app = App()
my_app.run()
my_app.quit()

