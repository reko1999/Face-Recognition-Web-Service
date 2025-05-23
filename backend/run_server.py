import subprocess
import time
from pyngrok import ngrok
import uvicorn
import os
import threading

def run_fastapi():
    # FastAPI 서버 실행
        config = uvicorn.Config(
            "app.app:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
        server = uvicorn.Server(config)
        server.run()


def setup_ngrok(auth_token):
    try:
        ngrok.set_auth_token(auth_token)

        # ngrok 터널 생성
        http_tunnel = ngrok.connect(8000)
        print(f"ngrok 터널이 생성되었습니다: {http_tunnel.public_url}")
        print("* 이 URL을 통해 외부에서 채팅 애플리케이션에 접속할 수 있습니다.\n")

        # 환경 변수로 공개 URL 전달 (선택사항)
        # os.environ['PUBLIC_URL'] = http_tunnel.public_url

        return http_tunnel.public_url
    except exception.PyngrokNgrokError as e:
        print(f"ngrok 에러: {e}")
        raise

if __name__ == "__main__":
    try:
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        print("FastAPI 서버가 시작되었습니다.")

        # 서버가 시작될 때까지 대기
        time.sleep(5)  # FastAPI 서버가 포트를 점유할 시간 확보

        # ngrok 인증 토큰 입력 받기
        auth_token = input("ngrok 인증 토큰을 입력하세요: ")

        # ngrok 설정
        public_url = setup_ngrok(auth_token)
        
        # 앱이 계속 실행되도록 대기
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"에러 발생: {e}")
        ngrok.kill()
        time.sleep(5)
        print("ngrok 터널 및 FastAPI 서버가 종료되었습니다.")
    except KeyboardInterrupt:
        # 종료 시 정리
        ngrok.kill()
        time.sleep(5)
        print("ngrok 터널 및 FastAPI 서버가 종료되었습니다.")