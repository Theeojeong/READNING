import { useLocation } from "react-router-dom";
import { useEffect, useState, useRef } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import styled from "styled-components";
import { doc, getDoc, getFirestore } from "firebase/firestore";
import { app } from "@/utils/firebase";
import TxtViewer from "./TxtViewer";
import EpubViewer from "../components/EpubViewer";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { BASE_AI_URL } from "../api/axiosInstance";
import {
  saveReadingProgress,
  getReadingProgress,
  updateReadingTime,
} from "@/utils/readingProgress";
import { getUserMusicPreferences } from "@/utils/musicPreferences";

pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

type Chapter = {
  title: string;
  page: number;
  musicUrl: string;
};

type Book = {
  id: string;
  title: string;
  author: string;
  pdfUrl: string;
  name: string;
};

export default function ReaderPage() {
  // const BASE_AI_URL = "https://5961-114-246-205-231.ngrok-free.app";

  const { state } = useLocation();
  const book = state?.book as Book;
  const db = getFirestore(app);

  const [pageNumber, setPageNumber] = useState(1);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const audioRef = useRef(new Audio());
  const [pdfUrl, setPdfUrl] = useState<string | undefined>(book?.pdfUrl);
  const [txtCurrentChapter, setTxtCurrentChapter] = useState(0);
  const urlToCheck = book?.pdfUrl ?? pdfUrl ?? "";
  const isTxtFile =
    urlToCheck.includes("books%2Ftxt%2F") || urlToCheck.includes(".txt");
  const isEpubFile = urlToCheck.includes(".epub");
  const isPdfFile = urlToCheck.includes(".pdf");
  const startTimeRef = useRef<Date>(new Date());
  const [isGeneratingMusic, setIsGeneratingMusic] = useState(false);
  const [userPreferences, setUserPreferences] = useState<string[]>([]);

  useEffect(() => {
    if (book?.pdfUrl || isTxtFile || isEpubFile) return;
    const loadFromIndexedDB = async () => {
      const dbReq = window.indexedDB.open("MyBookStorage");
      dbReq.onsuccess = () => {
        const db = dbReq.result;
        const tx = db.transaction("pdfs", "readonly");
        const store = tx.objectStore("pdfs");
        const getReq = store.get(book.id);
        getReq.onsuccess = () => {
          const file = getReq.result?.file;
          if (file) {
            const url = URL.createObjectURL(file);
            setPdfUrl(url);
          }
        };
      };
    };
    loadFromIndexedDB();
  }, [book?.id, book?.pdfUrl, isTxtFile, isEpubFile]);

  // 마지막 읽은 위치 복원
  useEffect(() => {
    const restoreReadingPosition = async () => {
      if (!book?.id) return;

      const progress = await getReadingProgress(book.id);
      if (progress) {
        if (progress.currentPage && isPdfFile) {
          setPageNumber(progress.currentPage);
        } else if (
          progress.currentChapter !== undefined &&
          (isTxtFile || isEpubFile)
        ) {
          setTxtCurrentChapter(progress.currentChapter);
        }
      }
    };

    restoreReadingPosition();
  }, [book?.id, isTxtFile, isEpubFile, isPdfFile]);

  // 읽기 시간 추적
  useEffect(() => {
    const interval = setInterval(() => {
      if (book?.id) {
        const now = new Date();
        const diffInMinutes = Math.floor(
          (now.getTime() - startTimeRef.current.getTime()) / (1000 * 60)
        );
        if (diffInMinutes > 0) {
          updateReadingTime(book.id, diffInMinutes);
          startTimeRef.current = now;
        }
      }
    }, 60000); // 1분마다 체크

    return () => clearInterval(interval);
  }, [book?.id]);

  // 페이지/챕터 변경 시 진행률 저장
  useEffect(() => {
    if (book?.id) {
      if (isTxtFile || isEpubFile) {
        saveReadingProgress(
          book.id,
          undefined,
          undefined,
          txtCurrentChapter,
          chapters.length
        );
      } else if (isPdfFile && numPages) {
        saveReadingProgress(book.id, pageNumber, numPages);
      }
    }
  }, [
    book?.id,
    pageNumber,
    numPages,
    txtCurrentChapter,
    chapters.length,
    isTxtFile,
    isEpubFile,
    isPdfFile,
  ]);

  // 사용자 음악 취향 로드
  useEffect(() => {
    const loadUserPreferences = async () => {
      const preferences = await getUserMusicPreferences();
      setUserPreferences(preferences);
    };
    loadUserPreferences();
  }, []);

  // 개인화된 음악 생성 함수
  const generatePersonalizedMusic = async (
    chapterIndex: number,
    chapterTitle: string
  ) => {
    if (!book?.id || isGeneratingMusic) return null;

    setIsGeneratingMusic(true);
    try {
      const formData = new FormData();

      // PDF/TXT 파일 추가 (필요한 경우)
      if (pdfUrl) {
        const response = await fetch(pdfUrl);
        const blob = await response.blob();
        const file = new File([blob], `${book.name || book.id}.pdf`, {
          type: blob.type,
        });
        formData.append("file", file);
      }

      formData.append("book_id", book.id);
      formData.append("page", String(chapterIndex + 1));
      formData.append("chapter_title", chapterTitle);
      formData.append("preference", JSON.stringify(userPreferences));

      const response = await fetch(`${BASE_AI_URL}/generate/music-v3`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`AI 서버 응답 오류: ${response.status}`);
      }

      await response.json(); // AI 서버 응답 확인용
      return `${BASE_AI_URL}/gen_musics/${book.id}/ch${chapterIndex}.wav`;
    } catch (error) {
      console.error("개인화된 음악 생성 실패:", error);
      return null;
    } finally {
      setIsGeneratingMusic(false);
    }
  };

  useEffect(() => {
    const fetchChapters = async () => {
      if (!book?.id) return;
      const docSnap = await getDoc(doc(db, "books", book.id));
      if (docSnap.exists()) {
        const data = docSnap.data();
        if (data.chapters) {
          const converted = data.chapters.map((ch: any) => ({
            ...ch,
            page: Number(ch.page),
          }));
          setChapters(converted);

          // 첫 번째 챕터의 개인화된 음악 생성 및 재생
          if (converted[0] && userPreferences.length > 0) {
            generatePersonalizedMusic(0, converted[0].title).then(
              (musicUrl) => {
                if (musicUrl) {
                  audioRef.current.src = musicUrl;
                  audioRef.current.play();
                }
              }
            );
          } else if (converted[0]?.musicUrl) {
            // 기존 음악이 있는 경우 기본값으로 사용
            audioRef.current.src = converted[0].musicUrl;
            audioRef.current.play();
          }
        }
      }
    };

    // 사용자 취향이 로드된 후에 챕터 로드
    if (userPreferences.length >= 0) {
      fetchChapters();
    }
  }, [book?.id, userPreferences]);

  useEffect(() => {
    const matched = chapters
      .slice()
      .reverse()
      .find((ch) => ch.page <= pageNumber);

    if (matched) {
      const chapterIndex = chapters.findIndex((ch) => ch === matched);

      // 사용자 취향이 있으면 개인화된 음악 생성, 없으면 기본 음악 사용
      if (userPreferences.length > 0) {
        generatePersonalizedMusic(chapterIndex, matched.title).then(
          (musicUrl) => {
            if (musicUrl && musicUrl !== audioRef.current.src) {
              audioRef.current.src = musicUrl;
              if (isPlaying) audioRef.current.play();
            }
          }
        );
      } else if (matched.musicUrl !== audioRef.current.src) {
        audioRef.current.src = matched.musicUrl;
        if (isPlaying) audioRef.current.play();
      }
    }
  }, [pageNumber, chapters, userPreferences]);

  const handleDocumentLoad = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const nextPage = () =>
    setPageNumber((prev) => Math.min(prev + 1, numPages ?? prev));
  const prevPage = () => setPageNumber((prev) => Math.max(prev - 1, 1));

  return (
    <Container>
      <Navbar />
      <Layout>
        <Hamburger onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? "×" : "☰"}
        </Hamburger>

        {sidebarOpen && (
          <Sidebar>
            <SidebarHeader>
              <BookInfo>
                <BookTitle>{book.title}</BookTitle>
                <BookAuthor>{book.author}</BookAuthor>
              </BookInfo>
              {/* <CloseButton onClick={() => setSidebarOpen(false)}>×</CloseButton> */}
            </SidebarHeader>
            <ChapterTitle>📚 목차</ChapterTitle>
            <ul>
              {chapters.map((ch, idx) => {
                const defaultMusicUrl =
                  isTxtFile || isEpubFile
                    ? `${BASE_AI_URL}/gen_musics/${book.name}/ch${idx}.wav`
                    : ch.musicUrl;

                return (
                  <li key={idx}>
                    <span
                      onClick={() => {
                        if (isTxtFile || isEpubFile) {
                          setTxtCurrentChapter(idx);
                        } else {
                          setPageNumber(Number(ch.page));
                        }
                      }}
                    >
                      {ch.title}
                    </span>
                    <div className="chapter-controls">
                      <button
                        onClick={async () => {
                          const audio = audioRef.current;
                          audio.pause();

                          // 사용자 취향이 있으면 개인화된 음악 생성
                          if (userPreferences.length > 0) {
                            const personalizedUrl =
                              await generatePersonalizedMusic(idx, ch.title);
                            if (personalizedUrl) {
                              audio.src = personalizedUrl;
                              audio.play();
                              setIsPlaying(true);
                            }
                          } else if (defaultMusicUrl) {
                            audio.src = defaultMusicUrl;
                            audio.play();
                            setIsPlaying(true);
                          }
                        }}
                        disabled={isGeneratingMusic}
                      >
                        {isGeneratingMusic
                          ? "🎵"
                          : audioRef.current.src.includes(`ch${idx}`) &&
                            isPlaying
                          ? "⏸"
                          : "▶"}
                      </button>
                      <a
                        href={
                          userPreferences.length > 0
                            ? `${BASE_AI_URL}/gen_musics/${book.id}/ch${idx}.wav`
                            : defaultMusicUrl
                        }
                        download
                      >
                        ⬇
                      </a>
                    </div>
                  </li>
                );
              })}
            </ul>
            <MusicControls>
              <button
                onClick={() => {
                  const audio = audioRef.current;
                  if (isPlaying) {
                    audio.pause();
                  } else {
                    audio.play();
                  }
                  setIsPlaying(!isPlaying);
                }}
              >
                {isPlaying ? "⏸️ 멈춤" : "▶️ 재생"}
              </button>
              <a href={audioRef.current.src} download>
                🎵 전체 음악 다운로드
              </a>
            </MusicControls>
          </Sidebar>
        )}

        <Main>
          <PdfContainer>
            {isTxtFile && pdfUrl ? (
              <TxtViewer
                key={book.id}
                txtUrl={pdfUrl}
                name={book.name}
                currentIndex={txtCurrentChapter}
                setCurrentIndex={setTxtCurrentChapter}
                externalAudioRef={audioRef}
                setIsPlaying={setIsPlaying}
              />
            ) : isEpubFile && pdfUrl ? (
              <EpubViewer
                key={book.id}
                epubUrl={pdfUrl}
                name={book.name}
                currentIndex={txtCurrentChapter}
                setCurrentIndex={setTxtCurrentChapter}
                externalAudioRef={audioRef}
                setIsPlaying={setIsPlaying}
              />
            ) : isPdfFile && pdfUrl ? (
              <Document file={pdfUrl} onLoadSuccess={handleDocumentLoad}>
                <Page
                  key={pageNumber}
                  pageNumber={pageNumber}
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                />
              </Document>
            ) : (
              <p>문서를 불러올 수 없습니다.</p>
            )}
          </PdfContainer>

          {isPdfFile && (
            <NavButtons>
              <button onClick={prevPage} disabled={pageNumber === 1}>
                ← 이전
              </button>
              <span>
                {pageNumber} / {numPages ?? "?"}
              </span>
              <button onClick={nextPage} disabled={pageNumber === numPages}>
                다음 →
              </button>
            </NavButtons>
          )}
        </Main>
      </Layout>
      <Footer />
    </Container>
  );
}

