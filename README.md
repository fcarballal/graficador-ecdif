Graficador de ecuaciones diferenciales ordinarias.

Hay que tener python y los siguientes paquetes:
numpy, scipy, PyOpenGL, glfw.

Para instalar los paquetes, alcanza ejecutar lo siguiente en una terminal (desde la carpeta donde está el archivo "requirements.txt"):
pip install -r requirements.txt

O alternativamente:
pip install numpy, scipy, PyOpenGL, glfw




Se ejecuta el archivo flujo2D.py

En el archivo flujo2DParams.py se puede modificar la ecuación diferencial, las condiciones iniciales, cómo se pinta el fondo y otros parámetros.

CONTROLES:

- barra espaciadora : pausa/continuar (comienza en pausa)
- tecla "a" : mover hacia la izquierda
- tecla "d" : mover hacia la derecha
- tecla "w" : mover hacia arriba
- tecla "s" : mover hacia abajo
- scroll del mouse : alejar o acercar
- tecla "c" : centrar y volver a la escala inicial
- click botón principal del mouse : agregar una solución nueva en ese punto
- dígitos del 1 al 9 : cambiar el color de las soluciones agregadas
- tecla "l" : activar o desactivar rastros (solo se puede activar en pausa)
