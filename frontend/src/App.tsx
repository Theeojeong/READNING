// src/App.tsx

import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainPage from "./pages/MainPage";
import ReaderPage from "./pages/ReaderPage";
import styled from "styled-components";
import TestMusicAPI from "./pages/TestMusicAPI";

export default function App() {
  return (
    <AppWrapper>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainPage />} />
          <Route path="/read/:bookId" element={<ReaderPage />} />
          <Route path="/test-music" element={<TestMusicAPI />} />
        </Routes>
      </BrowserRouter>
    </AppWrapper>
  );
}

// ========== styled-components ==========
const AppWrapper = styled.div`
  width: 100%;
  min-height: 100vh;

  display: flex;
  justify-content: center; /* 수평 중앙 정렬 */
  align-items: flex-start; /* 상단 정렬 */

  background-color: #ffffff;
  padding: 2rem 0;
`;
