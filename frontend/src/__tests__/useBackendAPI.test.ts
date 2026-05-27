import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useBackendAPI, NetworkError, TimeoutError } from '../hooks/useBackendAPI';

describe('useBackendAPI Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('checkHealth', () => {
    it('returns true when health check succeeds', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200
      });

      const { result } = renderHook(() => useBackendAPI());
      const isHealthy = await result.current.checkHealth();

      expect(isHealthy).toBe(true);
    });

    it('returns false when health check fails', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      const { result } = renderHook(() => useBackendAPI());
      const isHealthy = await result.current.checkHealth();

      expect(isHealthy).toBe(false);
    });

    it('returns false on network error', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useBackendAPI());
      const isHealthy = await result.current.checkHealth();

      expect(isHealthy).toBe(false);
    });
  });

  describe('getCoursesList', () => {
    it('returns courses list on success', async () => {
      const mockCourses = [
        { code: 'CS101', title: 'Intro to CS' },
        { code: 'MATH101', title: 'Calculus I' }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCourses
      });

      const { result } = renderHook(() => useBackendAPI());
      const courses = await result.current.getCoursesList();

      expect(courses).toEqual(mockCourses);
      expect(result.current.error).toBeNull();
    });

    it('sets error state on failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404
      });

      const { result } = renderHook(() => useBackendAPI());
      const courses = await result.current.getCoursesList();

      expect(courses).toEqual([]);
      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });
    });

    it('retries on network error', async () => {
      vi.useFakeTimers();
      (global.fetch as any)
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => []
        });

      const { result } = renderHook(() => useBackendAPI());
      const coursesPromise = result.current.getCoursesList();
      await vi.runAllTimersAsync();
      await coursesPromise;

      expect(global.fetch).toHaveBeenCalledTimes(2);
      vi.useRealTimers();
    });
  });

  describe('clearError', () => {
    it('clears error state', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404
      });

      const { result } = renderHook(() => useBackendAPI());
      await result.current.getCoursesList();

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Error Classes', () => {
    it('NetworkError is instanceof Error', () => {
      const error = new NetworkError('Test error');
      expect(error).toBeInstanceOf(Error);
      expect(error.name).toBe('NetworkError');
    });

    it('TimeoutError is instanceof Error', () => {
      const error = new TimeoutError('Test timeout');
      expect(error).toBeInstanceOf(Error);
      expect(error.name).toBe('TimeoutError');
    });
  });
});
