import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

# 서보모터 핀 설정
servo_pins = {
    'top_drawer': [2],
    'middle_drawer': [18],
    'bottom_drawer': [25]
}

# 서보모터 및 PWM 초기화
servos = {}
for drawer, pins in servo_pins.items():
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 50)  # 50Hz: 서보 모터에 적합한 주파수
        pwm.start(0)
        servos[pin] = pwm

# 최소 및 최대 듀티 사이클 설정
servo_min_duty = 2.5
servo_max_duty = 12.5

def set_servo_degree(pin, degree, reverse=False):
    if degree > 180:
        degree = 180
    elif degree < 0:
        degree = 0
    duty = (servo_min_duty + (degree * (servo_max_duty - servo_min_duty) / 180.0)) if not reverse else (servo_max_duty - (degree * (servo_max_duty - servo_min_duty) / 180.0))
    servos[pin].ChangeDutyCycle(duty)

def unlock_and_lock_drawer(drawer):
    pin = servo_pins[drawer][0]
    set_servo_degree(pin, 150)  # 서랍 열기 (90도 회전)
    sleep(1)  # 회전 완료 대기

def cleanup():
    for servo in servos.values():
        servo.stop()
    GPIO.cleanup()
