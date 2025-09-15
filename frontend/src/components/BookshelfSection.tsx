import styled from "styled-components";
import { useEffect, useState } from "react";
import { collection, getDocs, getFirestore } from "firebase/firestore";
import { app } from "@/utils/firebase";
import { useNavigate } from "react-router-dom";
import { getAllReadingProgress, getProgressColor } from "@/utils/readingProgress";
import MusicPreferenceModal from "./MusicPreferenceModal";

type Book = {
  id: string;
  title: string;
  author: string;
  name?: string;
  pdfUrl?: string;
  pdfBlobKey?: string;
  coverUrl?: string;
  isAI?: boolean;
  createdAt?: any;
  chapters?: {
    page: number;
    title: string;
    musicUrl: string;
  }[];
};

const db = getFirestore(app);

export default function BookshelfSection() {
  const [recBooks, setRecBooks] = useState<Book[]>([]);
  const [userBooks, setUserBooks] = useState<Book[]>([]);
  const [readingProgress, setReadingProgress] = useState<any>({});
  const [showMusicModal, setShowMusicModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchBooks = async () => {
      const querySnapshot = await getDocs(collection(db, "books"));
      const books = querySnapshot.docs
        .map((doc) => ({ id: doc.id, ...doc.data() } as Book))
        .filter((book) => book.isAI === false);
      setRecBooks(books);
    };

    const fetchUserBooks = async () => {
      const uid = localStorage.getItem("user_uid"); // 로그인된 사용자 UID 확인
      if (!uid) return;

      try {
        const snapshot = await getDocs(collection(db, "users", uid, "books")); // Firestore에서 해당 유저 경로의 books 컬렉션 불러옴
        const userUploadedBooks = snapshot.docs.map(
          (doc) => ({ id: doc.id, ...doc.data() } as Book)
        );
        setUserBooks(userUploadedBooks);
      } catch (e) {
        console.error("유저 책 불러오기 실패:", e);
      }
    };

    const fetchProgress = async () => {
      const progress = await getAllReadingProgress();
      setReadingProgress(progress);
    };

    fetchBooks();
    fetchUserBooks();
    fetchProgress();
  }, []);

  const handleBookClick = (book: Book) => {
    navigate(`/read/${book.id}`, { state: { book } });
  };

  return (
    <Wrapper>
      <Header>
        <SectionTitle>📁 사용자가 추가한 책 목록</SectionTitle>
        <MusicButton onClick={() => setShowMusicModal(true)}>
          🎵 음악 취향 설정
        </MusicButton>
      </Header>
      
      <SliderContainer>
        {userBooks.map((book) => {
          const progress = readingProgress[book.id];
          return (
            <BookCard key={book.id} onClick={() => handleBookClick(book)}>
              <BookCoverContainer>
                <BookCover
                  style={{ backgroundImage: `url(${book.coverUrl || ""})` }}
                />
                {progress && (
                  <ProgressOverlay>
                    <ProgressBar 
                      percentage={progress.progressPercentage}
                      color={getProgressColor(progress.progressPercentage)}
                    />
                    <ProgressText>
                      {progress.progressPercentage}%
                    </ProgressText>
                  </ProgressOverlay>
                )}
              </BookCoverContainer>
              <BookInfo>
                <strong>{book.title}</strong>
                <small>{book.author}</small>
                {progress && (
                  <ProgressInfo>
                    {progress.progressPercentage}% 완료
                  </ProgressInfo>
                )}
              </BookInfo>
            </BookCard>
          );
        })}
        {userBooks.length === 0 && (
          <p>로그인 후 추가한 책이 여기에 표시됩니다.</p>
        )}
      </SliderContainer>

      <SectionTitle>📘 리드닝이 제공하는 책 목록</SectionTitle>
      <GridContainer>
        {recBooks.map((book) => {
          const progress = readingProgress[book.id];
          return (
            <BookCard key={book.id} onClick={() => handleBookClick(book)}>
              <BookCoverContainer>
                <BookCover style={{ backgroundImage: `url(${book.coverUrl})` }} />
                {progress && (
                  <ProgressOverlay>
                    <ProgressBar 
                      percentage={progress.progressPercentage}
                      color={getProgressColor(progress.progressPercentage)}
                    />
                    <ProgressText>
                      {progress.progressPercentage}%
                    </ProgressText>
                  </ProgressOverlay>
                )}
              </BookCoverContainer>
              <BookInfo>
                <strong>{book.title}</strong>
                <small>{book.author}</small>
                {progress && (
                  <ProgressInfo>
                    {progress.progressPercentage}% 완료
                  </ProgressInfo>
                )}
              </BookInfo>
            </BookCard>
          );
        })}
      </GridContainer>
      
      <MusicPreferenceModal
        isOpen={showMusicModal}
        onClose={() => setShowMusicModal(false)}
        onSave={(preferences) => {
          console.log("음악 취향 저장됨:", preferences);
        }}
      />
    </Wrapper>
  );
}

