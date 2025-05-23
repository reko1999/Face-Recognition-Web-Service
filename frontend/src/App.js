import './App.css';
import React, { useState, useRef, useEffect } from 'react';

function App() {
  const [cameraActive, setCameraActive] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState('user');
  const [devices, setDevices] = useState([]);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [registerName, setRegisterName] = useState('');
  const [recognitionResults, setRecognitionResults] = useState(null);
  const [faceRectangle, setFaceRectangle] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
      // 카메라 장치 목록 가져오기
      navigator.mediaDevices.enumerateDevices()
          .then(devices => {
              const videoDevices = devices.filter(device => device.kind === 'videoinput');
              setDevices(videoDevices);
          });
  }, []);

  const startCamera = async () => {
      try {
          if (streamRef.current) {
              streamRef.current.getTracks().forEach(track => track.stop());
          }

          const constraints = {
              video: { facingMode: selectedCamera }
          };

          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          streamRef.current = stream;
          
          if (videoRef.current) {
              videoRef.current.srcObject = stream;
              setCameraActive(true);
          }
      } catch (error) {
          showMessage('카메라를 시작할 수 없습니다: ' + error.message, 'error');
      }
  };

  const stopCamera = () => {
      if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
      }
      if (videoRef.current) {
          videoRef.current.srcObject = null;
      }
      setCameraActive(false);
      setFaceRectangle(null);
  };

  const captureImage = () => {
      if (!videoRef.current) return null;

      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(videoRef.current, 0, 0);
      
      return canvas.toDataURL('image/jpeg');
  };

  const showMessage = (msg, type) => {
      setMessage(msg);
      setMessageType(type);
      setTimeout(() => {
          setMessage('');
          setMessageType('');
      }, 5000);
  };

  const registerFace = async () => {
      if (!registerName.trim()) {
          showMessage('이름을 입력해주세요.', 'error');
          return;
      }

      const imageData = captureImage();
      if (!imageData) {
          showMessage('카메라가 활성화되지 않았습니다.', 'error');
          return;
      }

      try {
          const formData = new FormData();
          const blob = await fetch(imageData).then(r => r.blob());
          formData.append('image', blob, 'face.jpg');
          formData.append('name', registerName);

          const response = await fetch('./register', {
              method: 'POST',
              body: formData
          });

          const data = await response.json();

          if (response.ok) {
              showMessage(data.message, 'success');
              setRegisterName('');
              setIsRegistering(false);
          } else {
              showMessage(data.detail || '등록 실패', 'error');
          }
      } catch (error) {
          showMessage('등록 중 오류 발생: ' + error.message, 'error');
      }
  };

  const recognizeFace = async () => {
      const imageData = captureImage();
      if (!imageData) {
          showMessage('카메라가 활성화되지 않았습니다.', 'error');
          return;
      }

      try {
          const formData = new FormData();
          const blob = await fetch(imageData).then(r => r.blob());
          formData.append('image', blob, 'face.jpg');

          const response = await fetch('./recognize', {
              method: 'POST',
              body: formData
          });

          const data = await response.json();

          if (response.ok) {
              setRecognitionResults(data);
              if (data.face_detected && videoRef.current) {
                  const videoWidth = videoRef.current.videoWidth;
                  const videoHeight = videoRef.current.videoHeight;
                  const displayWidth = videoRef.current.offsetWidth;
                  const displayHeight = videoRef.current.offsetHeight;
                  
                  const scaleX = displayWidth / videoWidth;
                  const scaleY = displayHeight / videoHeight;
                  
                  const rect = data.face_location;
                  setFaceRectangle({
                      left: rect.left * scaleX,
                      top: rect.top * scaleY,
                      width: rect.width * scaleX,
                      height: rect.height * scaleY
                  });
              }
              showMessage('인식 완료', 'success');
          } else {
              showMessage(data.detail || '인식 실패', 'error');
          }
      } catch (error) {
          showMessage('인식 중 오류 발생: ' + error.message, 'error');
      }
  };

  useEffect(() => {
      if (faceRectangle && canvasRef.current && videoRef.current) {
          const canvas = canvasRef.current;
          const ctx = canvas.getContext('2d');
          
          canvas.width = videoRef.current.offsetWidth;
          canvas.height = videoRef.current.offsetHeight;
          
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.strokeStyle = '#00ff00';
          ctx.lineWidth = 3;
          ctx.strokeRect(
              faceRectangle.left,
              faceRectangle.top,
              faceRectangle.width,
              faceRectangle.height
          );
      }
  }, [faceRectangle]);

  return (
      <div className="container">
          <h1>안면인식 시스템</h1>
          
          <div className="controls">
              <select 
                  value={selectedCamera} 
                  onChange={(e) => setSelectedCamera(e.target.value)}
                  disabled={cameraActive}
              >
                  <option value="user">전면 카메라</option>
                  <option value="environment">후면 카메라</option>
              </select>
              
              {!cameraActive ? (
                  <button onClick={startCamera}>카메라 시작</button>
              ) : (
                  <button onClick={stopCamera}>카메라 중지</button>
              )}
          </div>

          <div className="camera-container">
              <video 
                  ref={videoRef} 
                  autoPlay 
                  playsInline
                  style={{ display: cameraActive ? 'block' : 'none' }}
              />
              <canvas 
                  ref={canvasRef}
                  style={{ display: cameraActive ? 'block' : 'none' }}
              />
          </div>

          {message && (
              <div className={messageType === 'error' ? 'error' : 'success'}>
                  {message}
              </div>
          )}

          {cameraActive && (
              <div className="controls">
                  {!isRegistering ? (
                      <>
                          <button onClick={() => setIsRegistering(true)}>안면 등록</button>
                          <button onClick={recognizeFace}>안면 인식</button>
                      </>
                  ) : (
                      <div className="form-group">
                          <label>등록할 이름:</label>
                          <input
                              type="text"
                              value={registerName}
                              onChange={(e) => setRegisterName(e.target.value)}
                              placeholder="이름을 입력하세요"
                          />
                          <div className="controls" style={{ marginTop: '10px' }}>
                              <button onClick={registerFace}>등록 완료</button>
                              <button onClick={() => {
                                  setIsRegistering(false);
                                  setRegisterName('');
                              }}>취소</button>
                          </div>
                      </div>
                  )}
              </div>
          )}

          {recognitionResults && (
              <div className="recognition-results">
                  <h3>인식 결과</h3>
                  <p>얼굴 감지: {recognitionResults.face_detected ? '예' : '아니오'}</p>
                  {recognitionResults.recognized && (
                      <>
                          <p>인식된 사람: {recognitionResults.name}</p>
                          <p>신뢰도: {(recognitionResults.confidence * 100).toFixed(2)}%</p>
                      </>
                  )}
                  {recognitionResults.face_detected && (
                      <>
                          <p>얼굴 특징점 수: {recognitionResults.num_landmarks}</p>
                          <p>얼굴 위치: 
                              상단-{recognitionResults.face_location.top}, 
                              좌측-{recognitionResults.face_location.left},
                              너비-{recognitionResults.face_location.width},
                              높이-{recognitionResults.face_location.height}
                          </p>
                      </>
                  )}
              </div>
          )}
      </div>
  );
}

export default App;
