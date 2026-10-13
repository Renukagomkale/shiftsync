import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL;
const ACCESS = "shiftsync.access";
const REFRESH = "shiftsync.refresh";

export const getAccess = () => localStorage.getItem(ACCESS);
export const getRefresh = () => localStorage.getItem(REFRESH);

export function saveTokens({ access, refresh }) {
  localStorage.setItem(ACCESS, access);
  if (refresh) localStorage.setItem(REFRESH, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS);
  localStorage.removeItem(REFRESH);
}

const api = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  const access = getAccess();
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

let refreshing = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const refresh = getRefresh();
    const isAuthCall = /\/auth\/(login|register|refresh)\//.test(original?.url ?? "");
    if (error.response?.status !== 401 || original._retried || !refresh || isAuthCall) {
      return Promise.reject(error);
    }
    original._retried = true;
    refreshing ??= axios
      .post(`${baseURL}/auth/refresh/`, { refresh })
      .then((response) => {
        saveTokens({ access: response.data.access });
        return response.data.access;
      })
      .finally(() => {
        refreshing = null;
      });
    try {
      original.headers.Authorization = `Bearer ${await refreshing}`;
      return api(original);
    } catch {
      clearTokens();
      window.dispatchEvent(new Event("shiftsync:logout"));
      return Promise.reject(error);
    }
  }
);

export function errorMessages(error) {
  const data = error.response?.data;
  if (!data) return ["Cannot reach the server. Check that the backend is running."];
  const fieldErrors = data.errors ? Object.values(data.errors).flat().map(String) : [];
  if (fieldErrors.length) return fieldErrors;
  return [data.message ?? "Something went wrong. Please try again."];
}

export default api;
