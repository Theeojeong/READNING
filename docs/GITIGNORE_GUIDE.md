# 📝 .gitignore 가이드

Git에서 추적하지 않는 파일들에 대한 설명입니다.

---

## 🎯 무시되는 파일 카테고리

### 1️⃣ **Python 관련**
```
__pycache__/          # Python 바이트코드 캐시
*.py[cod]             # 컴파일된 Python 파일
*.egg-info/           # 패키지 메타데이터
dist/, build/         # 빌드 결과물
```
**이유**: 자동 생성되며, 소스 코드만 있으면 재생성 가능

---

### 2️⃣ **가상 환경**
```
.venv/, env/, venv/   # Python 가상환경
.python-version       # pyenv 버전 파일
```
**이유**: 각 개발자가 로컬에서 설치, requirements.txt만 있으면 됨

---

### 3️⃣ **IDE/에디터 설정**
```
.vscode/              # VS Code 설정
.idea/                # PyCharm 설정
*.swp, *.swo          # Vim 임시 파일
```
**이유**: 개발자마다 다른 설정 사용, 개인 선호도 반영

---

### 4️⃣ **비밀 정보 (매우 중요!) 🔐**
```
.env                  # 환경 변수 (DB 비밀번호 등)
*.key, *.pem          # 암호화 키
firebase-credentials.json  # Firebase 인증 정보
service-account*.json      # 서비스 계정 키
```
**이유**: **보안상 절대 커밋하면 안 됨!** 공개 시 해킹 위험

⚠️ **주의**: 실수로 커밋했다면 즉시 키를 재발급하고 git history에서 제거!

---

### 5️⃣ **데이터베이스**
```
mysql-data/           # MySQL 데이터 파일
*.db, *.sqlite        # SQLite 데이터베이스
```
**이유**: 
- 로컬 데이터는 개발자마다 다름
- 용량이 크고 자주 변경됨
- 프로덕션 데이터는 백업으로 별도 관리

---

### 6️⃣ **생성된 파일 (음악, 오디오)**
```
gen_musics/           # AI가 생성한 음악 파일
*.wav, *.mp3          # 오디오 파일
!scrollama/audio/*.wav  # 예외: 데모용 샘플은 포함
```
**이유**:
- 용량이 매우 큼 (수백 MB ~ GB)
- API로 재생성 가능
- GitHub 용량 제한 (파일당 100MB, 저장소 1GB)

**예외 처리**: `!scrollama/audio/*.wav`는 데모용 샘플이므로 포함

---

### 7️⃣ **로그 & 임시 파일**
```
*.log                 # 로그 파일
*.tmp, *.temp         # 임시 파일
.pytest_cache/        # 테스트 캐시
.coverage             # 코드 커버리지 데이터
```
**이유**: 런타임에 생성되며 디버깅 후 불필요

---

### 8️⃣ **ML 모델 & 캐시**
```
nltk_data/            # NLTK 데이터 캐시
models/               # 학습된 모델 파일
*.pt, *.pth           # PyTorch 모델
.torch/               # PyTorch 캐시
.audiocraft/          # Audiocraft 캐시
```
**이유**: 
- 모델 파일은 매우 큼 (수 GB)
- Hugging Face 등에서 다운로드 가능
- 자동 캐싱되는 데이터

---

### 9️⃣ **Node.js (프론트엔드)**
```
node_modules/         # npm 패키지
npm-debug.log         # npm 에러 로그
```
**이유**: 
- 용량이 매우 큼 (수백 MB)
- package.json만 있으면 `npm install`로 복원

---

### 🔟 **OS 파일**
```
.DS_Store             # macOS 폴더 메타데이터
Thumbs.db             # Windows 썸네일 캐시
desktop.ini           # Windows 폴더 설정
```
**이유**: OS별 시스템 파일, 프로젝트와 무관

---

### 1️⃣1️⃣ **Docker**
```
docker-compose.override.yml  # 로컬 Docker 오버라이드
```
**이유**: 개발자별 로컬 설정 (포트 변경 등)

---

### 1️⃣2️⃣ **Deprecated / 백업**
```
services/_deprecated/*.pyc  # 삭제 예정 파일들
*.bak, *.backup             # 백업 파일
```
**이유**: 임시 보관용, 나중에 삭제 예정

---