const Container = styled.div`
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 1400px;
  user-select: none;
  margin: 0 auto;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);

  @media (max-width: 768px) {
    max-width: 100%;
  }
`;

const Layout = styled.div`
  display: flex;
  position: relative;
  width: 100%;
  flex: 1;
`;

const Hamburger = styled.button`
  position: fixed;
  top: 5rem;
  left: 2rem;
  z-index: 1001;
  width: 50px;
  height: 50px;
  background: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;

  @media (max-width: 768px) {
    top: 1.5rem;
    left: 1.5rem;
    width: 45px;
    height: 45px;
    font-size: 1.3rem;
  }

  @media (max-width: 480px) {
    top: 1rem;
    left: 1rem;
    width: 40px;
    height: 40px;
    font-size: 1.2rem;
  }

  &:hover {
    background: #667eea;
    color: white;
    transform: scale(1.05);
  }
`;

const Sidebar = styled.aside`
  position: fixed;
  top: 0;
  left: 0;
  width: 350px;
  height: 100vh;
  background: white;
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(102, 126, 234, 0.1);
  padding: 2rem;
  z-index: 1000;
  overflow-y: auto;
  box-shadow: 0 0 50px rgba(0, 0, 0, 0.1);
  transform: translateX(0);
  transition: transform 0.3s ease;

  @media (max-width: 768px) {
    width: 300px;
    padding: 1.5rem;
  }

  @media (max-width: 480px) {
    width: 280px;
    padding: 1rem;
  }

  ul {
    list-style: none;
    padding: 0;
    margin-top: 2rem;

    li {
      background: rgba(102, 126, 234, 0.05);
      border-radius: 12px;
      padding: 1rem;
      margin-bottom: 1rem;
      transition: all 0.3s ease;

      &:hover {
        background: rgba(102, 126, 234, 0.1);
        transform: translateY(-2px);
      }

      span {
        cursor: pointer;
        color: #333;
        font-weight: 600;
        font-size: 1rem;
        display: block;
        margin-bottom: 0.5rem;

        &:hover {
          color: #667eea;
        }
      }

      .chapter-controls {
        display: flex;
        gap: 0.5rem;

        button,
        a {
          background: #667eea;
          color: white;
          border: none;
          padding: 0.5rem 0.8rem;
          border-radius: 8px;
          font-size: 0.9rem;
          cursor: pointer;
          transition: all 0.2s ease;
          text-decoration: none;
          display: flex;
          align-items: center;
          justify-content: center;

          &:hover {
            background: #764ba2;
            transform: scale(1.05);
          }

          &:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
          }
        }
      }
    }
  }
`;