const Wrapper = styled.section`
  max-width: 800px;
  width: 100%;
  margin: 2rem auto;
  padding: 0;
  box-sizing: border-box;

  @media (max-width: 768px) {
    max-width: 100%;
    margin: 1.8rem auto;
  }

  @media (max-width: 480px) {
    margin: 1.5rem auto;
  }

  @media (max-width: 375px) {
    margin: 1.2rem auto;
  }

  @media (max-width: 320px) {
    margin: 1rem auto;
  }
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 1.5rem 0 1rem;
  padding: 0;

  @media (max-width: 768px) {
    margin: 1.2rem 0 0.8rem;
  }

  @media (max-width: 480px) {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
    margin: 1rem 0 0.8rem;
  }

  @media (max-width: 375px) {
    gap: 0.8rem;
    margin: 0.8rem 0 0.6rem;
  }

  @media (max-width: 320px) {
    gap: 0.6rem;
    margin: 0.6rem 0 0.5rem;
  }
`;

const SectionTitle = styled.h3`
  font-size: 1.3rem;
  color: #3e2c1c;
  margin: 0;
  font-family: "Georgia", serif;
  font-weight: 700;

  @media (max-width: 768px) {
    font-size: 1.2rem;
  }

  @media (max-width: 480px) {
    font-size: 1.1rem;
    text-align: center;
  }

  @media (max-width: 375px) {
    font-size: 1.05rem;
  }

  @media (max-width: 320px) {
    font-size: 1rem;
  }
`;

const MusicButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  white-space: nowrap;

  @media (max-width: 768px) {
    padding: 0.75rem 1.3rem;
    font-size: 0.88rem;
  }

  @media (max-width: 480px) {
    padding: 0.7rem 1.2rem;
    font-size: 0.85rem;
    width: 100%;
    justify-content: center;
  }

  @media (max-width: 375px) {
    padding: 0.65rem 1rem;
    font-size: 0.8rem;
  }

  @media (max-width: 320px) {
    padding: 0.6rem 0.8rem;
    font-size: 0.75rem;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
  }

  &:active {
    transform: translateY(0);
  }
`;

const SliderContainer = styled.div`
  display: flex;
  overflow-x: auto;
  gap: 1rem;
  padding: 1rem 0;
  scroll-behavior: smooth;

  @media (max-width: 768px) {
    padding: 0.8rem 0;
    gap: 0.8rem;
  }

  @media (max-width: 480px) {
    padding: 0.5rem 0;
    gap: 0.6rem;
  }

  @media (max-width: 320px) {
    padding: 0.3rem 0;
  }

  &::-webkit-scrollbar {
    height: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: #92908e;
    border-radius: 10px;
  }
