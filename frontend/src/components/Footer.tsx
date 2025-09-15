import styled from "styled-components";

export default function Footer() {
  return (
    <FooterContainer>
      <Inner>
        <p>© 2025 Readning. All rights reserved.</p>
      </Inner>
    </FooterContainer>
  );
}

const FooterContainer = styled.footer`
  width: 100vw;
  background-color: #f8f9fa;
  border-top: 1px solid #e1e1e1;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-left: calc(-50vw + 50%);
  box-sizing: border-box;
  position: relative;

  @media (max-width: 768px) {
    padding: 1rem 2rem;
  }

  @media (max-width: 480px) {
    padding: 0.8rem 1.5rem;
  }

  @media (max-width: 375px) {
    padding: 0.8rem 1rem;
  }

  @media (max-width: 320px) {
    padding: 0.6rem 0.8rem;
  }
`;

const Inner = styled.div`
  width: 100%;
  max-width: 800px;
  text-align: center;
  font-size: 0.85rem;
  color: #6c757d;
  font-family: "Georgia", serif;

  @media (max-width: 480px) {
    font-size: 0.8rem;
  }

  @media (max-width: 320px) {
    font-size: 0.75rem;
  }

  p {
    margin: 0;
  }
`;
