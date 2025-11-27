import axios from "axios";

export const BASE_AI_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export const axiosInstance = axios.create({
  baseURL: BASE_AI_URL,
});
