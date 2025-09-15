import { useRef, useState } from "react";
import styled from "styled-components";
import { doc, setDoc } from "firebase/firestore";
import { db } from "@/utils/firebase";
import { getStorage, ref, uploadBytes, getDownloadURL } from "firebase/storage";

export default function UploadSection() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [coverUrl, setCoverUrl] = useState("");
  const [musicPreferences, setMusicPreferences] = useState<string[]>([]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    const validTypes = [
      "application/pdf",
      "text/plain",
      "application/epub+zip",
    ];
    const validExtensions = [".pdf", ".txt", ".epub"];

    const ext = f.name.slice(f.name.lastIndexOf(".")).toLowerCase();
    const isValid =
      validTypes.includes(f.type) || validExtensions.includes(ext);

    if (isValid) {
      setFile(f);
      setShowModal(true);
    } else {
      alert("PDF, TXT 또는 EPUB 파일만 업로드할 수 있습니다.");
    }
  };

  const handleSubmit = async () => {
    const uid = localStorage.getItem("user_uid");
    if (!uid || !file) return;

    const id = `user-${Date.now()}`;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("book_id", id);
    formData.append("preference", JSON.stringify(musicPreferences));

    console.log(file);
    console.log(id);
    console.log(musicPreferences);
    console.log(JSON.stringify(musicPreferences));

    try {
      const res = await fetch(
        "https://rjnrbqepcwsbaegk.tunnel.elice.io/proxy/8000/generate/music-v3",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!res.ok) throw new Error("AI 서버 응답 실패");

      const { chapters } = await res.json(); // 📥 챕터 정보 자동 생성 결과

      // 1️⃣ Firebase Storage에 업로드
      const storage = getStorage();
      const ext = file.name.split(".").pop();
      const fileRef = ref(storage, `books/${id}.${ext}`);
      await uploadBytes(fileRef, file);
      const fileUrl = await getDownloadURL(fileRef);

      // 2️⃣ Firestore에 메타데이터 저장
      await setDoc(doc(db, "users", uid, "books", id), {
        id,
        title,
        author,
        isAI: true,
        pdfUrl: fileUrl,
        coverUrl: coverUrl || "https://via.placeholder.com/150",
        chapters,
        uploadedAt: new Date(),
      });

      alert("✅ 업로드 완료!");
      setShowModal(false);
    } catch (err) {
      console.error("❌ 에러 발생:", err);
      alert("업로드 중 오류가 발생했습니다.");
    }
  };

  const musicOptions = [
    "잔잔한 피아노",
    "자연 소리",
    "클래식",
    "재즈",
    "일렉트로닉",
    "몰입형 사운드",
  ];

  return (
    <Wrapper>
      <Title>📚 새로운 책 추가하기</Title>
      <Subtitle>PDF, TXT, EPUB 파일을 업로드하고 AI 음악과 함께 독서를 시작하세요</Subtitle>
      <DropZone
        onDragOver={(e: React.DragEvent<HTMLDivElement>) => {
          e.preventDefault();
        }}
        onDrop={(e: React.DragEvent<HTMLDivElement>) => {
          e.preventDefault();
          const dropped = e.dataTransfer.files[0];
          if (dropped) {
            const validTypes = [
              "application/pdf",
              "text/plain", 
              "application/epub+zip"
            ];
            const ext = dropped.name.slice(dropped.name.lastIndexOf(".")).toLowerCase();
            const validExtensions = [".pdf", ".txt", ".epub"];
            
            const isValid = validTypes.includes(dropped.type) || validExtensions.includes(ext);
            
            if (isValid) {
              setFile(dropped);
              setShowModal(true);
            } else {
              alert("PDF, TXT 또는 EPUB 파일만 업로드할 수 있습니다.");
            }
          }
        }}
      >
        <UploadIcon>📁</UploadIcon>
        <UploadTitle>파일을 여기에 드래그하거나</UploadTitle>
        <AttachButton onClick={() => fileInputRef.current?.click()}>
          <ButtonIcon>📤</ButtonIcon>
          파일 선택하기
        </AttachButton>
        <SupportText>지원 형식: PDF, TXT, EPUB (최대 50MB)</SupportText>
        <HiddenInput
          type="file"
          ref={fileInputRef}
          accept=".pdf,.txt,.epub"
          onChange={handleFileUpload}
        />
      </DropZone>

      {showModal && (
        <ModalBackdrop>
          <Modal>
            <ModalHeader>
              <h3>책 정보 입력</h3>
              <CloseBtn onClick={() => setShowModal(false)}>✖</CloseBtn>
            </ModalHeader>

            <input
              placeholder="책 제목"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <input
              placeholder="작가"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
            />
            <input
              placeholder="표지 이미지 URL (선택)"
              value={coverUrl}
              onChange={(e) => setCoverUrl(e.target.value)}
            />

            <h4>🎧 원하는 음악 스타일 선택</h4>
            <CheckboxGroup>
              {musicOptions.map((option) => (
                <label key={option}>
                  <input
                    type="checkbox"
                    checked={musicPreferences.includes(option)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setMusicPreferences([...musicPreferences, option]);
                      } else {
                        setMusicPreferences(
                          musicPreferences.filter((o) => o !== option)
                        );
                      }
                    }}
                  />
                  {option}
                </label>
              ))}
            </CheckboxGroup>

            <SubmitBtn onClick={handleSubmit}>✅ 저장하기</SubmitBtn>
          </Modal>
        </ModalBackdrop>
      )}
    </Wrapper>
  );
}

