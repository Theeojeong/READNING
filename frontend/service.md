⏺ 📚 Readning 서비스 분석 결과

  Readning은 AI 기반 독서 몰입 경험 플랫폼입니다. 주요 특징은 다음과 같습니다:

  🎯 핵심 서비스

  1. AI 음악 생성: 책의 내용을 분석해 각 챕터별로 맞춤 배경음악 자동 생성
  2. 멀티포맷 지원: PDF, TXT, EPUB 파일 업로드 및 읽기
  3. 개인 도서관: Firebase를 통한 개인 서재 관리
  4. 몰입형 리더: 음악과 함께하는 독서 환경

  🔧 기술 스택

  - Frontend: React + TypeScript + Vite + styled-components
  - Backend: Firebase (Firestore + Storage + Functions)
  - AI 서버: 외부 API (음악 생성 엔진)
  - PDF 렌더링: react-pdf + pdfjs-dist

  📱 주요 기능

  1. 책 업로드 & AI 처리
  - 파일 업로드 시 사용자의 음악 취향 선택 (피아노, 자연소리, 클래식 등)
  - AI가 책 내용 분석 후 챕터별 배경음악 자동 생성
  - Firebase Storage에 파일 저장, Firestore에 메타데이터 저장

  2. 몰입형 독서 환경
  - 사이드바에서 목차별 음악 재생/일시정지/다운로드
  - 페이지 이동 시 해당 챕터 음악 자동 재생
  - PDF 뷰어와 TXT 뷰어 지원

  3. 개인화된 서재
  - 사용자별 업로드한 책 관리
  - 리드닝 제공 추천 도서 목록
  - Google 로그인 연동

  📊 데이터 구조 (Firebase)

  Firestore Collections:
  - users/{uid}/books - 사용자 업로드 책
  - books - 리드닝 제공 도서
  - 각 책 문서에는 chapters 배열 (제목, 페이지, 음악URL 포함)

  Storage:
  - books/ - 업로드된 책 파일들
  - AI 서버에서 생성된 음악 파일들

  이 서비스는 독서 + 음악 + AI를 결합한 독창적인 몰입형 독서 플랫폼으로, 개인의 취향에 맞는 배경음악으로 독서 경험을
  향상시키는 것이 핵심 가치입니다.