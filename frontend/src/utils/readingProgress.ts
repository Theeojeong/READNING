import { auth, db } from "./firebase";
import { doc, setDoc, getDoc, updateDoc } from "firebase/firestore";

export interface ReadingProgress {
  bookId: string;
  currentPage?: number;
  totalPages?: number;
  currentChapter?: number;
  totalChapters?: number;
  progressPercentage: number;
  lastReadAt: Date;
  readingTime: number; // 총 읽은 시간 (분)
}

export interface BookProgress {
  [bookId: string]: ReadingProgress;
}

export async function saveReadingProgress(
  bookId: string,
  currentPage?: number,
  totalPages?: number,
  currentChapter?: number,
  totalChapters?: number
): Promise<void> {
  const user = auth.currentUser;
  if (!user) return;

  try {
    let progressPercentage = 0;
    
    if (currentPage && totalPages) {
      progressPercentage = Math.round((currentPage / totalPages) * 100);
    } else if (currentChapter !== undefined && totalChapters) {
      progressPercentage = Math.round(((currentChapter + 1) / totalChapters) * 100);
    }

    const progressData: ReadingProgress = {
      bookId,
      currentPage,
      totalPages,
      currentChapter,
      totalChapters,
      progressPercentage,
      lastReadAt: new Date(),
      readingTime: 0 // 기존 시간은 유지하고 새로 추가되는 시간만 업데이트
    };

    // 기존 진행률 데이터 가져오기
    const userDoc = await getDoc(doc(db, "users", user.uid));
    const existingData = userDoc.exists() ? userDoc.data() : {};
    const existingProgress = existingData.readingProgress || {};
    const existingBookProgress = existingProgress[bookId];

    // 기존 읽기 시간 유지
    if (existingBookProgress?.readingTime) {
      progressData.readingTime = existingBookProgress.readingTime;
    }

    await setDoc(doc(db, "users", user.uid), {
      readingProgress: {
        ...existingProgress,
        [bookId]: progressData
      }
    }, { merge: true });

  } catch (error) {
    console.error("읽기 진행률 저장 실패:", error);
  }
}

export async function getReadingProgress(bookId: string): Promise<ReadingProgress | null> {
  const user = auth.currentUser;
  if (!user) return null;

  try {
    const userDoc = await getDoc(doc(db, "users", user.uid));
    if (userDoc.exists()) {
      const data = userDoc.data();
      const progress = data.readingProgress?.[bookId];
      return progress || null;
    }
    return null;
  } catch (error) {
    console.error("읽기 진행률 가져오기 실패:", error);
    return null;
  }
}

export async function getAllReadingProgress(): Promise<BookProgress> {
  const user = auth.currentUser;
  if (!user) return {};

  try {
    const userDoc = await getDoc(doc(db, "users", user.uid));
    if (userDoc.exists()) {
      const data = userDoc.data();
      return data.readingProgress || {};
    }
    return {};
  } catch (error) {
    console.error("전체 읽기 진행률 가져오기 실패:", error);
    return {};
  }
}

export async function updateReadingTime(bookId: string, additionalMinutes: number): Promise<void> {
  const user = auth.currentUser;
  if (!user) return;

  try {
    const userDoc = await getDoc(doc(db, "users", user.uid));
    if (userDoc.exists()) {
      const data = userDoc.data();
      const progress = data.readingProgress || {};
      const bookProgress = progress[bookId];

      if (bookProgress) {
        const updatedProgress = {
          ...bookProgress,
          readingTime: (bookProgress.readingTime || 0) + additionalMinutes,
          lastReadAt: new Date()
        };

        await updateDoc(doc(db, "users", user.uid), {
          [`readingProgress.${bookId}`]: updatedProgress
        });
      }
    }
  } catch (error) {
    console.error("읽기 시간 업데이트 실패:", error);
  }
}

export function formatReadingTime(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}분`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}시간 ${remainingMinutes}분`;
}

export function getProgressColor(percentage: number): string {
  if (percentage >= 80) return "#4CAF50"; // 초록
  if (percentage >= 50) return "#FF9800"; // 주황
  if (percentage >= 20) return "#2196F3"; // 파랑
  return "#9E9E9E"; // 회색
}