const MusicControls = styled.div`
  margin-top: 2rem;
  padding: 1.5rem;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 1rem;

  button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
    font-size: 1rem;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
  }

  a {
    text-decoration: none;
    color: #667eea;
    font-weight: 600;
    text-align: center;
    padding: 0.5rem;
    transition: color 0.3s ease;

    &:hover {
      color: #764ba2;
    }
  }
`;

const Main = styled.main`
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
  box-sizing: border-box;
  transition: margin-left 0.3s ease;

  @media (max-width: 768px) {
    padding: 1rem;
    max-width: 100%;
  }

  @media (max-width: 480px) {
    padding: 0.8rem;
  }
`;

const SidebarHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid rgba(102, 126, 234, 0.1);
`;

const BookInfo = styled.div`
  margin-top: 7rem;
  flex: 1;
`;

const BookTitle = styled.h2`
  color: #333;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  line-height: 1.3;

  @media (max-width: 768px) {
    font-size: 1.3rem;
  }

  @media (max-width: 480px) {
    font-size: 1.2rem;
  }
`;

const BookAuthor = styled.p`
  color: #666;
  font-size: 1rem;
  margin: 0;

  @media (max-width: 768px) {
    font-size: 0.9rem;
  }

  @media (max-width: 480px) {
    font-size: 0.8rem;
  }
