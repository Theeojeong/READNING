import styled from "styled-components";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import IntroSection from "../components/IntroSection";
import UploadSection from "../components/UploadSection";
import BookshelfSection from "../components/BookshelfSection";

export default function MainPage() {
  return (
    <PageLayout>
      <Navbar />
      <IntroSection />
      <UploadSection />
      <BookshelfSection />
      <Footer />
    </PageLayout>
  );
}

const PageLayout = styled.div`
  max-width: 800px;
  width: 100%;
  padding: 0 2rem;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  user-select: none;
  box-sizing: border-box;

  @media (max-width: 768px) {
    max-width: 100%;
    padding: 0 2rem;
  }

  @media (max-width: 480px) {
    max-width: 100%;
    padding: 0 1.5rem;
  }

  @media (max-width: 375px) {
    max-width: 100%;
    padding: 0 1rem;
  }

  @media (max-width: 320px) {
    max-width: 100%;
    padding: 0 0.8rem;
  }
`;