// 스타일 정의
const Wrapper = styled.section`
  width: 100%;
  max-width: 800px;
  margin: 3rem auto 0;
  text-align: center;
  padding: 0;
  box-sizing: border-box;

  @media (max-width: 768px) {
    max-width: 100%;
    margin-top: 2rem;
  }

  @media (max-width: 480px) {
    margin-top: 1.5rem;
  }

  @media (max-width: 375px) {
    margin-top: 1.2rem;
  }

  @media (max-width: 320px) {
    margin-top: 1rem;
  }
`;

const Title = styled.h2`
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
  text-align: center;

  @media (max-width: 768px) {
    font-size: 1.7rem;
  }

  @media (max-width: 480px) {
    font-size: 1.5rem;
  }
`;

const Subtitle = styled.p`
  color: #666;
  font-size: 1rem;
  text-align: center;
  margin-bottom: 3rem;

  @media (max-width: 768px) {
    font-size: 0.9rem;
    margin-bottom: 2rem;
  }

  @media (max-width: 480px) {
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
  }

  @media (max-width: 320px) {
    font-size: 0.8rem;
    margin-bottom: 1rem;
  }
`;

const DropZone = styled.div`
  padding: 4rem 2rem;
  border: 2px dashed #667eea;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  transition: all 0.3s ease;
  text-align: center;
  position: relative;
  overflow: hidden;
  margin: 0 auto;
  max-width: 100%;

  @media (max-width: 768px) {
    padding: 3rem 1.5rem;
    border-radius: 16px;
  }

  @media (max-width: 480px) {
    padding: 2.5rem 1.2rem;
    border-radius: 14px;
  }

  @media (max-width: 375px) {
    padding: 2rem 1rem;
    border-radius: 12px;
  }

  @media (max-width: 320px) {
    padding: 1.8rem 0.8rem;
    border-radius: 10px;
  }

  &:hover {
    border-color: #764ba2;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    transform: translateY(-2px);
  }

  &::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: conic-gradient(transparent, rgba(102, 126, 234, 0.1), transparent 30%);
    animation: rotate 4s linear infinite;
    z-index: 0;
  }

  & > * {
    position: relative;
    z-index: 1;
  }

  @keyframes rotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;

  h3 {
    margin: 0;
  }
`;

