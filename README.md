# Face-Recognition-Web-Service
안면인식 웹 서비스

## 개요
MediaPipe와 FastAPI로 얼굴을 등록/인식하며, React와 WebRTC로 실시간 카메라 스트리밍을 제공하는 웹 서비스. ngrok으로 외부 접근.

## 설치
1. Python 3.11 이상.
2. 종속성:
- fastapi: 백엔드 API 서버.
- uvicorn: FastAPI 실행용 ASGI 서버.
- pyngrok: 로컬 서버 외부 공개.
- mediapipe: 컴퓨터 비전 및 머신 러닝 기반 미디어 처리.
- opencv-python-headless: GUI 없는 이미지 및 비디오 처리.
- pillow: 이미지 처리 및 조작.
- numpy: 수치 연산 및 배열 처리.
- python-multipart: 파일 업로드 처리.
4. ngrok 설치 및 인증 토큰 설정.

## 실행
1. FastAPI: `python app.py`.
2. ngrok: `python run_server.py`.
3. 공개 URL로 접속.

## API 사용법
- **엔드포인트**: `/register`
  - **메서드**: POST
  - **요청**: FormData (`image`, `name`)
  - **응답**: JSON (등록 메시지).
- **엔드포인트**: `/recognize`
  - **메서드**: POST
  - **요청**: FormData (`image`)
  - **응답**: JSON (인식 결과, 신뢰도, 바운딩 박스).
- **엔드포인트**: `/health`
  - **메서드**: GET
  - **응답**: JSON (서버 상태).
