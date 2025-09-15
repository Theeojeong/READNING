import { useState } from "react";
import styled from "styled-components";
import { auth, db } from "@/utils/firebase";
import { doc, setDoc } from "firebase/firestore";

interface MusicPreferenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (preferences: string[]) => void;
}

const musicGenres = [
  "클래식", "재즈", "록", "팝", "일렉트로닉", "힙합",
  "R&B", "컨트리", "포크", "인디", "어쿠스틱", "앰비언트",
  "로파이", "뉴에이지", "월드뮤직", "사운드트랙"
];

const moods = [
  "차분한", "집중적인", "몽환적인", "경쾌한", "우울한", 
  "신비로운", "따뜻한", "시원한", "강렬한", "부드러운"
];

export default function MusicPreferenceModal({ 
  isOpen, 
  onClose, 
  onSave 
}: MusicPreferenceModalProps) {
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [selectedMoods, setSelectedMoods] = useState<string[]>([]);

  const toggleGenre = (genre: string) => {
    setSelectedGenres(prev => 
      prev.includes(genre) 
        ? prev.filter(g => g !== genre)
        : [...prev, genre]
    );
  };

  const toggleMood = (mood: string) => {
    setSelectedMoods(prev => 
      prev.includes(mood) 
        ? prev.filter(m => m !== mood)
        : [...prev, mood]
    );
  };

  const handleSave = async () => {
    const user = auth.currentUser;
    if (!user) return;

    const preferences = [...selectedGenres, ...selectedMoods];
    
    try {
      await setDoc(doc(db, "users", user.uid), {
        musicPreferences: preferences,
        updatedAt: new Date()
      }, { merge: true });
      
      onSave(preferences);
      onClose();
    } catch (error) {
      console.error("음악 취향 저장 실패:", error);
    }
  };

  if (!isOpen) return null;

  return (
    <Overlay>
      <Modal>
        <Header>
          <h2>🎵 음악 취향 설정</h2>
          <CloseButton onClick={onClose}>×</CloseButton>
        </Header>
        
        <Content>
          <Section>
            <h3>선호하는 장르</h3>
            <TagContainer>
              {musicGenres.map(genre => (
                <Tag
                  key={genre}
                  selected={selectedGenres.includes(genre)}
                  onClick={() => toggleGenre(genre)}
                >
                  {genre}
                </Tag>
              ))}
            </TagContainer>
          </Section>

          <Section>
            <h3>선호하는 분위기</h3>
            <TagContainer>
              {moods.map(mood => (
                <Tag
                  key={mood}
                  selected={selectedMoods.includes(mood)}
                  onClick={() => toggleMood(mood)}
                >
                  {mood}
                </Tag>
              ))}
            </TagContainer>
          </Section>
        </Content>

        <Footer>
          <SaveButton 
            onClick={handleSave}
            disabled={selectedGenres.length === 0 && selectedMoods.length === 0}
          >
            저장하기
          </SaveButton>
        </Footer>
      </Modal>
    </Overlay>
  );
}

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const Modal = styled.div`
  background: white;
  border-radius: 12px;
  padding: 0;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  
  h2 {
    margin: 0;
    color: #333;
  }
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  
  &:hover {
    background: #f0f0f0;
  }
`;

const Content = styled.div`
  padding: 1.5rem;
`;

const Section = styled.div`
  margin-bottom: 2rem;
  
  h3 {
    margin: 0 0 1rem 0;
    color: #5f3dc4;
    font-size: 1.1rem;
  }
`;

const TagContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
`;

const Tag = styled.button<{ selected: boolean }>`
  padding: 0.5rem 1rem;
  border: 2px solid ${props => props.selected ? '#5f3dc4' : '#ddd'};
  background: ${props => props.selected ? '#5f3dc4' : 'white'};
  color: ${props => props.selected ? 'white' : '#333'};
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: #5f3dc4;
    background: ${props => props.selected ? '#4c2db3' : '#f8f7ff'};
  }
`;

const Footer = styled.div`
  padding: 1.5rem;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: center;
`;

const SaveButton = styled.button`
  background: #5f3dc4;
  color: white;
  border: none;
  padding: 0.8rem 2rem;
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