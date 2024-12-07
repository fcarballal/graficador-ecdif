import numpy as np

# Hace más suave los colores. Con 0 queda todo negro.
ATENUACION_COLOR = 1


#########################
# CONDICIONES INICIALES #
#########################

# Se cargan en las listas x e y. 
# Si x = [x_i], y = [y_i], entonces las condiciones iniciales son {(x_i,y_i)}.
# Por ejemplo, para que sean (0,0), (1,0) y (0,1), habría que hacer x = [0,1,0]; y = [0,0,1].
# Lo que hay por defecto pone condiciones iniciales en la grilla de coordenadas enteras entre -4 y 4
# (recordar que la función range es con < para el extremo de arriba).
def posiciones_iniciales():
    x = []
    y = []
    for i in range(-4, 5):
        for j in range(-4, 5):
            x.append(i)
            y.append(j)
    return x,y

########################
# ECUACIÓN DIFERENCIAL #
########################

# Parámetros de Van Der Pol (por si se decide usar esta ecuación diferencial)
MU = 2
A = 13
OMEGA = 4

# Función de la ecuación diferencial.
# Lo que se retorna son x' e y' en ese orden, es decir, cuando dice "return dx, dy", significa que dx es x', y que dy es y'.
# Si se cambia, todas las funciones no lineales que se usen (salvo productos, exponenciales y divisiones) deben ser de la biblioteca numpy.
# Eso es importante porque debe funcionar componente a componente en el caso de que x,y sean arreglos (vectores).
# Por ejemplo, para seno se debe usar np.sin(), para exponencial np.exp(), etc.
# Recordar que en python la exponencial es a**b.
def ec_dif(t,x,y):
    return  y, MU*(1-x*x)*y - x + A*np.sin(OMEGA*t)


################
# PINTAR FONDO #
################

# Lo de esta sección está para poder pintar el fondo de alguna forma que ayude a visualizar el flujo.
# La idea es que el color de cada punto puede depender del punto y del valor del flujo en ese punto.

# Si no se quiere pintar nada, poner esto en False.
PINTAR_FONDO = True

# Resolución del color de fondo.
# Como requiere muchas cuentas, según el procesador y la tarjeta gráfica puede ralentizar al programa.
# Bajar este número mejora el rendimiento (más fps).
RESOLUCION_FONDO = 300


#Funciones auxiliares para la función del color.

#Lo positivo va rojo y lo negativo azul. Intensidad dada por el valor absoluto.
def pos_neg(v):
    modulo = np.abs(v)
    color = modulo/(1 + modulo)
    rojo = np.heaviside(v,0)*color
    verde = 0*modulo
    azul = np.heaviside(-v,0)*color
    return rojo, verde, azul

#Intento fallido de abanico de colores, pero se ve divertido.
def psicodelico(v):
    rojo = np.sin(v)
    verde = np.sin(v/2)
    azul = np.sin(v/3)
    return rojo, verde, azul

# Función para pintar el fondo en base a tiempo, posición y derivada.
# Cada color es un número entre 0 y 1, siendo 1 la máxima intensidad. >1 hace lo mismo que 1 y <0 lo mismo que 0.
# t es el tiempo, (x,y) es la posición del punto a pintar y (dx,dy) es el valor del flujo en ese punto,
# es decir, dx,dy = flujo_funcion(t,x,y).
# Salvo el primer parámetro, los otros van a ser arreglos de numpy, así que para modificarlo aplica lo mismo
# que para flujo_funcion (usar funciones de numpy).
def funcion_color(t, x, y, dx, dy):
    rojo, verde, azul = pos_neg(dy)
    return ATENUACION_COLOR*rojo, ATENUACION_COLOR*verde, ATENUACION_COLOR*azul


#Método numérico a usar para resolver.
#E_AD: Método de Euler hacia adelante
#H: Método de Heun
#SP: Usa el solver de Scipy
METODO_NUMERICO = "SP"


#Color de las soluciones
SOL_ROJO = 0
SOL_VERDE = 1
SOL_AZUL = 0


#Resolución de la ventana
SCREEN_WIDTH = 750
SCREEN_HEIGHT = 750


#Muestra las condiciones iniciales por esta cantidad de segundos antes de comenzar. Solo en Windows sé que funciona.
#Poner en 0 para que empiece de una.
RETRASO = 1


#Si se dibujan ejes y grilla o no
PINTAR_EJES = True
PINTAR_GRILLA = True

#Al ponerlo en True, en vez de pintar todo el eje, solo pone triángulos blancos en los enteros
EJES_CON_TRIANGULOS = False


#Cantidad de puntos que se pueden agregar haciendo click
# (pongo un tope para manejar los datos mejor más eficientemente)
PUNTOS_AGREGAR = 1000

#Escala inicial
ESCALA = 5

#Cantidad de triángulos en los que se descomponen los círculos
RES_CIRC = 30