### 1️⃣3️⃣ **테스트 파일 (선택적)**
```
test_*.py             # 개인 테스트 스크립트
!test_mysql_connection.py  # 예외: 공식 테스트는 포함
!test_health_check.py      # 예외: 공식 테스트는 포함
scratch.py            # 스크래치 파일
temp*.py              # 임시 Python 파일
```
**이유**: 
- 개인 실험용 스크립트는 제외
- 공식 테스트 파일은 포함 (`!` 예외 처리)

---

### 1️⃣4️⃣ **사용자 생성 콘텐츠**
```
user_id/              # 사용자별 데이터
uploads/              # 업로드된 파일
uploaded/             # 처리된 업로드 파일
```
**이유**: 런타임에 생성되는 사용자 데이터

---

## ✅ Git에 포함되어야 하는 파일

다음 파일들은 **반드시 커밋**해야 합니다:

### 📄 프로젝트 설정
- ✅ `pyproject.toml` - Python 프로젝트 설정
- ✅ `requirements.txt` - Python 의존성
- ✅ `uv.lock` - 의존성 잠금 파일
- ✅ `package.json` - Node.js 의존성
- ✅ `docker-compose.yml` - Docker 설정

### 📚 문서
- ✅ `README.md` - 프로젝트 설명
- ✅ `QUICKSTART.md` - 빠른 시작 가이드
- ✅ `MYSQL_SETUP.md` - MySQL 설정 가이드
- ✅ `CHANGELOG_*.md` - 변경 로그

### 💻 소스 코드
- ✅ `src/` - 소스 코드
- ✅ `services/` - 서비스 로직
- ✅ `routers/` - API 라우터
- ✅ `utils/` - 유틸리티

### 🎨 프론트엔드
- ✅ `frontend/src/` - React 소스
- ✅ `scrollama/` - Scrollama 라이브러리
- ✅ `public/` - 정적 파일

### 🗄️ 데이터베이스 스키마
- ✅ `init-db.sql` - DB 초기화 스크립트

### 🧪 공식 테스트
- ✅ `test_mysql_connection.py`
- ✅ `test_health_check.py`

---

## 🚨 실수로 커밋한 경우

### 비밀 정보를 커밋했다면:

```bash
# 1. 즉시 키/비밀번호 재발급!
# 2. Git history에서 제거
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 3. 강제 푸시 (주의!)
git push origin --force --all
```

### 대용량 파일을 커밋했다면:

```bash
# Git LFS로 전환 또는 history에서 제거
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch gen_musics/*.wav" \
  --prune-empty --tag-name-filter cat -- --all
```

---

## 📊 .gitignore 적용 확인

### 현재 무시되는 파일 확인:
```bash
git status --ignored
```

### 특정 파일이 무시되는지 확인:
```bash
git check-ignore -v gen_musics/test.wav
# 출력: .gitignore:58:gen_musics/    gen_musics/test.wav
```

### 이미 추적 중인 파일 제거:
```bash
# .gitignore에 추가했지만 이미 커밋된 파일
git rm --cached <file>
git commit -m "Remove tracked file"
```

---

## 🎯 베스트 프랙티스

### 1. **환경 변수 예시 파일 제공**
```bash
# .env는 무시하되, 예시 파일은 제공
cp .env.example .env  # 로컬에서 복사 후 수정
```

### 2. **README에 설정 안내**
```markdown
## 설정

1. `.env` 파일 생성:
   ```bash
   cp .env.example .env
   ```
2. 필요한 값 입력:
   - DATABASE_URL=...
   - API_KEY=...
```

### 3. **대용량 파일은 외부 저장소**
- 음악 파일 → S3, Google Drive
- 모델 파일 → Hugging Face Hub
- 데이터셋 → DVC (Data Version Control)

### 4. **민감한 파일은 암호화**
```bash
# git-crypt 사용
git-crypt init
echo "credentials/ filter=git-crypt diff=git-crypt" >> .gitattributes
```

---

## 📚 참고 자료

- [GitHub .gitignore 템플릿](https://github.com/github/gitignore)
- [Git 공식 문서](https://git-scm.com/docs/gitignore)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) - Git history 정리 도구

---

## 💡 팁

### 전역 .gitignore 설정
개인적으로 모든 프로젝트에서 무시하고 싶은 파일:

```bash
# ~/.gitignore_global
.DS_Store
Thumbs.db
*.swp
.vscode/settings.json
```

적용:
```bash
git config --global core.excludesfile ~/.gitignore_global
```

---

**마지막 업데이트**: 2025-10-07  
**작성자**: AI Assistant

