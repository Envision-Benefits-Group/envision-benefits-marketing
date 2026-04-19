import axios from "axios";
import {
  getAccessToken,
  getRefreshToken,
  removeTokens,
  setTokens,
} from "./auth";

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

let isRefreshing = false;
let failedQueue: { resolve: (token: string) => void; reject: (error: any) => void }[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token as string);
    }
  });
  failedQueue = [];
};

// Add response interceptor to handle auth errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = "Bearer " + token;
            return axios(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        removeTokens();
        if (typeof window !== 'undefined') {
          window.location.href = "/auth/login";
        }
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`,
          {
            refresh_token: refreshToken,
          }
        );

        const { access_token: newAccessToken, refresh_token: newRefreshToken } =
          data;
        setTokens(newAccessToken, newRefreshToken);

        api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        removeTokens();
        if (typeof window !== 'undefined') {
          window.location.href = "/auth/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

import type { AutoRenewalRequest, BrowseFilters, ComparisonRequest, IngestResponse, Plan } from "@/types/plans";

// Plans API functions
export const plansApi = {
  browse: (params: BrowseFilters) =>
    api.get<Plan[]>("/plans/browse", { params }),
  update: (planId: string, data: Partial<Plan>) =>
    api.patch<Plan>(`/plans/${planId}`, data),
  downloadMasterTemplate: (year: number, quarter: string) =>
    api.get("/plans/master-template", {
      params: { year, quarter },
      responseType: "blob",
    }),
  generateComparison: (data: ComparisonRequest) =>
    api.post("/plans/comparison-template", data, { responseType: "blob" }),
  generateAutoRenewal: (data: AutoRenewalRequest) =>
    api.post("/plans/auto-renewal", data, { responseType: "blob" }),
};

// Extraction API functions (uses API key auth, not JWT)
export const extractionApi = {
  ingest: (files: File[], quarter?: string) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    if (quarter) formData.append("quarter", quarter);
    return api.post<IngestResponse>("/extraction/ingest", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
        "x-api-key": process.env.NEXT_PUBLIC_API_KEY || "test-secret-key",
      },
    });
  },
};

// User API functions
export const userAPI = {
  getCurrentUser: () => api.get("/auth/user/current_user"),
  updateCurrentUser: (data: any) =>
    api.put("/auth/user/current_user", data),
  login: (data: any) => api.post('/auth/login/access-token', data, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  }),
};

export default api; 