`;

const BookCard = styled.div`
  min-width: 140px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.1);
  text-align: center;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;

  @media (max-width: 768px) {
    min-width: 130px;
    padding: 0.9rem;
  }

  @media (max-width: 480px) {
    min-width: 120px;
    padding: 0.8rem;
    border-radius: 14px;
  }

  @media (max-width: 375px) {
    min-width: 110px;
    padding: 0.7rem;
    border-radius: 12px;
  }

  @media (max-width: 320px) {
    min-width: 100px;
    padding: 0.6rem;
    border-radius: 10px;
  }

  &:hover {
    transform: translateY(-6px);
    box-shadow: 0 16px 32px rgba(0, 0, 0, 0.15);
    border-color: rgba(102, 126, 234, 0.3);
  }

  &:active {
    transform: translateY(-2px);
  }
`;

const BookCoverContainer = styled.div`
  position: relative;
  width: 100%;
  height: 160px;
  margin-bottom: 0.8rem;
  border-radius: 8px;
  overflow: hidden;

  @media (max-width: 768px) {
    height: 140px;
    margin-bottom: 0.7rem;
  }

  @media (max-width: 480px) {
    height: 130px;
    margin-bottom: 0.6rem;
  }

  @media (max-width: 375px) {
    height: 120px;
    margin-bottom: 0.5rem;
  }

  @media (max-width: 320px) {
    height: 110px;
    margin-bottom: 0.4rem;
  }
`;

const BookCover = styled.div`
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  border-radius: 8px;
  background-color: #f8f9fa;
  transition: transform 0.3s ease;

  &:hover {
    transform: scale(1.02);
  }
`;

const ProgressOverlay = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  border-radius: 0 0 6px 6px;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ProgressBar = styled.div<{ percentage: number; color: string }>`
  flex: 1;
  height: 4px;
  background: rgba(255,255,255,0.3);
  border-radius: 2px;
  overflow: hidden;
  
  &::after {
    content: '';
    display: block;
    width: ${props => props.percentage}%;
    height: 100%;
    background: ${props => props.color};
    border-radius: 2px;
    transition: width 0.3s ease;
  }
`;

const ProgressText = styled.span`
  color: white;
  font-size: 0.7rem;
  font-weight: bold;
  min-width: 25px;
`;

const BookInfo = styled.div`
  padding: 0.2rem 0;
  
  strong {
    display: block;
    font-size: 1rem;
    color: #2c2c2c;
    font-weight: 600;
    line-height: 1.3;
    margin-bottom: 0.3rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    @media (max-width: 768px) {
      font-size: 0.95rem;
    }

    @media (max-width: 480px) {
      font-size: 0.9rem;
    }

    @media (max-width: 375px) {
      font-size: 0.85rem;
    }

    @media (max-width: 320px) {
      font-size: 0.8rem;
    }
  }
  
  small {
    display: block;
    font-size: 0.85rem;
    color: #666;
    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    @media (max-width: 768px) {
      font-size: 0.8rem;
    }

    @media (max-width: 480px) {
      font-size: 0.75rem;
    }

    @media (max-width: 375px) {
      font-size: 0.7rem;
    }

    @media (max-width: 320px) {
      font-size: 0.65rem;
    }
  }
`;

const ProgressInfo = styled.div`
  font-size: 0.75rem;
  color: #667eea;
  font-weight: 600;
  margin-top: 0.3rem;
  padding: 0.25rem 0.6rem;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  display: inline-block;
  border: 1px solid rgba(102, 126, 234, 0.2);

  @media (max-width: 480px) {
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
  }

  @media (max-width: 375px) {
    font-size: 0.65rem;
    padding: 0.15rem 0.4rem;
  }

  @media (max-width: 320px) {
    font-size: 0.6rem;
    padding: 0.1rem 0.3rem;
  }
`;

const GridContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
  padding: 1rem 0;
  max-height: 500px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: #cdb89e;
    border-radius: 10px;
  }

  @media (max-width: 1024px) {
    grid-template-columns: repeat(3, 1fr);
  }

  @media (max-width: 768px) {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.8rem;
    padding: 0.8rem 0;
  }

  @media (max-width: 600px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 480px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.6rem;
    padding: 0.5rem 0;
  }

  @media (max-width: 320px) {
    padding: 0.3rem 0;
    gap: 0.5rem;
  }
`;
