import time
from inputs import get_gamepad  # Importar la librería de inputs
from _py_librerias import Bluetooth as Bt  # Bluetooth

def connect_robot(address):
    return Bt.connect(address)

def send_command(robot, WM1FL, WM2FR, WM3BL, WM4BR):
    WM1FL = int(WM1FL)
    WM2FR = int(WM2FR)
    WM3BL = int(WM3BL)
    WM4BR = int(WM4BR)
    Bt.move(robot, WM1FL, WM2FR, WM3BL, WM4BR)

def limit_value(value, min_value, max_value):
    """ Limitar el valor entre un mínimo y un máximo. """
    return max(min(value, max_value), min_value)

def apply_deadzone(value, deadzone_threshold):
    """ Aplicar el ángulo muerto (deadzone) a los valores del joystick. """
    return 0 if abs(value) < deadzone_threshold else value

def calculate_motor_speeds(erx, ery, erGiro):
    """ Calcular las velocidades de los motores a partir de erx, ery y erGiro para rotación. """
    r = 0.1  # Radio de las ruedas en metros
    # Ecuaciones para movimiento omnidireccional y rotación
    WM1FL = (1 / r) * (erx + ery - erGiro)  # Motor delantero izquierdo
    WM2FR = (1 / r) * (-erx + ery - erGiro)  # Motor delantero derecho
    WM3BL = (-1 / r) * (-erx + ery + erGiro)  # Motor trasero izquierdo
    WM4BR = (-1 / r) * (erx + ery + erGiro)  # Motor trasero derecho
    return WM1FL, WM2FR, WM3BL, WM4BR

def main():
    robot_bt = connect_robot("D8:13:2A:72:18:D6")
    max_value = 800
    deadzone_threshold = 0.1 * max_value  # Ángulo muerto del 10%

    erx = 0  # Inicializar erx
    ery = 0  # Inicializar ery
    erGiro = 0  # Inicializar erGiro (para el eje de rotación)

    active_joystick = None  # Variable para determinar qué joystick está activo (None, 'left', 'right')

    try:
        last_send_time = time.time()  # Inicializar tiempo del último envío
        send_interval = 0.1  # Intervalo de envío (10 Hz = 0.1 segundos)

        while True:
            events = get_gamepad()

            for event in events:
                # Joystick izquierdo: ABS_Y y ABS_X
                if event.code == 'ABS_Y' or event.code == 'ABS_X':
                    if active_joystick in [None, 'left']:  # Solo permitir si ninguno está activo o el izquierdo
                        if event.code == 'ABS_Y':  # Eje Y (vertical) del joystick izquierdo
                            erx = event.state * max_value / 32768  # Escalar a ±200
                            erx = apply_deadzone(erx, deadzone_threshold)  # Aplicar ángulo muerto
                            erx = limit_value(erx, -max_value, max_value)  # Limitar a ±200
                        elif event.code == 'ABS_X':  # Eje X (horizontal) del joystick izquierdo
                            ery = event.state * max_value / 32768  # Escalar a ±200
                            ery = apply_deadzone(ery, deadzone_threshold)  # Aplicar ángulo muerto
                            ery = limit_value(ery, -max_value, max_value)  # Limitar a ±200
                        # Si ambos ejes están fuera del ángulo muerto, activamos el joystick izquierdo
                        if abs(erx) > deadzone_threshold or abs(ery) > deadzone_threshold:
                            active_joystick = 'left'

                # Joystick derecho: ABS_RX
                elif event.code == 'ABS_RX':
                    if active_joystick in [None, 'right']:  # Solo permitir si ninguno está activo o el derecho
                        erGiro = event.state * max_value / 32768  # Escalar a ±200
                        erGiro = apply_deadzone(erGiro, deadzone_threshold)  # Aplicar ángulo muerto
                        erGiro = limit_value(erGiro, -max_value, max_value)  # Limitar a ±200
                        # Si el eje horizontal está fuera del ángulo muerto, activamos el joystick derecho
                        if abs(erGiro) > deadzone_threshold:
                            active_joystick = 'right'

            # Si los valores de los joysticks están en la zona muerta, desactivar joystick
            if abs(erx) < deadzone_threshold and abs(ery) < deadzone_threshold and abs(erGiro) < deadzone_threshold:
                active_joystick = None

            # Solo enviar comando si ha pasado suficiente tiempo
            current_time = time.time()
            if current_time - last_send_time >= send_interval:
                # Calcular velocidades de los motores usando erx, ery y erGiro
                WM1FL, WM2FR, WM3BL, WM4BR = calculate_motor_speeds(erx, ery, erGiro)
                WM1FL = int(WM1FL)
                WM2FR = int(WM2FR)
                WM3BL = int(WM3BL)
                WM4BR = int(WM4BR)
                # Enviar comando al robot
                send_command(robot_bt, WM1FL, WM2FR, WM3BL, WM4BR)

                # Imprimir los valores enviados y el joystick activo
                print(f"Valores enviados: WM1FL={WM1FL}, WM2FR={WM2FR}, WM3BL={WM3BL}, WM4BR={WM4BR}, erGiro={erGiro}, Joystick activo: {active_joystick}")

                # Actualizar tiempo del último envío
                last_send_time = current_time

    finally:
        send_command(robot_bt, 0, 0, 0, 0)  # Detener el robot
        Bt.disconnect(robot_bt)  # Desconectar Bluetooth

if __name__ == "__main__":
    main()