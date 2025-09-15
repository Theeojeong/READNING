import styled from "styled-components";
import { Link } from "react-router-dom";
import { handleGoogleLogin } from "./handleGoogleLogin";
import { useEffect, useState } from "react";

export default function Navbar() {
  const [userName, setUserName] = useState("");
  const [userPhoto, setUserPhoto] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    const name = localStorage.getItem("user_name");
    const photo = localStorage.getItem("user_photo");
    if (name) setUserName(name);
    if (photo) setUserPhoto(photo);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("user_uid");
    localStorage.removeItem("user_name");
    localStorage.removeItem("user_photo");
    localStorage.removeItem("user_email");
    window.location.reload();
  };

  return (
    <Nav>
      <Logo>
        <Link to="/">🎵 리드닝</Link>
      </Logo>
      <NavLinks>
        <a href="#about">서비스 소개</a>
        <a href="#faq">FAQ</a>
        <a href="#pricing">가격</a>

        {userName ? (
          <DropdownContainer>
            <UserInfo onClick={() => setDropdownOpen((prev) => !prev)}>
              {userPhoto && <ProfileImg src={userPhoto} alt="프로필" />}
              <UserName>{userName}</UserName>
            </UserInfo>
            {dropdownOpen && (
              <DropdownMenu>
                <DropdownItem onClick={handleLogout}>로그아웃</DropdownItem>
              </DropdownMenu>
            )}
          </DropdownContainer>
        ) : (
          <LoginButton type="button" onClick={handleGoogleLogin}>
            Google 로그인
          </LoginButton>
        )}
      </NavLinks>
    </Nav>
  );
}

const UserName = styled.span`
  font-weight: 500;
`;

const DropdownContainer = styled.div`
  position: relative;
`;

const DropdownMenu = styled.div`
  position: absolute;
  top: 120%;
  right: 0;
  background-color: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
`;

const DropdownItem = styled.div`
  padding: 0.7rem 1.2rem;
  cursor: pointer;
  font-size: 0.95rem;
  white-space: nowrap;

  &:hover {
    background-color: #f2f2f2;
  }
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-weight: 500;
  color: #3a3a3a;
  cursor: pointer;
  white-space: nowrap;

  @media (max-width: 480px) {
    gap: 0.4rem;
  }

  &:hover {
    color: #5f3dc4;
  }
`;

const ProfileImg = styled.img`
  width: 32px;
  height: 32px;
  border-radius: 50%;

  @media (max-width: 480px) {
    width: 28px;
    height: 28px;
  }
`;

const Nav = styled.nav`
  width: 100vw;
  padding: 1.2rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f9f9fb;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  margin-top: -2rem;
  margin-left: calc(-50vw + 50%);
  box-sizing: border-box;
  position: relative;

  @media (max-width: 768px) {
    padding: 1rem 2rem;
  }

  @media (max-width: 480px) {
    padding: 0.8rem 1.5rem;
    flex-direction: column;
    gap: 1rem;
  }

  @media (max-width: 375px) {
    padding: 0.8rem 1rem;
  }

  @media (max-width: 320px) {
    padding: 0.6rem 0.8rem;
  }
`;

const Logo = styled.h1`
  font-size: 1.6rem;
  font-weight: bold;
  font-family: "Georgia", serif;
  color: #4d3b2a;
  margin: 0;

  @media (max-width: 480px) {
    font-size: 1.4rem;
  }

  a {
    color: #3a3a3a;
    text-decoration: none;
    font-weight: 500;

    &:hover {
      color: #5f3dc4;
    }
  }
`;

const NavLinks = styled.div`
  display: flex;
  gap: 1.5rem;
  align-items: center;

  @media (max-width: 768px) {
    gap: 1rem;
  }

  @media (max-width: 480px) {
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.8rem;
  }

  a {
    color: #3a3a3a;
    text-decoration: none;
    font-weight: 500;
    font-size: 1rem;

    @media (max-width: 480px) {
      font-size: 0.9rem;
    }

    &:hover {
      color: #5f3dc4;
    }
  }
`;

const LoginButton = styled.button`
  background-color: #5f3dc4;
  color: white;
  padding: 0.5rem 1.2rem;
  border-radius: 6px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  white-space: nowrap;

  @media (max-width: 480px) {
    padding: 0.4rem 1rem;
    font-size: 0.9rem;
  }

  &:hover {
    background-color: #4a2faf;
  }
`;
