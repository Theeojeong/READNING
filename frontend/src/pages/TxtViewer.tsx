import { useEffect, useState } from "react";
import styled from "styled-components";
import { BASE_AI_URL } from "../api/axiosInstance";

type Chapter = {
  title: string;
  content: string;
};

type Props = {
  txtUrl: string;
  name: string;
  currentIndex: number;
  setCurrentIndex: React.Dispatch<React.SetStateAction<number>>;
  externalAudioRef: React.MutableRefObject<HTMLAudioElement>;
  setIsPlaying: React.Dispatch<React.SetStateAction<boolean>>;
};

// const BASE_AI_URL = "https://5961-114-246-205-231.ngrok-free.app";

export default function TxtViewer({
  txtUrl,
  name,
  externalAudioRef,
  setIsPlaying,
}: Props) {
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loop] = useState(true);
  //const audioRef = useRef(new Audio());
  const audioRef = externalAudioRef;

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
  useEffect(() => {
    if (chapters.length === 0) return;

    const audio = audioRef.current;
    const musicUrl = `${BASE_AI_URL}/gen_musics/${name}/ch${currentPage}.wav`;

    console.log("🎵 음악 URL 설정:", musicUrl);

    audio.pause();
    audio.src = musicUrl;
    audio.loop = loop;
    audio.load();

    audio
      .play()
      .then(() => {
        console.log("자동 재생 시작");
        setIsPlaying(true);
      })
      .catch((err) => console.warn("자동 재생 실패:", err));
  }, [currentPage, chapters, name, loop]);

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

  const next = () => {
    if (currentPage < chapters.length - 1) {
      setCurrentPage((prev) => prev + 1);
    }
  };

  const prev = () => {
    if (currentPage > 0) {
      setCurrentPage((prev) => prev - 1);
    }
  };

  return (
    <Wrapper>
      {chapters.length > 0 ? (
        <>
          <Title>{chapters[currentPage].title}</Title>
          <TextContainer>
            {loading ? (
              <Loading>📚 텍스트 로딩 중...</Loading>
            ) : (
              <TextContent>{chapters[currentPage].content}</TextContent>
            )}
          </TextContainer>

          <Controls>
            <button onClick={() => audioRef.current.play()}>▶ 재생</button>
            <button onClick={() => audioRef.current.pause()}>⏸ 멈춤</button>
            <a
              href={`${BASE_AI_URL}/gen_musics/${name}/ch${currentPage}.wav`}
              download
            >
              ⬇ 다운로드
            </a>
          </Controls>

          <NavButtons>
            <button onClick={prev} disabled={currentPage === 0}>
              ← 이전
            </button>
            <span>
              {currentPage + 1} / {chapters.length}
            </span>
            <button
              onClick={next}
              disabled={currentPage === chapters.length - 1}
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
