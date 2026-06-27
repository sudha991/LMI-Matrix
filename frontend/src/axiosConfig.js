import axios from "axios";

const API = axios.create({
  baseURL: "http://10.0.180.28:5000"
});

// 🔥 Add token automatically to all requests
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default API;