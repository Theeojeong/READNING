-- Readning 프로젝트 데이터베이스 초기화 스크립트
-- Docker 컨테이너 실행 시 자동으로 실행됩니다

-- 데이터베이스 선택
USE readning;

-- 책 정보 테이블
CREATE TABLE IF NOT EXISTS books (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(255),
    file_url TEXT,
    cover_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 페이지/챕터 테이블
CREATE TABLE IF NOT EXISTS chapters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id VARCHAR(255) NOT NULL,
    page INT NOT NULL,
    total_duration INT DEFAULT 240,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    UNIQUE KEY unique_book_page (book_id, page),
    INDEX idx_book_id (book_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 청크 테이블 (핵심!)
CREATE TABLE IF NOT EXISTS chunks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chapter_id INT NOT NULL,
    chunk_index INT NOT NULL,
    text_content TEXT NOT NULL,
    text_preview VARCHAR(500),
    emotion VARCHAR(100),
    audio_url TEXT,
    audio_duration FLOAT DEFAULT 30.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
    INDEX idx_chapter (chapter_id),
    INDEX idx_chunk_order (chapter_id, chunk_index),
    INDEX idx_emotion (emotion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 사용자 음악 취향 테이블 (선택사항)
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id VARCHAR(255) PRIMARY KEY,
    music_style VARCHAR(100),
    preferences JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 샘플 데이터 삽입 (테스트용)
INSERT INTO books (id, user_id, title, author) VALUES 
('test_book_1', 'user_123', '테스트 소설', '홍길동')
ON DUPLICATE KEY UPDATE title=title;

-- 초기화 완료 메시지
SELECT '✅ 데이터베이스 초기화 완료!' as status;

