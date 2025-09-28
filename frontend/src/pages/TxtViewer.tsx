import { useEffect, useRef, useState } from "react";
import styled from "styled-components";
import { BASE_AI_URL } from "../api/axiosInstance";

type Chapter = {
  title: string;
  content: string;
};

type Props = {
  txtUrl: string;
  name: string;
  bookId: string;
  currentIndex: number;
  setCurrentIndex: React.Dispatch<React.SetStateAction<number>>;
  externalAudioRef: React.MutableRefObject<HTMLAudioElement>;
  setIsPlaying: React.Dispatch<React.SetStateAction<boolean>>;
};

// const BASE_AI_URL = "https://5961-114-246-205-231.ngrok-free.app";

export default function TxtViewer({
  txtUrl,
  name,
  bookId,
  currentIndex,
  setCurrentIndex,
  externalAudioRef,
  setIsPlaying,
}: Props) {
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(false);
  const [loop] = useState(true);
  const audioRef = externalAudioRef;
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [chunkItems, setChunkItems] = useState<
    { index: number; audio_url: string; text: string; emotions?: string; next_transition?: any }[]
  >([]);
  const [activeChunk, setActiveChunk] = useState<number>(0);

  useEffect(() => {
    return () => {
      console.log("📴 TxtViewer 언마운트 - 음악 정지");
      audioRef.current.pause();
      audioRef.current.src = "";
    };
  }, []);

  useEffect(() => {
    const fetchText = async () => {
      console.log("텍스트 불러오기 시작:", txtUrl);
      setLoading(true);
      try {
        const response = await fetch(txtUrl);
        const raw = await response.text();
        console.log("텍스트 로드 성공");

        const parsedChapters = parseChapters(raw);
        setChapters(parsedChapters);
        console.log("챕터 파싱 결과:", parsedChapters);
      } catch (err) {
        console.error("텍스트 로드 실패:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchText();
  }, [txtUrl]);

  // 음악 로딩 및 반복 설정
  // 청크 기반: 현재 보이는 청크의 오디오 자동 재생
  useEffect(() => {
    if (chunkItems.length === 0) return;
    const audio = audioRef.current;
    const musicUrl = chunkItems[activeChunk]?.audio_url;
    if (!musicUrl) return;

    console.log("🎵 청크 음악 URL:", musicUrl);
    audio.pause();
    audio.src = musicUrl;
    audio.loop = loop;
    audio.load();
    audio
      .play()
      .then(() => setIsPlaying(true))
      .catch((err) => console.warn("자동 재생 실패:", err));
  }, [activeChunk, chunkItems, loop]);

  // 루프 보조: ended 이벤트로 수동 반복 처리
  useEffect(() => {
    const audio = audioRef.current;

    const handleEnded = () => {
      if (loop) {
        console.log("🔁 재생 끝 → 다시 재생");
        audio.currentTime = 0;
        audio.play();
      }
    };

    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("ended", handleEnded);
    };
  }, [loop]);

  const parseChapters = (text: string): Chapter[] => {
    const lines = text.split(/\r?\n/);
    const chapters: Chapter[] = [];
    let buffer = "";
    let title = "서문";

    const chapterRegex =
      /^(\s)*(제\s?\d+\s?장|[0-9]+\.|Chapter\s+\d+|CHAPTER\s+\d+)/i;

    for (let line of lines) {
      if (chapterRegex.test(line)) {
        if (buffer.trim()) {
          chapters.push({
            title,
            content: buffer.trim(),
          });
          buffer = "";
        }
        title = line.trim();
      }
      buffer += line + "\n";
    }

    if (buffer.trim()) {
      chapters.push({
        title,
        content: buffer.trim(),
      });
    }

    return chapters;
  };

  // IntersectionObserver로 보이는 청크 추적
  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;

    const sections = Array.from(container.querySelectorAll('[data-chunk-index]')) as HTMLElement[];
    if (sections.length === 0) return;

    const obs = new IntersectionObserver(
      (entries) => {
        // 가장 크게 보이는 섹션 선택
        const top = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (!top) return;
        const idxAttr = (top.target as HTMLElement).dataset.chunkIndex;
        if (idxAttr == null) return;
        const idx = Number(idxAttr);
        setActiveChunk((prev) => (prev !== idx ? idx : prev));
      },
      { root: container, threshold: [0.2, 0.4, 0.6, 0.8] }
    );

    sections.forEach((sec) => obs.observe(sec));
    return () => obs.disconnect();
  }, [chunkItems.length]);

  // 현재 챕터에 대한 청크 메타 요청
  useEffect(() => {
    const generateChunks = async () => {
      if (!bookId || chapters.length === 0) return;
      const ch = chapters[currentIndex];
      if (!ch) return;
      try {
        const fd = new FormData();
        fd.append("book_id", bookId);
        fd.append("chapter_index", String(currentIndex));
        fd.append("chapter_title", ch.title);
        fd.append("text", ch.content);

        const resp = await fetch(`${BASE_AI_URL}/generate/music-by-chapter`, {
          method: "POST",
          body: fd,
        });
        if (!resp.ok) throw new Error(`AI 서버 오류: ${resp.status}`);
        const data = await resp.json();
        setChunkItems(data.chunks || []);
        setActiveChunk(0);
      } catch (e) {
        console.error("청크 생성 실패", e);
      }
    };
    generateChunks();
  }, [bookId, currentIndex, chapters]);

  return (
    <Wrapper>
      {chapters.length > 0 ? (
        <>
          <Title>{chapters[currentIndex].title}</Title>
          <TextContainer ref={scrollRef}>
            {loading ? (
              <Loading>📚 텍스트 로딩 중...</Loading>
            ) : chunkItems.length > 0 ? (
              <>
                {chunkItems.map((ck) => (
                  <ChunkSection key={ck.index} data-chunk-index={ck.index}>
                    <ChunkHeader>
                      <span>청크 {ck.index + 1}</span>
                      {ck.emotions && <em>{ck.emotions}</em>}
                    </ChunkHeader>
                    <TextContent>{ck.text}</TextContent>
                  </ChunkSection>
                ))}
              </>
            ) : (
              <TextContent>{chapters[currentIndex].content}</TextContent>
            )}
          </TextContainer>

          <Controls>
            <button onClick={() => audioRef.current.play()}>▶ 재생</button>
            <button onClick={() => audioRef.current.pause()}>⏸ 멈춤</button>
          </Controls>

          <NavButtons>
            <button onClick={() => setCurrentIndex((v) => Math.max(0, v - 1))} disabled={currentIndex === 0}>
              ← 이전
            </button>
            <span>
              {currentIndex + 1} / {chapters.length}
            </span>
            <button
              onClick={() => setCurrentIndex((v) => Math.min(chapters.length - 1, v + 1))}
              disabled={currentIndex === chapters.length - 1}
            >
              다음 →
            </button>
          </NavButtons>
        </>
      ) : (
        <Loading>📄 텍스트 로딩 중...</Loading>
      )}
    </Wrapper>
  );
}

