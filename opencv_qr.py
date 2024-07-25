import cv2
from picamera2 import Picamera2
import numpy as np
import tkinter as tk
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

# �������� �� ����
servo_pins = {
    'top_drawer': [2],
    'middle_drawer': [18],
    'bottom_drawer': [25]
}

# �������� �� PWM �ʱ�ȭ
servos = {}
for drawer, pins in servo_pins.items():
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 50)  # 50Hz: ���� ���Ϳ� ������ ���ļ�
        pwm.start(0)
        servos[pin] = pwm

# �ּ� �� �ִ� ��Ƽ ����Ŭ ����
servo_min_duty = 2.5
servo_max_duty = 12.5

def set_servo_degree(pin, degree):
    if degree > 180:
        degree = 180
    elif degree < 0:
        degree = 0
    duty = 2.5 + (degree * (12.5 - 2.5) / 180.0)
    servos[pin].ChangeDutyCycle(duty)

def unlock_and_lock_drawer(drawer):
    pin = servo_pins[drawer][0]
    set_servo_degree(pin, 180)
    print(f"{drawer} unlocked")

def cleanup():
    for servo in servos.values():
        servo.stop()
    GPIO.cleanup()

def detect_and_display_qr_code(image):
    qr = cv2.QRCodeDetector()
    data, box, _ = qr.detectAndDecode(image)
    if data:
        cv2.putText(image, data, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        if box is not None:
            pts = box.astype(int).reshape((-1, 1, 2))
            cv2.polylines(image, [pts], isClosed=True, color=(0, 255, 0), thickness=3)
        return data
    cv2.imshow('QR Code Detection', image)
    return False

def show_custom_message(qrnumber):
    root = tk.Tk()
    root.withdraw()
    dialog = tk.Toplevel(root)
    dialog.title("�˸�")
    dialog.geometry("400x120+{}+{}".format(dialog.winfo_screenwidth()//2-200, 100))
    message_label = tk.Label(dialog, text=f"{qrnumber}��° ����� �����Ǿ����ϴ�.\n��ǰ ���� �� ��� �Ϸ� ��ư�� ��������.", font=("Arial", 12))
    message_label.pack(pady=10)
    ok_button = tk.Button(dialog, text="Ȯ��", command=dialog.destroy, font=("Arial", 14), width=10, height=2)
    ok_button.pack(pady=7)
    dialog.attributes('-topmost', 'true')
    dialog.focus_force()
    root.after(3000, root.destroy)  # 5�� �Ŀ� �޽��� â�� �ڵ����� ����
    root.mainloop()

def main():
    picam2 = Picamera2()
    picam2.start()
    try:
        while True:
            image = picam2.capture_array()
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            qr_data = detect_and_display_qr_code(image)
            if qr_data:
                try:
                    qrnumber = int(qr_data)
                    if qrnumber in [1, 2, 3]:
                        unlock_and_lock_drawer(['top_drawer', 'middle_drawer', 'bottom_drawer'][qrnumber - 1])
                        picam2.stop()  # ī�޶� ����
                        show_custom_message(qrnumber)
                        break
                except ValueError:
                    print("QR �����Ͱ� �ùٸ� ���� ������ �ƴմϴ�. QR �����͸� ���ڷ� ��ȯ�� �� �����ϴ�.")
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cv2.destroyAllWindows()
        cleanup()

if __name__ == "__main__":
    main()

