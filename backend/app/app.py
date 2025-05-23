from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import cv2
import mediapipe as mp
import numpy as np
import json
import os
import base64
from pathlib import Path
import pickle
from typing import Optional
import io
from PIL import Image

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MediaPipe 초기화
mp_face_detection = mp.solutions.face_detection
mp_face_mesh = mp.solutions.face_mesh
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5)

# 등록된 얼굴 데이터 저장 경로
REGISTERED_FACES_DIR = Path("../registered_faces")
REGISTERED_FACES_DIR.mkdir(exist_ok=True)

def extract_face_embedding(image):
    """MediaPipe를 사용한 얼굴 특징 추출"""
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_image)
    
    if results.multi_face_landmarks:
        face_landmarks = results.multi_face_landmarks[0]
        
        # 랜드마크를 numpy 배열로 변환
        landmarks = []
        for landmark in face_landmarks.landmark:
            landmarks.extend([landmark.x, landmark.y, landmark.z])
        
        return np.array(landmarks)
    
    return None

def compare_embeddings(embedding1, embedding2):
    """두 임베딩 간의 유사도 계산"""
    if embedding1 is None or embedding2 is None:
        return 0.0
    
    # 코사인 유사도 계산
    dot_product = np.dot(embedding1, embedding2)
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    return similarity

def get_face_detection_info(image):
    """얼굴 감지 정보 추출"""
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_detection.process(rgb_image)
    
    if results.detections:
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        h, w, _ = image.shape
        
        return {
            "face_detected": True,
            "face_location": {
                "left": int(bbox.xmin * w),
                "top": int(bbox.ymin * h),
                "width": int(bbox.width * w),
                "height": int(bbox.height * h)
            }
        }
    
    return {"face_detected": False}

@app.post("/register")
async def register_face(image: UploadFile = File(...), name: str = Form(...)):
    """얼굴 등록 API"""
    try:
        # 이름 검증
        if not name.strip():
            raise HTTPException(status_code=400, detail="이름을 입력해주세요.")
        
        # 이미지 읽기
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 얼굴 특징 추출
        embedding = extract_face_embedding(img)
        if embedding is None:
            raise HTTPException(status_code=400, detail="얼굴을 찾을 수 없습니다.")
        
        # 기존 등록된 얼굴과 비교
        for file in REGISTERED_FACES_DIR.glob("*.pkl"):
            with open(file, "rb") as f:
                registered_data = pickle.load(f)
                registered_embedding = registered_data["embedding"]
                similarity = compare_embeddings(embedding, registered_embedding)
                
                if similarity > 0.95:  # 95% 이상 유사도
                    raise HTTPException(
                        status_code=400, 
                        detail=f"이미 등록된 얼굴입니다. (유사도: {similarity*100:.1f}%)"
                    )
        
        # 얼굴 데이터 저장
        face_data = {
            "name": name,
            "embedding": embedding
        }
        
        filename = f"{name}_{len(list(REGISTERED_FACES_DIR.glob('*.pkl')))}.pkl"
        with open(REGISTERED_FACES_DIR / filename, "wb") as f:
            pickle.dump(face_data, f)
        
        return {"message": f"{name}님의 얼굴이 성공적으로 등록되었습니다."}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recognize")
async def recognize_face(image: UploadFile = File(...)):
    """얼굴 인식 API"""
    try:
        # 이미지 읽기
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 얼굴 감지 정보
        detection_info = get_face_detection_info(img)
        
        # 얼굴 특징 추출
        embedding = extract_face_embedding(img)
        if embedding is None:
            return {
                **detection_info,
                "recognized": False,
                "message": "얼굴을 찾을 수 없습니다."
            }
        
        # 등록된 얼굴과 비교
        best_match = None
        best_similarity = 0
        
        for file in REGISTERED_FACES_DIR.glob("*.pkl"):
            with open(file, "rb") as f:
                registered_data = pickle.load(f)
                registered_embedding = registered_data["embedding"]
                similarity = compare_embeddings(embedding, registered_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = registered_data["name"]
        
        # 결과 반환
        if best_similarity > 0.85:  # 85% 이상 유사도로 인식
            # 얼굴 메시 정보 추가
            results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            num_landmarks = len(results.multi_face_landmarks[0].landmark) if results.multi_face_landmarks else 0
            
            return {
                **detection_info,
                "recognized": True,
                "name": best_match,
                "confidence": float(best_similarity),
                "num_landmarks": num_landmarks,
                "message": f"{best_match}님으로 인식되었습니다."
            }
        else:
            return {
                **detection_info,
                "recognized": False,
                "confidence": float(best_similarity),
                "message": "등록되지 않은 얼굴입니다."
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}

# 메인 페이지 라우트
@app.get("/")
async def read_index():
    return FileResponse('www/index.html')

# Static 파일 설정 - API 엔드포인트 정의 후에 마운트
app.mount("/static", StaticFiles(directory="./www/static"), name="static")