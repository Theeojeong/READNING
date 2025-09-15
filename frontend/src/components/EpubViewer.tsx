import { useEffect, useState } from "react";
import styled from "styled-components";

type Props = {
  epubUrl: string;
  name: string;
  currentIndex: number;
  setCurrentIndex: React.Dispatch<React.SetStateAction<number>>;
  externalAudioRef: React.MutableRefObject<HTMLAudioElement>;
  setIsPlaying: React.Dispatch<React.SetStateAction<boolean>>;
};

type Chapter = {
  title: string;
  content: string;
};

export default function EpubViewer({
  epubUrl,
  name: _name,
  currentIndex,
  setCurrentIndex,
  externalAudioRef,
  setIsPlaying: _setIsPlaying,
}: Props) {
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    return () => {
      console.log("📴 EpubViewer 언마운트 - 음악 정지");
      externalAudioRef.current.pause();
      externalAudioRef.current.src = "";
    };
  }, [externalAudioRef]);

  useEffect(() => {
    const loadEpub = async () => {
      if (!epubUrl) return;
      
      setLoading(true);
      setError("");
      
      try {
        // EPUB 파일을 텍스트로 변환하는 로직
        // 실제로는 epub.js 같은 라이브러리를 사용해야 하지만
        // 임시로 텍스트 파일처럼 처리
        const response = await fetch(epubUrl);
        
        if (!response.ok) {
          throw new Error("EPUB 파일을 불러올 수 없습니다.");
        }
        
        // EPUB는 ZIP 형태이므로 직접 텍스트로 읽기 어려움
        // 임시로 에러 처리
        const blob = await response.blob();
        await blob.text(); // EPUB 파싱을 위해 필요하지만 현재는 미사용
        
        // 임시 챕터 데이터 (실제로는 EPUB 파싱 필요)
        const tempChapters: Chapter[] = [
          {
            title: "Chapter 1",
            content: "EPUB 파일 뷰어가 아직 완전히 구현되지 않았습니다. 현재는 기본적인 텍스트 표시만 가능합니다."
          }
        ];
        
        setChapters(tempChapters);
      } catch (err) {
        console.error("EPUB 로드 실패:", err);
        setError("EPUB 파일을 읽을 수 없습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.");
      } finally {
        setLoading(false);
      }
    };

    loadEpub();
  }, [epubUrl]);

  const nextChapter = () => {
    if (currentIndex < chapters.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const prevChapter = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  if (loading) {
    return (
      <Container>
        <LoadingMessage>📖 EPUB 파일을 불러오는 중...</LoadingMessage>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <ErrorMessage>
          ❌ {error}
          <br />
          <small>EPUB 뷰어는 현재 개발 중입니다. PDF나 TXT 파일을 사용해주세요.</small>
        </ErrorMessage>
      </Container>
    );
  }

  if (chapters.length === 0) {
    return (
      <Container>
        <ErrorMessage>📖 EPUB 파일에서 내용을 찾을 수 없습니다.</ErrorMessage>
      </Container>
    );
  }

  const currentChapter = chapters[currentIndex] || chapters[0];

  return (
    <Container>
      <ChapterHeader>
        <ChapterTitle>{currentChapter.title}</ChapterTitle>
        <ChapterInfo>
          {currentIndex + 1} / {chapters.length}
        </ChapterInfo>
      </ChapterHeader>
      
      <ContentArea>
        <ChapterContent>{currentChapter.content}</ChapterContent>
      </ContentArea>

      <NavigationButtons>
        <NavButton onClick={prevChapter} disabled={currentIndex === 0}>
          ← 이전 챕터
        </NavButton>
        <NavButton onClick={nextChapter} disabled={currentIndex === chapters.length - 1}>
          다음 챕터 →
        </NavButton>
      </NavigationButtons>
    </Container>
  );
}

const Container = styled.div`
  width: 100%;
  height: 600px;
  background: white;
  border-radius: 8px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
`;

const LoadingMessage = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 1.2rem;
  color: #666;
`;

const ErrorMessage = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #e74c3c;
  
  small {
    margin-top: 1rem;
    color: #666;
  }
`;

const ChapterHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #eee;
`;

const ChapterTitle = styled.h2`
  margin: 0;
  color: #333;
  font-size: 1.5rem;
`;

const ChapterInfo = styled.span`
  color: #666;
  font-size: 0.9rem;
`;

const ContentArea = styled.div`
  flex: 1;
  overflow-y: auto;
  margin-bottom: 2rem;
`;

const ChapterContent = styled.div`
  line-height: 1.8;
  font-size: 1.1rem;
  color: #333;
  white-space: pre-wrap;
`;

const NavigationButtons = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 1rem;
`;

const NavButton = styled.button`
  padding: 0.8rem 1.5rem;
  background: #5f3dc4;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s ease;

  &:hover:not(:disabled) {
    background: #4c2db3;
  }

  &:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
`;