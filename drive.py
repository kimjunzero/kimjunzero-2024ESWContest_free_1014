import cv2
import numpy as np
import RPi.GPIO as GPIO
import time
import zmq
from flask_socketio import SocketIO, emit


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")
socketio = SocketIO(message_queue='redis://')

# 모터 PWM 및 GPIO 핀
ENA_FRONT_LEFT = 21
ENA_FRONT_RIGHT = 7
IN1_FRONT_LEFT = 20
IN2_FRONT_LEFT = 16
IN1_FRONT_RIGHT = 12
IN2_FRONT_RIGHT = 1
ENA_REAR_LEFT = 9
ENA_REAR_RIGHT = 26
IN1_REAR_LEFT = 19
IN2_REAR_LEFT = 13
IN1_REAR_RIGHT = 6
IN2_REAR_RIGHT = 5

def motor_setup():
    # GPIO 모드 설정
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # 모터 핀 설정
    GPIO.setup(IN1_FRONT_LEFT, GPIO.OUT)
    GPIO.setup(IN2_FRONT_LEFT, GPIO.OUT)
    GPIO.setup(ENA_FRONT_LEFT, GPIO.OUT)
    
    GPIO.setup(IN1_FRONT_RIGHT, GPIO.OUT)
    GPIO.setup(IN2_FRONT_RIGHT, GPIO.OUT)
    GPIO.setup(ENA_FRONT_RIGHT, GPIO.OUT)
    
    GPIO.setup(IN1_REAR_LEFT, GPIO.OUT)
    GPIO.setup(IN2_REAR_LEFT, GPIO.OUT)
    GPIO.setup(ENA_REAR_LEFT, GPIO.OUT)
    
    GPIO.setup(IN1_REAR_RIGHT, GPIO.OUT)
    GPIO.setup(IN2_REAR_RIGHT, GPIO.OUT)
    GPIO.setup(ENA_REAR_RIGHT, GPIO.OUT)

    # PWM 설정
    global front_left_motor, front_right_motor, rear_left_motor, rear_right_motor
    front_left_motor = GPIO.PWM(ENA_FRONT_LEFT, 100)
    front_right_motor = GPIO.PWM(ENA_FRONT_RIGHT, 100)
    rear_left_motor = GPIO.PWM(ENA_REAR_LEFT, 100)
    rear_right_motor = GPIO.PWM(ENA_REAR_RIGHT, 100)

    front_left_motor.start(0)
    front_right_motor.start(0)
    rear_left_motor.start(0)
    rear_right_motor.start(0)

def motor_control(front_left_speed, front_right_speed, rear_left_speed, rear_right_speed):
    front_left_motor.ChangeDutyCycle(abs(front_left_speed))
    GPIO.output(IN1_FRONT_LEFT, front_left_speed > 0)
    GPIO.output(IN2_FRONT_LEFT, front_left_speed <= 0)

    front_right_motor.ChangeDutyCycle(abs(front_right_speed))
    GPIO.output(IN1_FRONT_RIGHT, front_right_speed > 0)
    GPIO.output(IN2_FRONT_RIGHT, front_right_speed <= 0)

    rear_left_motor.ChangeDutyCycle(abs(rear_left_speed))
    GPIO.output(IN1_REAR_LEFT, rear_left_speed > 0)
    GPIO.output(IN2_REAR_LEFT, rear_left_speed <= 0)

    rear_right_motor.ChangeDutyCycle(abs(rear_right_speed))
    GPIO.output(IN1_REAR_RIGHT, rear_right_speed > 0)
    GPIO.output(IN2_REAR_RIGHT, rear_right_speed <= 0)



def detect_red(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.add(mask1, mask2)
    return cv2.countNonZero(red_mask)

def detect_yellow(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([20, 100, 100])  # 노란색의 HSV 범위 설정
    upper_yellow = np.array([30, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    return cv2.countNonZero(yellow_mask)

def main():
    motor_setup()
    cap = cv2.VideoCapture(2)  # 적절한 카메라 인덱스 사용
    if not cap.isOpened():
        print("Cannot open camera")
        return
    cap.set(3, 160) 
    cap.set(4, 120)

    while cap.isOpened():
        ret, frame = cap.read()
        reversed_frame = cv2.flip(frame,-1)
        if not ret:
            print("Failed to grab frame")
            break
        crop_img = reversed_frame[60:120, 0:160]
        output_img = crop_img    
        height, width, _ = frame.shape
        bottom_frame = frame[int(height*0.9):height, 0:width]
                
        red_detected = detect_red(bottom_frame)
        if red_detected > 600:  # Adjust
            print("red")
            break  # Optional: Remove this to keep the loop running even after detection

        yellow_detected = detect_yellow(bottom_frame)
        if yellow_detected > 500:  # 적절한 임계값 설정
            motor_control(0, 0, 0, 0)  # 정지
            print("Yellow")
        
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        ret, thresh1 = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY_INV)

        mask = cv2.erode(thresh1, None, iterations=3)
        mask = cv2.dilate(mask, None, iterations=3)      
        
        contours, hierarchy = cv2.findContours(mask.copy(), 1, cv2.CHAIN_APPROX_NONE)
        
        # Canny 에지 감지를 사용하여 경계 찾기
        edges = cv2.Canny(mask, 100, 200)
        edge_height, edge_width = edges.shape
        # 각 행에서 최소, 최대 에지 찾기
        for y in range(edge_height):
            row = edges[y]
            edge_positions = np.where(row == 255)[0]
            if edge_positions.size > 0:
                left_edge = edge_positions[0]
                right_edge = edge_positions[-1]
                cv2.circle(output_img, (left_edge, y), 1, (0, 255, 0), 2)  # 왼쪽 경계에 녹색 점 그리기
                cv2.circle(output_img, (right_edge, y), 1, (0, 255, 0), 2)  # 오른쪽 경계에 빨간 점 그리기
    
        
        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            
            if M['m00'] != 0:
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
            
                if cx >= 95 and cx <= 125:
                    print("Turn Left!")
                    motor_control(100, -60, 100, -60)  # Turn right
                elif cx >= 39 and cx <= 65:
                    print("Turn Right")
                    motor_control(-60, 100, -60, 100)  # Turn left
                else:
                    print("Go")
                    motor_control(80, 80, 80, 80)  # Go straight
        output_img = cv2.flip(output_img,-1)
        ret, jpeg = cv2.imencode('.jpg', output_img)
        if ret:
            socket.send(jpeg.tobytes())
        
    
    cap.release()
    cv2.destroyAllWindows()
    front_left_motor.stop()
    front_right_motor.stop()
    rear_left_motor.stop()
    rear_right_motor.stop()
    GPIO.cleanup()

if __name__ == "__main__":
    main()
