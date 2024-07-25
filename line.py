import cv2
import numpy as np

IMG_WIDTH = 640
IMG_HEIGHT = 480
ASSIST_BASE_LINE = 320
ASSIST_BASE_WIDTH = 60

def canny_edge_detection(img):
    """Canny 엣지 검출을 수행합니다."""
    blur_img = cv2.GaussianBlur(img, (3, 3), 0)
    canny_img = cv2.Canny(blur_img, 70, 170)
    return canny_img

def region_of_interest(img, vertices):
    """이미지에서 관심 영역을 마스킹 처리합니다."""
    mask = np.zeros_like(img)
    cv2.fillPoly(mask, vertices, 255)
    masked_img = cv2.bitwise_and(img, mask)
    return masked_img

def draw_lines(img, lines):
    """검출된 차선을 이미지에 그립니다."""
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 5)  # 초록색으로 선 그리기

def main():
    cap = cv2.VideoCapture(2)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    # ROI 설정
    vertices = np.array([[(0, ASSIST_BASE_LINE - ASSIST_BASE_WIDTH),
                          (0, ASSIST_BASE_LINE + ASSIST_BASE_WIDTH),
                          (IMG_WIDTH, ASSIST_BASE_LINE + ASSIST_BASE_WIDTH),
                          (IMG_WIDTH, ASSIST_BASE_LINE - ASSIST_BASE_WIDTH)]], dtype=np.int32)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Cannot read frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = canny_edge_detection(gray)
        roi = region_of_interest(edges, vertices)

        # Hough 변환을 이용한 직선 검출
        lines = cv2.HoughLinesP(roi, 1, np.pi/180, 40, minLineLength=20, maxLineGap=10)

        # 검출된 차선을 원본 이미지에 초록색으로 그립니다.
        draw_lines(frame, lines)
        
        cv2.imshow("Detected Lanes", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