const Wrapper = styled.div`
  width: 100%;
  max-width: 768px;
  margin: 2rem auto;
  padding: 2rem 2rem 3rem;
  background-color: #fff;
  border-radius: 12px;
  font-family: "Georgia", serif;
  line-height: 1.75;
  user-select: none;
  box-sizing: border-box; //레이아웃
`;

const Title = styled.h2`
  font-size: 1.75rem;
  color: #4b3f2f;
  margin-bottom: 1.25rem;
  border-left: 5px solid #7c5dfa;
  padding-left: 1rem;
`;

const TextContainer = styled.div`
  padding: 1.5rem;
  background-color: #fafafa;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  max-height: 600px;
  overflow-y: auto;
  font-size: 1.05rem;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
`;

const TextContent = styled.div`
  white-space: pre-wrap;
  word-break: break-word;
`;

const ChunkSection = styled.section`
  padding: 1rem 0;
  border-bottom: 1px dashed #e0e0f5;
`;

const ChunkHeader = styled.div`
  display: flex;
  justify-content: space-between;
  color: #6b6b6b;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;

  em {
    font-style: normal;
    color: #5f3dc4;
  }
`;

const NavButtons = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;

  button {
    background: #e8e8f9;
    color: #5f3dc4;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  span {
    font-size: 1rem;
    color: #666;
  }
`;

const Loading = styled.div`
  font-size: 1rem;
  color: #aaa;
  text-align: center;
  padding: 2rem 0;
`;

const Controls = styled.div`
  margin-top: 2rem;
  display: flex;
  gap: 1rem;
  justify-content: center;

  button,
  a {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: #7c5dfa;
    color: white;
    border: none;
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    text-decoration: none;
    cursor: pointer;
    font-weight: 500;
    transition: background 0.2s;
    justify-content: center;

    &:hover {
      background: #6547c2;
    }
  }
`;
