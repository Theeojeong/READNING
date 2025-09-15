import { initializeApp, getApps, getApp } from "firebase/app";
import { getFirestore, collection, getDocs } from "firebase/firestore";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyBrwvVJmgnc06SxMpKwG6NpxqJUHZrf4jU",
  authDomain: "readning-3cb46.firebaseapp.com",
  projectId: "readning-3cb46",
  storageBucket: "readning-3cb46.firebasestorage.app",
  messagingSenderId: "873200182505",
  appId: "1:873200182505:web:5b597a720a812e63f0fc78",
  measurementId: "G-2E3H8EG4GB",
};

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

const db = getFirestore(app);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

export { app, db, auth, provider };

export async function getBooksFromFirebase() {
  const snapshot = await getDocs(collection(db, "books"));
  return snapshot.docs.map((doc) => ({
    id: doc.id,
    ...doc.data(),
  })) as {
    id: string;
    title: string;
    author: string;
    content: string;
    coverUrl: string;
  }[];
}
