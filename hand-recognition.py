import cv2
import mouse
import numpy as np
import threading
import time
from cvzone.HandTrackingModule import HandDetector

# Inicializar contadores para los estados de interés
click_count = 0
scroll_up_count = 0
scroll_down_count = 0


limit=150 #numero para delimitarel cuadro 

# Definir umbrales para activar las acciones
click_threshold = 3  # Se ejecutará el clic izquierdo después de detectar 4 veces
scroll_threshold = 2  # Se ejecutará el scroll después de detectar 4 veces

l_delay=0


def click_delay():
    global l_delay
    global click_thread
    time.sleep(1)
    l_delay = 0
    click_thread = threading.Thread(target=click_delay)
    
    
click_thread = threading.Thread(target=click_delay)

# Declarar el objeto de detección de manos
detector = HandDetector(detectionCon=0.9, maxHands=1)
cap = cv2.VideoCapture(0)
# Resolución de ancho y alto de la cámara
cam_w, cam_h = 640, 480
cap.set(3, cam_w)
cap.set(4, cam_h)

# Definir una lista para almacenar las coordenadas anteriores
prev_x = []
prev_y = []

# Número de muestras anteriores para considerar en el filtro de media móvil
n_samples = 9

# Función para aplicar el filtro de media móvil
def apply_moving_average(value, prev_values):
    prev_values.append(value)
    if len(prev_values) > n_samples:
        prev_values.pop(0)  # Eliminar el valor más antiguo si excede el número máximo de muestras
    return sum(prev_values) / len(prev_values)

while True:
    # Capturar el fotograma de la cámara
    success, img = cap.read()
    img = cv2.flip(img, 1)
    
    # Dibujar la región de movimiento de la mano
    cv2.rectangle(img, (limit, limit), (cam_w-limit,cam_h-limit), (0, 255, 0), 2)
    
    # Detectar manos en el fotograma
    hands, img = detector.findHands(img, flipType=False)
    
    if hands:
        # Obtener la posición de la mano    
        lmList = hands[0]["lmList"]  # Lista de puntos clave de la mano, con esto vamos sacando los indices del dedo y mano que queremos utilizar
        ind_x , ind_y = lmList[8][0],lmList[8][1]#numeros los cuales indican que dedo se quiere utilizar(el indice)
        mid_x , mid_y = lmList[12][0], lmList[12][1] #numeros los cuales indican al dedo de al medio
        
        cv2.circle(img,(ind_x,ind_y),5,(0,255,255),2)
        fingers = detector.fingersUp(hands[0]) # Hace que detecte si los dedos estan levantados o no, y los guarda en un arreglo(0,0,0,0,0), 1 si esta levantado, 0 si no lo esta 
        # print(fingers) 
        # --------------CONTROL MOVIMIENTO DEL MOUSE---------------------
        x, y, _ = lmList[8]  # Tomar los primeros dos elementos de la mano completa
        # Mapear las coordenadas de la mano a la región de movimiento, se lo delimitamos cambiando el 100
        conv_x = int(np.interp(x,(limit,cam_w-limit),(0,1536)))
        conv_y = int(np.interp(y,(limit,cam_h-limit),(0,864)))
        # Mover el cursor del mouse a la nueva posición después de aplicar el filtro de media móvil
        conv_x_smoothed = int(apply_moving_average(conv_x, prev_x))
        conv_y_smoothed = int(apply_moving_average(conv_y, prev_y))
        mouse.move(conv_x_smoothed, conv_y_smoothed)
        
            
        # Mover el cursor del mouse a la nueva posición
        #mouse.move(conv_x,conv_y)
        #------------------CONTROL DEL CLICK IZQUIERDO-----------------------------------
        if fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0 and fingers[0] == 1:
            click_count += 1
            scroll_up_count = 0
            scroll_down_count = 0
        
            if click_count >= click_threshold:
                # Hacer clic izquierdo
                if l_delay == 0:
                    mouse.click(button="left")
                    l_delay = 1
                    click_thread.start()
                click_count=0
        elif fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
        # Hacer scroll hacia arriba
            scroll_up_count += 1
            click_count = 0
            scroll_down_count = 0
            if scroll_up_count >= scroll_threshold:
                mouse.wheel(delta=0.5)
                scroll_up_count=0

        elif fingers[0] == 0 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
    # Hacer scroll hacia abajo
            scroll_down_count += 1
            click_count = 0
            scroll_up_count = 0
            if scroll_down_count >= scroll_threshold:
                
                mouse.wheel(delta=-0.5)
                scroll_down_count= 0

        
    # Mostrar el fotograma con la mano detectada y la región de movimiento
    cv2.imshow("Camara", img)
    
    # Salir del bucle si se presiona 'q' en el teclado
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar todas las ventanas
cap.release()
cv2.destroyAllWindows()