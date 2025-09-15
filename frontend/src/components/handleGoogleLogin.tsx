import { auth, provider } from "@/utils/firebase";
import { signInWithPopup } from "firebase/auth";

export const handleGoogleLogin = async () => {
  try {
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    // 사용자 정보 저장 (예: 로컬스토리지 또는 상태)
    localStorage.setItem("user_email", user.email || "");
    localStorage.setItem("user_name", user.displayName || "");
    localStorage.setItem("user_uid", user.uid);

    alert("구글 로그인 성공!");
    window.location.href = "/";
  } catch (error) {
    console.error("구글 로그인 실패:", error);
    alert("구글 로그인 중 오류가 발생했습니다.");
  }
};
