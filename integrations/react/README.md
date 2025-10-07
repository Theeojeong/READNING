# React 통합 가이드

이 디렉토리는 기존 React/Next 앱에 “읽는 청크 감지 → 해당 BGM 크로스페이드 재생”을 이식하기 위한 최소 훅과 예시 컴포넌트를 제공합니다.

구성
- `useActiveChunk.js`: IntersectionObserver + 체류시간 기반 활성 청크 감지 훅
- `useAudioController.js`: Web Audio API 기반 크로스페이드 오디오 훅
- `Reader.jsx`: 위 두 훅을 조합한 예시 컴포넌트

빠른 사용법
1) 두 훅 파일을 기존 앱의 `src/hooks/` 같은 위치로 복사하세요.
2) 매니페스트 형태는 다음을 기대합니다:
```json
{
  "title": "도서 제목",
  "chunks": [
    { "id": "c1", "title": "청크 1", "text": "...", "audioUrl": "/assets/c1.mp3", "fadeMs": 600 }
  ]
}
```
3) 페이지/컴포넌트에서 예시처럼 렌더링합니다:
```jsx
import { Reader } from './Reader';
// manifest는 서버에서 가져오거나 SSR로 주입
<Reader manifest={manifest} />
```

주의 사항
- 브라우저 자동재생 정책: 첫 사용자 제스처 이전에는 재생이 불가합니다. `오디오 활성화` 버튼으로 언락합니다.
- 오디오 파일 CORS: `audioUrl`이 다른 도메인이면 CORS 허용이 필요합니다.
- iOS Safari: 백그라운드/화면잠금 전환 시 자동 일시정지될 수 있습니다. UX상 자연스러운 복귀 처리를 고려하세요.
- 성능: 긴 리스트에서도 IntersectionObserver 1개만 사용합니다. 필요시 `dwellMs`를 조정해 전환 안정성을 높일 수 있습니다.

커스터마이즈 포인트
- 감지 민감도: `useActiveChunk({ dwellMs })`의 `dwellMs` 변경, 점수 가중치(가시성/상단근접) 변경 가능.
- 페이드/루프: `useAudioController({ defaultFadeMs })` 조정, 트랙별 `fadeMs` 지원.
- 프리로딩: `preloadNeighbors(list, activeIndex)`는 현재 ±1만 로드합니다. 확장 가능.

