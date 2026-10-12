import axios from 'axios';

const defaultProtocol = typeof window !== 'undefined' ? window.location.protocol : 'http:';
const defaultHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
const API_URL = import.meta.env.VITE_API_URL || `${defaultProtocol}//${defaultHost}:5000`;

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('cognifocus_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  getMe: () => api.get('/api/auth/me'),
  logout: () => api.post('/api/auth/logout'),
};

export const adminAPI = {
  startMonitoring: () => api.post('/api/admin/start-monitoring'),
  stopMonitoring: () => api.post('/api/admin/stop-monitoring'),
  discoverCameras: () => api.get('/api/admin/cameras/discover'),
};

export const teacherAPI = {
  enterClassroom: (code) => api.post('/api/teacher/classroom/enter', { classroom_code: code }),
  startMonitoring: (code) => api.post('/api/teacher/monitoring/start', { classroom_code: code }),
  getCurrentClassroom: () => api.get('/api/teacher/classroom/current'),
  leaveClassroom: () => api.post('/api/teacher/classroom/leave'),
  stopMonitoring: () => api.post('/api/teacher/monitoring/stop'),
  getClassrooms: () => api.get('/api/teacher/classrooms'),
  getCameras: () => api.get('/api/teacher/cameras'),
  getAlerts: (params) => api.get('/api/teacher/alerts', { params }),
  getDashboardStats: () => api.get('/api/teacher/dashboard/stats'),
  getVapidPublicKey: () => api.get('/api/teacher/push/vapid-public-key'),
  subscribePush: (data) => api.post('/api/teacher/push/subscribe', data),
};

export const monitorAPI = {
  getStatus: () => api.get('/api/monitor/status'),
  getDetections: () => api.get('/api/monitor/detections'),
  getSeats: () => api.get('/api/monitor/seats'),
  start: (camera_source, camera_id = 'CAM001') => api.post('/api/monitor/start', { camera_source, camera_id }),
  stop: () => api.post('/api/monitor/stop'),
  verifyCode: (code) => api.post('/api/monitor/verify-code', { code }),
  getFeedUrl: (cam_id = 'CAM001') => `${API_URL}/api/cameras/${cam_id}/stream`,
};

export const alertsAPI = {
  getAlerts: (params) => api.get('/api/alerts', { params }),
  getSummary: () => api.get('/api/alerts/summary'),
  acknowledge: (id) => api.post(`/api/alerts/${id}/acknowledge`),
  resolve: (id) => api.post(`/api/alerts/${id}/resolve`),
  deleteAlert: (id) => api.delete(`/api/alerts/${id}`),
};

export const classroomsAPI = {
  getClassrooms: () => api.get('/api/classrooms'),
  createClassroom: (data) => api.post('/api/classrooms', data),
  updateClassroom: (id, data) => api.put(`/api/classrooms/${id}`, data),
  deleteClassroom: (id) => api.delete(`/api/classrooms/${id}`),
  getSeats: (id) => api.get(`/api/classrooms/${id}/seats`),
};

export const camerasAPI = {
  getCameras: () => api.get('/api/cameras'),
  getStreamUrl: (cam_id = 'CAM001') => {
    const token = localStorage.getItem('cognifocus_token');
    const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : '';
    return `${API_URL}/api/cameras/${cam_id}/stream${tokenQuery}`;
  },
  createCamera: (data) => api.post('/api/cameras', data),
  updateCamera: (id, data) => api.put(`/api/cameras/${id}`, data),
  deleteCamera: (id) => api.delete(`/api/cameras/${id}`),
  testCamera: (id) => api.post(`/api/cameras/${id}/test`),
};

export const studentsAPI = {
  getStudents: () => api.get('/api/students'),
  getStudentDetails: (id) => api.get(`/api/students/${id}`),
};

export const reportsAPI = {
  getAnalytics: (params) => api.get('/api/reports/analytics', { params }),
  getHeatmap: () => api.get('/api/reports/heatmap'),
  getExportUrl: () => `${API_URL}/api/reports/export`,
};

export const configAPI = {
  getConfig: () => api.get('/api/config'),
  updateConfig: (data) => api.put('/api/config', data),
};

export const notificationsAPI = {
  getPreferences: () => api.get('/api/notifications/preferences'),
  updatePreferences: (data) => api.put('/api/notifications/preferences', data),
  sendTestEmail: (email) => api.post('/api/notifications/test-email', { email }),
  sendTestSMS: (phone) => api.post('/api/notifications/test-sms', { phone }),
  getLogs: (alert_id) => api.get('/api/notifications/logs', { params: { alert_id } }),
};

export default api;

