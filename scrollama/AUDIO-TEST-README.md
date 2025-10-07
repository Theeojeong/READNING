# 🎵 Scrollama + Audio 테스트 가이드

## 📁 오디오 파일 준비

`audio` 폴더에 다음 이름으로 오디오 파일을 넣어주세요:

```
audio/
  ├── track1.mp3
  ├── track2.mp3
  ├── track3.mp3
  ├── track4.mp3
  └── track5.mp3
```

**지원 형식**: MP3, WAV, OGG, M4A 등

## 🚀 실행 방법

### 방법 1: Live Server (추천)
1. VS Code에서 `test-audio-scroll.html` 우클릭
2. "Open with Live Server" 선택
3. 브라우저에서 자동으로 열림

### 방법 2: Python 서버
```bash
# Python 3
python -m http.server 8000

# 브라우저에서 접속
# http://localhost:8000/test-audio-scroll.html
```

### 방법 3: Node.js 서버
```bash
npx http-server -p 8000

# 브라우저에서 접속
# http://localhost:8000/test-audio-scroll.html
```

### 방법 4: 직접 열기
- 파일을 브라우저로 드래그 앤 드롭
- ⚠️ 보안 정책으로 인해 일부 기능이 제한될 수 있음

## 🎨 주요 기능

### ✨ 인터랙티브 요소
- **스크롤 트리거**: 각 섹션에 도달하면 자동으로 오디오 변경
- **Sticky 레이아웃**: 오디오 플레이어가 화면에 고정
- **부드러운 전환**: Active 섹션 강조 효과
- **진행률 표시**: 상단 프로그레스 바

### 🎵 오디오 제어
- 각 섹션마다 다른 오디오 재생
- 수동 재생/일시정지 가능
- 자동 재생 옵션 (선택적)

## ⚙️ 커스터마이징

### 오디오 파일 경로 변경
`test-audio-scroll.html` 파일의 19번째 줄 근처:

```javascript
const audioFiles = {
    audio1: 'audio/track1.mp3',  // 여기를 수정
    audio2: 'audio/track2.mp3',
    // ...
};
```

### 텍스트 내용 수정
각 `.step` div의 내용을 원하는 텍스트로 변경:

```html
<div class="step" data-step="1" data-audio="audio1">
    <h2>제목</h2>
    <p>내용을 여기에 입력하세요</p>
</div>
```

### 섹션 추가/삭제
1. HTML에서 `.step` 추가/삭제
2. JavaScript의 `audioFiles`와 `audioTitles` 객체 업데이트

### 자동 재생 활성화
`onStepEnter` 콜백에서 주석 해제:

```javascript
// 자동 재생 (선택사항)
audioPlayer.play().catch(e => console.log('자동 재생 실패:', e));
```

## 🎯 테스트 시나리오

1. **스크롤 테스트**: 천천히 스크롤하며 각 섹션 전환 확인
2. **오디오 테스트**: 각 섹션에서 올바른 오디오가 로드되는지 확인
3. **반응형 테스트**: 브라우저 크기 조절하여 모바일 레이아웃 확인
4. **진행률 테스트**: 프로그레스 바가 정상 작동하는지 확인

## 🐛 문제 해결

### 오디오가 재생되지 않음
- 파일 경로 확인
- 브라우저 콘솔에서 에러 메시지 확인
- 오디오 형식이 지원되는지 확인

### CORS 에러
- 로컬 서버 사용 (방법 1, 2, 3)
- 파일을 직접 열면 발생할 수 있음

### Scrollama가 작동하지 않음
- `build/scrollama.js` 파일 존재 확인
- 브라우저 콘솔에서 에러 확인

## 📱 모바일 지원

- 반응형 디자인 적용
- 768px 이하에서 레이아웃 변경
- 터치 스크롤 지원

## 💡 추가 아이디어

- 각 섹션마다 배경색 변경
- 이미지나 비디오 추가
- 오디오 파형 시각화
- 페이드 인/아웃 효과
- 스크롤 방향에 따른 다른 효과

즐거운 테스트 되세요! 🚀