const CloseBtn = styled.button`
  background: transparent;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
`;

const CheckboxGroup = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.6rem;

  @media (max-width: 480px) {
    gap: 0.5rem;
  }

  label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.95rem;

    @media (max-width: 480px) {
      font-size: 0.9rem;
    }
  }

  input[type="checkbox"] {
    width: 16px;
    height: 16px;

    @media (max-width: 480px) {
      width: 18px;
      height: 18px;
    }
  }
`;

const UploadIcon = styled.div`
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.7;

  @media (max-width: 768px) {
    font-size: 3.5rem;
  }

  @media (max-width: 480px) {
    font-size: 3rem;
    margin-bottom: 0.8rem;
  }
`;

const UploadTitle = styled.h3`
  font-size: 1.2rem;
  color: #333;
  margin-bottom: 1.5rem;
  font-weight: 600;

  @media (max-width: 768px) {
    font-size: 1.1rem;
  }

  @media (max-width: 480px) {
    font-size: 1rem;
    margin-bottom: 1rem;
  }
`;

const AttachButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 2rem;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  margin-bottom: 1rem;

  @media (max-width: 768px) {
    padding: 0.8rem 1.5rem;
    font-size: 0.9rem;
  }

  @media (max-width: 480px) {
    padding: 0.7rem 1.2rem;
    font-size: 0.85rem;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
  }
`;

const ButtonIcon = styled.span`
  font-size: 1.1rem;
`;

const HiddenInput = styled.input`
  display: none;
`;

const SupportText = styled.p`
  color: #888;
  font-size: 0.9rem;
  margin: 0;

  @media (max-width: 480px) {
    font-size: 0.8rem;
  }
`;

const ModalBackdrop = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
`;

const Modal = styled.div`
  background: white;
  padding: 2rem;
  width: 400px;
  max-width: 90vw;
  margin: 5rem auto;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-sizing: border-box;

  @media (max-width: 768px) {
    width: 90%;
    max-width: 500px;
    padding: 1.8rem;
    margin: 3rem auto;
  }

  @media (max-width: 480px) {
    width: 95%;
    max-width: 95vw;
    padding: 1.5rem;
    margin: 2.5rem auto;
    border-radius: 12px;
  }

  @media (max-width: 375px) {
    padding: 1.2rem;
    margin: 2rem auto;
    border-radius: 10px;
  }

  @media (max-width: 320px) {
    padding: 1rem;
    margin: 1.5rem auto;
    border-radius: 8px;
  }

  input {
    width: 100%;
    padding: 0.8rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-sizing: border-box;
    font-size: 1rem;
    transition: border-color 0.2s ease;

    &:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
    }

    @media (max-width: 480px) {
      padding: 0.7rem;
      font-size: 0.9rem;
    }

    @media (max-width: 320px) {
      padding: 0.6rem;
      font-size: 0.85rem;
    }
  }

  h3 {
    margin: 0;
    color: #333;
    font-size: 1.3rem;
    font-weight: 700;

    @media (max-width: 480px) {
      font-size: 1.2rem;
    }

    @media (max-width: 320px) {
      font-size: 1.1rem;
    }
  }

  h4 {
    margin: 1rem 0 0.5rem 0;
    color: #555;
    font-size: 1.1rem;
    font-weight: 600;

    @media (max-width: 480px) {
      font-size: 1rem;
    }

    @media (max-width: 320px) {
      font-size: 0.95rem;
    }
  }
`;

const SubmitBtn = styled.button`
  background: #5f3dc4;
  color: white;
  font-weight: bold;
  border: none;
  border-radius: 6px;
  padding: 0.6rem;
  cursor: pointer;
  transition: all 0.2s ease;

  @media (max-width: 480px) {
    padding: 0.8rem;
    font-size: 0.9rem;
  }

  &:hover {
    background: #4a2faf;
  }
`;
