import { BASE_AI_URL } from "@/api/axiosInstance";
import { auth, db } from "./firebase";
import { doc, getDoc } from "firebase/firestore";

export interface MusicGenerationRequest {
  bookTitle: string;
  chapterTitle: string;
  chapterContent: string;
  userPreferences: string[];
}

export async function getUserMusicPreferences(): Promise<string[]> {
  const user = auth.currentUser;
  if (!user) return [];

  try {
    const userDoc = await getDoc(doc(db, "users", user.uid));
    if (userDoc.exists()) {
      return userDoc.data().musicPreferences || [];
    }
    return [];
  } catch (error) {
    console.error("음악 취향 가져오기 실패:", error);
    return [];
  }
}

export async function generateMusicWithPreferences(
  request: MusicGenerationRequest
): Promise<string | null> {
  try {
    const preferencesText = request.userPreferences.length > 0 
      ? `사용자 음악 취향: ${request.userPreferences.join(", ")}`
      : "사용자 음악 취향: 일반적";

    const response = await fetch(`${BASE_AI_URL}/generate-music`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        bookTitle: request.bookTitle,
        chapterTitle: request.chapterTitle,
        chapterContent: request.chapterContent,
        musicPreferences: preferencesText,
      }),
    });

    if (!response.ok) {
      throw new Error(`AI 서버 응답 오류: ${response.status}`);
    }

    const data = await response.json();
    return data.musicUrl || null;
  } catch (error) {
    console.error("AI 음악 생성 실패:", error);
    return null;
  }
}

export function createMusicPrompt(
  bookTitle: string, 
  chapterTitle: string, 
  preferences: string[]
): string {
  const preferencesText = preferences.length > 0 
    ? preferences.join(", ") 
    : "일반적인 독서 분위기";

  return `책 제목: "${bookTitle}"
챕터: "${chapterTitle}"
사용자 음악 취향: ${preferencesText}

위 정보를 바탕으로 독서에 적합한 배경음악을 생성해주세요. 
사용자의 음악 취향을 반영하되, 집중력을 방해하지 않는 적절한 볼륨과 리듬의 음악을 만들어주세요.`;
}