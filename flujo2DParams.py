import numpy as np

#Poner true si se ejecuta en una mac.
MAC = False

#Resolución de la ventana
SCREEN_WIDTH = 750
SCREEN_HEIGHT = 750

#Muestra las condiciones iniciales por esta cantidad de segundos antes de comenzar.
#Poner en 0 para que empiece de una.
RETRASO = 1

#Si se pinta el fondo con colores o no
PINTAR_FONDO = True

#Tamaño de la grilla con la que se pinta el fondo. Cuanto mayor, mejor resolución y peor rendimiento
SEPARACION_FONDO = 300

PINTAR_EJES = True
PINTAR_GRILLA = True

#Al ponerlo en True, en vez de pintar todo el eje, solo pone triángulos blancos en los enteros
EJES_CON_TRIANGULOS = False

#Cantidad de puntos que se pueden agregar haciendo click
PUNTOS_AGREGAR = 1000

# Hace más suave los colores. Con 0 queda todo negro.
ATENUACION_COLOR = 1

#Escala inicial
ESCALA = 5

#Cantidad de triángulos en los que se descomponen los círculos
RES_CIRC = 30

#Posiciones iniciales
def posiciones_iniciales():
    x = []
    y = []
    for i in range(-4, 5):
        for j in range(-4, 5):
            x.append(i)
            y.append(j)
    return x,y



#Parámetros de Van Der Pol
MU = 1
A = 3
OMEGA = 3


#Función de la ecuación diferencial. Si se cambia, todas las funciones no lineales que se usen deben ser de la biblioteca numpy.
#Eso es importante porque debe funcionar componente a componente en el caso de que x,y sean arreglos (vectores).
def flujo_funcion(x,y,t):
    return  np.copy(y) ,MU*(1-x*x)*y - x + A*np.sin(OMEGA*t)


#Función para pintar el fondo en base a posición y derivada. Cada color es un número entre 0 y 1.
def funcion_color(x, y, dx, dy):
    ady = np.abs(dy)
    color = ady/(1 + ady)
    rojo = np.heaviside(dy,0)*color
    verde = 0*ady
    azul = np.heaviside(-dy,0)*color
    return ATENUACION_COLOR*rojo, ATENUACION_COLOR*verde, ATENUACION_COLOR*azul


#Método numérico a usar para resolver.
#E_AD: Método de Euler hacia adelante
#H: Método de Heun
#SP: Usa el solver de Scipy
METODO_NUMERICO = "SP"
