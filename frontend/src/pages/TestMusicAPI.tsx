import { useState, useRef, ChangeEvent } from "react";
import { BASE_AI_URL } from "../api/axiosInstance";

export default function TestMusicAPI() {
  const [bookId, setBookId] = useState("string");
  const [page, setPage] = useState(1);
  const [preference, setPreference] = useState(
    '["잔잔한 피아노", "자연 소리"]'
  );
  const [response, setResponse] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 🎵 GET 요청 테스트용
  const handleGetAudio = async () => {
    const url = `${BASE_AI_URL}/gen_musics/${bookId}/ch${page}.wav`;
    try {
      const res = await fetch(url);
      if (!res.ok)
        throw new Error(`❌ 오디오 파일을 찾을 수 없습니다: ${res.status}`);
      setAudioUrl(url);
      setResponse("✅ GET 음악 파일 로드 성공!");
    } catch (err: any) {
      console.error("❌ 오류:", err);
      setResponse(err.message);
      setAudioUrl("");
    }
  };

  // 🎵 POST 파일 업로드 요청
  const handlePostUpload = async () => {
    const formData = new FormData();

    if (!selectedFile) {
      alert("파일을 선택하세요.");
      return;
    }

    formData.append("file", selectedFile);
    formData.append("book_id", bookId);
    formData.append("page", String(page));
    formData.append("preference", preference);

    try {
      const res = await fetch(`${BASE_AI_URL}/generate/music-v3`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error(`업로드 실패: ${res.status}`);

      const data = await res.json();
      console.log("POST 응답:", data);
      setResponse(JSON.stringify(data, null, 2));

      const audioPath = `${BASE_AI_URL}/gen_musics/${bookId}/ch${page}.wav`;
      setAudioUrl(audioPath);
    } catch (err: any) {
      console.error("업로드 오류:", err);
      setResponse(err.message);
      setAudioUrl("");
    }

    for (let pair of formData.entries()) {
      console.log(`${pair[0]}:`, pair[1]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handlePlay = () => audioRef.current?.play();
  const handlePause = () => audioRef.current?.pause();

  return (
    <div style={{ padding: "2rem" }}>
      <h2>🎼 AI 서버 음악 생성 테스트</h2>

      {/* 🔧 공통 입력 */}
      <div style={{ marginBottom: "1rem" }}>
        <label>
          📖 book_id:{" "}
          <input
            value={bookId}
            onChange={(e) => setBookId(e.target.value)}
            style={{ marginRight: "1rem" }}
          />
        </label>
        <label>
          📄 page:{" "}
          <input
            type="number"
            value={page}
            onChange={(e) => setPage(Number(e.target.value))}
            style={{ width: "4rem", marginRight: "1rem" }}
          />
        </label>
      </div>

      {/* 🎧 GET 테스트 */}
      <div style={{ marginBottom: "2rem" }}>
        <h3>🟢 GET 요청 테스트</h3>
        <button onClick={handleGetAudio}>🎼 음악 불러오기 (GET)</button>
      </div>

      {/* 📤 POST 업로드 */}
      <div style={{ marginBottom: "2rem" }}>
        <h3>🟣 POST 파일 업로드 테스트</h3>

        <label>
          📖 book_id:{" "}
          <input
            value={bookId}
            onChange={(e) => setBookId(e.target.value)}
            style={{ marginRight: "1rem" }}
          />
        </label>

        <label>
          📄 page:{" "}
          <input
            type="number"
            value={page}
            onChange={(e) => setPage(Number(e.target.value))}
            style={{ width: "4rem", marginRight: "1rem" }}
          />
        </label>

        <br />

        <label>
          🎵 preference:{" "}
          <input
            value={preference}
            onChange={(e) => setPreference(e.target.value)}
            style={{ width: "20rem", margin: "0.5rem 0" }}
          />
        </label>

        <br />

        <input type="file" onChange={handleFileChange} />

        <br />

        <button onClick={handlePostUpload} style={{ marginTop: "1rem" }}>
          📤 파일 업로드 및 요청 (POST)
        </button>
      </div>

      {/* 🔊 오디오 컨트롤 */}
      {audioUrl && (
        <div style={{ marginTop: "2rem" }}>
          <audio
            ref={audioRef}
            src={audioUrl}
            controls
            style={{ display: "none" }}
          />
          <button onClick={handlePlay}>▶ 재생</button>
          <button onClick={handlePause}>⏸ 멈춤</button>
          <a href={audioUrl} download style={{ marginLeft: "1rem" }}>
            ⬇ 다운로드
          </a>
        </div>
      )}

      {/* 🪵 응답 로그 */}
      <pre
        style={{
          marginTop: "2rem",
          background: "#f4f4f4",
          padding: "1rem",
          borderRadius: "8px",
          whiteSpace: "pre-wrap",
        }}
      >
        {response}
      </pre>
    </div>
  );
}
