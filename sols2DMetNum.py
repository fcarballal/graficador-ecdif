from sols2DParams import *
from scipy.integrate import odeint



#Esta función es el método numérico para dar un paso en la solución de la ecuación diferencial.
def paso(x, y, t, deltaT, met=METODO_NUMERICO):
    if met == "E_AD":
        der_x, der_y = ec_dif(t, x,y)
        return  x + deltaT*der_x, y + deltaT*der_y
    
    elif met == "H":
        der_x, der_y = ec_dif(t, x,y)
        x1 = x + deltaT*der_x
        y1 = y + deltaT*der_y
        der_x1, der_y1 = ec_dif(t + deltaT, x1, y1)
        der_xf = (der_x + der_x1)/2
        der_yf = (der_y + der_y1)/2
        return x + deltaT*der_xf, y + deltaT*der_yf
    
    elif met == "SP":
        def func(y,t):
            x1, y1 = ec_dif(t, y[0],y[1])
            return [x1,y1]
        for i in range(x.size):    
            y0 = [x[i],y[i]]
            tiempos = [t, t + deltaT]
            sol = odeint(func, y0, tiempos)
            x[i] = sol[1,0]
            y[i] = sol[1,1]
        return x,y