`;


const ChapterTitle = styled.h3`
  color: #333;
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
`;


const PdfContainer = styled.div`
  background: white;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.1);
  overflow: hidden;

  @media (max-width: 768px) {
    padding: 1.5rem;
    border-radius: 16px;
  }

  @media (max-width: 480px) {
    padding: 1rem;
    border-radius: 12px;
    margin: 0 -0.5rem;
  }

  /* PDF 반응형 처리 */
  .react-pdf__Document {
    @media (max-width: 768px) {
      max-width: 100%;
    }
  }

  .react-pdf__Page {
    @media (max-width: 768px) {
      max-width: 100% !important;
      height: auto !important;
    }
  }

  .react-pdf__Page__canvas {
    @media (max-width: 768px) {
      max-width: 100% !important;
      height: auto !important;
    }
  }
`;

const NavButtons = styled.div`
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;

  @media (max-width: 768px) {
    gap: 0.8rem;
    margin-top: 1.5rem;
  }

  @media (max-width: 480px) {
    gap: 0.5rem;
    margin-top: 1rem;
    flex-wrap: wrap;
  }

  button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    min-width: 120px;

    @media (max-width: 768px) {
      padding: 0.8rem 1.5rem;
      font-size: 0.9rem;
      min-width: 100px;
    }

    @media (max-width: 480px) {
      padding: 0.7rem 1rem;
      font-size: 0.8rem;
      min-width: 80px;
      border-radius: 8px;
    }

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }

    &:disabled {
      background: #ccc;
      cursor: not-allowed;
      transform: none;
    }
  }

  span {
    display: flex;
    align-items: center;
    color: #333;
    font-weight: 600;
    font-size: 1.1rem;

    @media (max-width: 768px) {
      font-size: 1rem;
    }

    @media (max-width: 480px) {
      font-size: 0.9rem;
    }
  }
`;
