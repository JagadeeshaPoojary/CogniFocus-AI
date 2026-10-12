import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI, adminAPI, teacherAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('cognifocus_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);
  const [teacherClassroom, setTeacherClassroom] = useState(null);
  const [isTeacherMonitoringActive, setIsTeacherMonitoringActive] = useState(false);

  const fetchTeacherSession = async () => {
    try {
      const res = await teacherAPI.getCurrentClassroom();
      if (res.data.success) {
        if (res.data.monitoring_active && res.data.classroom) {
          setTeacherClassroom(res.data.classroom);
          setIsTeacherMonitoringActive(true);
        } else {
          setTeacherClassroom(null);
          setIsTeacherMonitoringActive(false);
        }
      }
    } catch (err) {
      console.error("[useAuth] fetchTeacherSession error:", err);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('cognifocus_token');
    if (token && token !== 'undefined' && token !== 'null') {
      authAPI.getMe()
        .then(res => {
          if (res.data.success) {
            const userData = res.data.user;
            setUser(userData);
            localStorage.setItem('cognifocus_user', JSON.stringify(userData));

            if (userData.role === 'ADMIN') {
              adminAPI.startMonitoring().catch(err => console.error("Admin auto-start error:", err));
            } else if (userData.role === 'TEACHER') {
              fetchTeacherSession();
            }
          } else {
            logout();
          }
        })
        .catch((err) => {
          console.error("[useAuth] getMe validation failed:", err);
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
      if (user) {
        logout();
      }
    }
  }, []);

  const login = async (email, password) => {
    const res = await authAPI.login({ email, password });
    if (res.data.success) {
      const { token, user: loggedUser } = res.data;
      localStorage.setItem('cognifocus_token', token);
      localStorage.setItem('cognifocus_user', JSON.stringify(loggedUser));
      setUser(loggedUser);

      // Auto-start camera monitoring ONLY if Admin
      if (loggedUser.role === 'ADMIN') {
        try {
          await adminAPI.startMonitoring();
          console.log("[CogniFocus] Admin auto monitoring initialized!");
        } catch (err) {
          console.error("Admin auto-start error:", err);
        }
      } else if (loggedUser.role === 'TEACHER') {
        // Teachers start in NO_CLASSROOM state (Monitoring = OFF)
        setTeacherClassroom(null);
        setIsTeacherMonitoringActive(false);
      }

      return loggedUser;
    }
    throw new Error(res.data.message || 'Login failed');
  };

  const enterTeacherClassroom = async (code) => {
    try {
      const res = await teacherAPI.enterClassroom(code);
      if (res.data.success) {
        setTeacherClassroom(res.data.classroom);
        setIsTeacherMonitoringActive(true);
        return res.data;
      }
      throw new Error(res.data.message || 'Failed to start monitoring');
    } catch (err) {
      console.error("[Teacher Classroom Access Error]", err);
      if (err.response) {
        const status = err.response.status;
        const msg = err.response.data?.message;
        if (status === 401) {
          throw new Error(msg || "Session expired or invalid login. Please log in again.");
        } else if (status === 403) {
          throw new Error(msg || "You are not authorized to monitor this classroom.");
        } else if (status === 404) {
          throw new Error(msg || "Classroom code not found.");
        } else if (status === 409) {
          throw new Error(msg || "Monitoring conflict. Classroom is already being monitored.");
        } else if (status === 500) {
          throw new Error(msg || "Server error. Please try again.");
        } else {
          throw new Error(msg || `Server error (${status}). Please try again.`);
        }
      } else if (err.code === 'ECONNABORTED' || err.message === 'Network Error' || err.request) {
        throw new Error("Unable to connect to monitoring server.");
      } else {
        throw new Error(err.message || "An unexpected error occurred.");
      }
    }
  };

  const stopTeacherMonitoring = async () => {
    try {
      const res = await teacherAPI.stopMonitoring();
      return res.data;
    } catch (err) {
      console.error("[useAuth] stopTeacherMonitoring error:", err);
      throw err;
    } finally {
      setIsTeacherMonitoringActive(false);
    }
  };

  const leaveTeacherClassroom = async () => {
    try {
      await teacherAPI.leaveClassroom();
    } catch (err) {
      console.error("[useAuth] leaveTeacherClassroom error:", err);
    } finally {
      setTeacherClassroom(null);
      setIsTeacherMonitoringActive(false);
    }
  };

  const logout = async () => {
    if (user?.role === 'ADMIN') {
      try {
        await adminAPI.stopMonitoring();
        console.log("[CogniFocus] Admin monitoring workers released.");
      } catch (err) {
        console.error("Admin stop monitoring error:", err);
      }
    } else if (user?.role === 'TEACHER') {
      await leaveTeacherClassroom();
    }

    localStorage.removeItem('cognifocus_token');
    localStorage.removeItem('cognifocus_user');
    setUser(null);
    setTeacherClassroom(null);
    setIsTeacherMonitoringActive(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        loading,
        isAdmin: user?.role === 'ADMIN',
        isTeacher: user?.role === 'TEACHER',
        teacherClassroom,
        isTeacherMonitoringActive,
        enterTeacherClassroom,
        stopTeacherMonitoring,
        leaveTeacherClassroom,
        refreshTeacherSession: fetchTeacherSession
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
