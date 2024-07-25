from flask import Flask, render_template, request, Response, jsonify, send_file
import logging
import qrcode
import subprocess 
from subprocess import Popen,PIPE
from io import BytesIO
import os
from flask_socketio import SocketIO, emit
import zmq

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://192.168.137.213:5555")
socket.setsockopt_string(zmq.SUBSCRIBE, '')

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# 순환하는 QR 코드 값과 주문 순서 추적을 위한 전역 변수
current_qr_value = 0
order_count = 0  # 주문 순서를 추적하는 전역 변수

@app.route('/')
def home():
    return render_template('index.html')

def generate_frame():
    while True:
        try:
            frame = socket.recv(flags=zmq.NOBLOCK)  # Non-blocking receive
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except zmq.Again:
            continue
        
        
@app.route('/video_feed')
def video_feed():
    """ 비디오 피드 라우트, 스트리밍 데이터 전송 """
    return Response(generate_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    
@socketio.on('connect', namespace='/test')
def test_connect():
    """ 소켓 연결 확인 메시지 """
    print('Client connected')
    
@app.route('/unlock', methods=['POST'])
def unlock():
    try:
        subprocess.Popen(['python', 'opencv_qr.py'], env=dict(os.environ, DISPLAY=":0"))
        return jsonify({"message": "카메라가 활성화되었습니다."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data', methods=['POST'])
def receive_number():
    global current_qr_value, order_count
    try:
        data = request.get_json()
        number = data.get('data')  # 받을 장소 정보
        cart_item_names = data.get('cartItemNames')  # 메뉴 아이템 목록
        if number is not None and cart_item_names :
            current_qr_value = (current_qr_value % 3) + 1
            qr_data = str(current_qr_value)

            order_count += 1
            app.logger.info(f'  Order: [{order_count}] Menu: [{cart_item_names}] Receive place : {number} Drawer number: [{qr_data}]')

            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            return send_file(img_byte_arr, mimetype='image/png')
        else:
            return jsonify({"status": "error", "message": "Missing items or location"}), 400
    except Exception as e:
        app.logger.error(f"Error processing the data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/start', methods=['POST'])
def start_delivery():
    print("Start delivery endpoint hit")
    socketio.emit('button_action', {'display': 'none'}, namespace='/test')
    proc = Popen(['python', 'drive.py'], stdout=PIPE, stderr=PIPE)
    socketio.emit('video_status', {'status': 'ON'}, namespace='/test')
    proc.wait()
    print("drive.py process finished")
    socketio.emit('button_action', {'display': 'block'}, namespace='/test')
    socketio.emit('video_status', {'status': 'OFF'}, namespace='/test')
    if proc.returncode == 0:
        return jsonify({"message": "배송이 시작되었습니다.", "status": "success"}), 200
    else:
        error_message = proc.stderr.read().decode()
        print("Error in drive.py:", error_message)
        return jsonify({"message": "Error: " + error_message, "status": "failure"}), 500



if __name__ == "__main__":
    app.run(host="192.168.137.213", port=8080) 