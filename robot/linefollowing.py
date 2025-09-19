import time
from picar import Picar
pc = Picar()


active: bool = True
crossing: bool = False


motor_left = pc.MOTOR_LEFT
motor_right = pc.MOTOR_RIGHT
update_time = 0.8
sensor_states = pc.get_line_sensor_states()

def go_forward(speed: float):
    # set motor speed
    pc.set_speed(motor_left, speed)
    pc.set_speed(motor_right, speed)
    
def stop():
    # set motor speed
    pc.set_speed(motor_left, 0)
    pc.set_speed(motor_right, 0)

def turn(left: float, right: float):
    pc.set_speed(motor_left, left)
    pc.set_speed(motor_right, right)

def sensor_check():
    return pc.get_line_sensor_states()

def analyse_sensor(sensor_states):
    if(sensor_states[0] == sensor_states[1] == 1):
        print(f"sensor_analyse_left = 1")
        return 0
    if(sensor_states[1] == sensor_states[2] == sensor_states[3] == 1):
        print(f"sensor_analyse_center = 1")
        return 1
    if(sensor_states[3] == sensor_states[4] == 1):
        print(f"sensor_analyse_right = 1")
        return 2


while active:
    sensor_states = sensor_check()
    print(f"sensors: {sensor_states}")
    line_is = analyse_sensor(sensor_states)
    if(line_is == 0):
        turn(0.4,0.6)
    elif(line_is == 1):
        go_forward(0.8)
    elif(line_is == 2):
        turn(0.6,0.4)
    else:
        print("out of lane?")
        stop()
    time.sleep(update_time)