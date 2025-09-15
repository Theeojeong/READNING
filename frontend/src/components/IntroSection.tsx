import styled, { keyframes } from "styled-components";

export default function IntroSection() {
  return (
    <Section>
      <Content>
        <TextSection>
          <Badge>✨ AI 기반 개인화 독서</Badge>
          <Title>
            당신만의 <br />
            독서 공간,
            <br />
            <GradientText>리드닝</GradientText>
          </Title>
          <Description>
            AI가 분석한 당신의 취향으로 <br />
            완벽한 배경음악을 생성합니다.
            <br />
            책과 음악이 만나는 <br />
            새로운 독서 경험을 시작하세요.
          </Description>
          <ButtonGroup>
            <PrimaryButton>
              <ButtonIcon>🎵</ButtonIcon>
              지금 <br />
              시작하기
            </PrimaryButton>
            <SecondaryButton>
              <ButtonIcon>📖</ButtonIcon>
              둘러보기
            </SecondaryButton>
          </ButtonGroup>
        </TextSection>

        <VisualSection>
          <FloatingCard delay="0s">
            <CardIcon>🎧</CardIcon>
            <CardTitle>개인화된 음악</CardTitle>
            <CardDesc>AI가 당신의 취향을 학습합니다</CardDesc>
          </FloatingCard>

          <FloatingCard delay="0.5s">
            <CardIcon>📚</CardIcon>
            <CardTitle>진행률 추적</CardTitle>
            <CardDesc>어디서든 이어서 읽을 수 있어요</CardDesc>
          </FloatingCard>

          <FloatingCard delay="1s">
            <CardIcon>✨</CardIcon>
            <CardTitle>몰입형 독서</CardTitle>
            <CardDesc>책에 완전히 빠져들게 됩니다</CardDesc>
          </FloatingCard>
        </VisualSection>
      </Content>
    </Section>
  );
}

const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const float = keyframes`
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-10px) rotate(1deg); }
`;

const Section = styled.section`
  width: 100%;
  max-width: 1200px;
  margin: 6rem auto;
  padding: 0 2rem;
  animation: ${fadeInUp} 0.8s ease-out;
  box-sizing: border-box;

  @media (max-width: 768px) {
    margin: 4rem auto;
    padding: 0 1rem;
  }

  @media (max-width: 480px) {
    margin: 3rem auto;
    padding: 0 1rem;
  }

  @media (max-width: 320px) {
    margin: 2rem auto;
    padding: 0 1rem;
  }
`;

const Content = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  min-height: 500px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 3rem;
    text-align: center;
  }
`;

const TextSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const Badge = styled.div`
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50px;
  font-size: 0.85rem;
  font-weight: 600;
  width: fit-content;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);

  @media (max-width: 480px) {
    font-size: 0.8rem;
    padding: 0.4rem 0.8rem;
  }
`;

const Title = styled.h1`
  font-size: 3.5rem;
  font-weight: 800;
  color: #1a1a1a;
  line-height: 1.1;
  margin: 0;

  @media (max-width: 768px) {
    font-size: 2.5rem;
  }

  @media (max-width: 480px) {
    font-size: 2rem;
  }
`;

const GradientText = styled.span`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: ${float} 3s ease-in-out infinite;
`;

const Description = styled.p`
  color: #666;
  line-height: 1.7;
  font-size: 1.1rem;
  margin: 0;
  max-width: 500px;

  @media (max-width: 768px) {
    font-size: 1rem;
    max-width: 100%;
  }

  @media (max-width: 480px) {
    font-size: 0.9rem;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1rem;

  @media (max-width: 768px) {
    justify-content: center;
  }

  @media (max-width: 480px) {
    flex-direction: column;
    gap: 0.8rem;
    align-items: center;
  }
`;

const PrimaryButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  max-width: 200px;
  width: 100%;

  @media (max-width: 768px) {
    padding: 0.8rem 1.5rem;
    font-size: 0.9rem;
  }

  @media (max-width: 480px) {
    padding: 0.7rem 1.2rem;
    font-size: 0.85rem;
    width: 100%;
    max-width: 200px;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
  }
`;

const SecondaryButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  max-width: 200px;
  width: 100%;

  @media (max-width: 768px) {
    padding: 0.8rem 1.5rem;
    font-size: 0.9rem;
  }

  @media (max-width: 480px) {
    padding: 0.7rem 1.2rem;
    font-size: 0.85rem;
    width: 100%;
    max-width: 200px;
  }

  &:hover {
    background: #667eea;
    color: white;
    transform: translateY(-2px);
  }
`;

const ButtonIcon = styled.span`
  font-size: 1.2rem;
`;

const VisualSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;

  @media (max-width: 768px) {
    gap: 1rem;
  }

  @media (max-width: 480px) {
    gap: 0.8rem;
  }
`;

const FloatingCard = styled.div<{ delay: string }>`
  background: white;
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
  animation: ${float} 4s ease-in-out infinite;
  animation-delay: ${(props) => props.delay};

  @media (max-width: 768px) {
    padding: 1.2rem;
  }

  @media (max-width: 480px) {
    padding: 1rem;
    border-radius: 12px;
  }

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  }
`;

const CardIcon = styled.div`
  font-size: 2rem;
  margin-bottom: 0.5rem;

  @media (max-width: 480px) {
    font-size: 1.8rem;
  }
`;

const CardTitle = styled.h3`
  color: #1a1a1a;
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;

  @media (max-width: 480px) {
    font-size: 1rem;
  }
`;

const CardDesc = styled.p`
  color: #666;
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0;

  @media (max-width: 480px) {
    font-size: 0.85rem;
  }
`;
