import { useState, useCallback } from 'react';
import { HealthResponse, Course, Settings, QueueStats, FileRecord } from '../types/api';

const API_BASE = 'http://127.0.0.1:8765';
const REQUEST_TIMEOUT = 10000; // 10 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second base delay

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TimeoutError';
  }
}

// Helper to make fetch requests with timeout
async function fetchWithTimeout(url: string, options: RequestInit = {}, timeout: number = REQUEST_TIMEOUT): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
      throw new NetworkError('Unable to reach backend. Please check your connection.');
    }
    if ((error as any)?.name === 'AbortError') {
      throw new TimeoutError('Request timed out. Please try again.');
    }
    throw error;
  }
}

// Helper to retry requests with exponential backoff
async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  maxRetries: number = MAX_RETRIES
): Promise<Response> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetchWithTimeout(url, options);
      
      // Only retry on 5xx errors and network issues, not client errors
      if (response.status >= 500 || response.status === 0) {
        if (attempt < maxRetries) {
          const delay = RETRY_DELAY * Math.pow(2, attempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      }
      
      return response;
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on client errors, but do retry on network/timeout errors
      if (!(error instanceof NetworkError || error instanceof TimeoutError) && attempt < maxRetries) {
        const delay = RETRY_DELAY * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      
      if (attempt === maxRetries) {
        throw error;
      }
    }
  }

  throw lastError || new Error('Request failed after retries');
}

export function useBackendAPI() {
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/health`, {}, 1);
      return response.ok;
    } catch {
      return false;
    }
  }, []);

  const getCoursesList = useCallback(async (): Promise<Course[]> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/courses/list`);
      if (!response.ok) throw new Error('Failed to fetch courses');
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load courses';
      setError(message);
      return [];
    }
  }, []);

  const getSettings = useCallback(async (): Promise<Settings | null> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/settings/current`);
      if (response.status === 404) return null;
      if (!response.ok) throw new Error('Failed to fetch settings');
      return await response.json();
    } catch (err) {
      if (err instanceof Error && err.message.includes('404')) return null;
      const message = err instanceof Error ? err.message : 'Failed to load settings';
      setError(message);
      return null;
    }
  }, []);

  const createSemester = useCallback(
    async (
      semesterName: string,
      organizationStyle: 'week' | 'type' = 'week'
    ): Promise<boolean> => {
      try {
        const params = new URLSearchParams({
          semester_name: semesterName,
          organization_style: organizationStyle,
        });
        const response = await fetchWithRetry(
          `${API_BASE}/api/settings/create-semester?${params}`,
          { method: 'POST' }
        );
        if (!response.ok) throw new Error('Failed to create semester');
        setError(null);
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to create semester';
        setError(message);
        return false;
      }
    },
    []
  );

  const updateSettings = useCallback(async (updates: Partial<Settings>): Promise<boolean> => {
    try {
      const params = new URLSearchParams();
      if (updates.organization_style) params.append('organization_style', updates.organization_style);
      if (updates.confidence_auto !== undefined) params.append('confidence_auto', String(updates.confidence_auto));
      if (updates.confidence_suggest !== undefined) params.append('confidence_suggest', String(updates.confidence_suggest));

      const response = await fetchWithRetry(`${API_BASE}/api/settings/current?${params}`, {
        method: 'PUT',
      });
      if (!response.ok) throw new Error('Failed to update settings');
      setError(null);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update settings';
      setError(message);
      return false;
    }
  }, []);

  const getQueueStats = useCallback(async (): Promise<QueueStats | null> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/queue/stats`);
      if (!response.ok) throw new Error('Failed to fetch queue stats');
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load queue';
      setError(message);
      return null;
    }
  }, []);

  const getPendingFiles = useCallback(async (): Promise<FileRecord[]> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/queue/pending`);
      if (!response.ok) throw new Error('Failed to fetch pending files');
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load pending files';
      setError(message);
      return [];
    }
  }, []);

  const getRecentFiles = useCallback(async (): Promise<FileRecord[]> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/files/list?limit=10`);
      if (!response.ok) throw new Error('Failed to fetch recent files');
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load files';
      setError(message);
      return [];
    }
  }, []);

  const confirmFile = useCallback(async (fileId: number, courseCode: string): Promise<boolean> => {
    try {
      const params = new URLSearchParams();
      params.append('file_id', String(fileId));
      params.append('course_code', courseCode);

      const response = await fetchWithRetry(`${API_BASE}/api/files/confirm?${params}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to confirm file');
      setError(null);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to confirm file';
      setError(message);
      return false;
    }
  }, []);

  const rejectFile = useCallback(async (fileId: number): Promise<boolean> => {
    try {
      const params = new URLSearchParams();
      params.append('file_id', String(fileId));

      const response = await fetchWithRetry(`${API_BASE}/api/files/reject?${params}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to reject file');
      setError(null);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to reject file';
      setError(message);
      return false;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Watch Folders API
  const getWatchFolders = useCallback(async (): Promise<any[]> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/watch-folders/list`);
      if (!response.ok) throw new Error('Failed to fetch watch folders');
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load watch folders';
      setError(message);
      return [];
    }
  }, []);

  const addWatchFolder = useCallback(async (path: string): Promise<boolean> => {
    try {
      const params = new URLSearchParams();
      params.append('path', path);
      const response = await fetchWithRetry(`${API_BASE}/api/watch-folders/add?${params}`, {
        method: 'POST',
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to add watch folder');
      }
      setError(null);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to add watch folder';
      setError(message);
      return false;
    }
  }, []);

  const deleteWatchFolder = useCallback(async (folderId: number): Promise<boolean> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/watch-folders/${folderId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete watch folder');
      setError(null);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete watch folder';
      setError(message);
      return false;
    }
  }, []);

  const updateWatchFolder = useCallback(
    async (folderId: number, path?: string, enabled?: boolean): Promise<boolean> => {
      try {
        const params = new URLSearchParams();
        if (path) params.append('path', path);
        if (enabled !== undefined) params.append('enabled', String(enabled));
        
        const response = await fetchWithRetry(`${API_BASE}/api/watch-folders/${folderId}?${params}`, {
          method: 'PUT',
        });
        if (!response.ok) throw new Error('Failed to update watch folder');
        setError(null);
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update watch folder';
        setError(message);
        return false;
      }
    },
    []
  );

  const checkWatchFolderStatus = useCallback(async (folderId: number): Promise<any | null> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/watch-folders/${folderId}/status`);
      if (!response.ok) throw new Error('Failed to check folder status');
      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to check folder status';
      setError(message);
      return null;
    }
  }, []);

  // Session API
  const createSession = useCallback(async (): Promise<string | null> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/session/create`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to create session');
      const data = await response.json();
      setError(null);
      return data.id;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create session';
      setError(message);
      return null;
    }
  }, []);

  const verifySession = useCallback(async (sessionId: string): Promise<boolean> => {
    try {
      const response = await fetchWithRetry(`${API_BASE}/api/session/${sessionId}/verify`, {
        method: 'POST',
      });
      if (!response.ok) return false;
      const data = await response.json();
      return data.valid;
    } catch {
      return false;
    }
  }, []);

  return {
    checkHealth,
    getCoursesList,
    getSettings,
    createSemester,
    updateSettings,
    getQueueStats,
    getPendingFiles,
    getRecentFiles,
    confirmFile,
    rejectFile,
    getWatchFolders,
    addWatchFolder,
    deleteWatchFolder,
    updateWatchFolder,
    checkWatchFolderStatus,
    createSession,
    verifySession,
    error,
    clearError,
    isHealthy: !error,
  };
}
