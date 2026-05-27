import { useState, useEffect, useCallback } from 'react';
import { Dashboard } from './pages/Dashboard';
import { ReviewQueue } from './pages/ReviewQueue';
import { Library } from './pages/Library';
import { Courses } from './pages/Courses';
import { Settings } from './pages/Settings';
import { SetupWizard } from './pages/SetupWizard';
import { AppShell } from './components/layout/AppShell';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastProvider, useToast } from './components/Toast';
import { useBackendAPI } from './hooks/useBackendAPI';
import type { PageId } from './types/navigation';
import type { Settings as SettingsType } from './types/api';

function AppContent() {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [backendReady, setBackendReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(false);
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const { checkHealth, getSettings, createSemester, getPendingFiles, createSession, verifySession, error: apiError, clearError } =
    useBackendAPI();
  const { addToast } = useToast();

  const refreshSettings = useCallback(async () => {
    const s = await getSettings();
    setSettings(s);
    setNeedsSetup(!s);
    return s;
  }, [getSettings]);

  const refreshPending = useCallback(async () => {
    const files = await getPendingFiles();
    setPendingCount(files.length);
  }, [getPendingFiles]);

  useEffect(() => {
    const init = async () => {
      // Initialize or verify session
      const storedSessionId = localStorage.getItem('acadsort_session_id');
      let currentSessionId = storedSessionId;

      if (storedSessionId) {
        // Verify existing session
        const isValid = await verifySession(storedSessionId);
        if (!isValid) {
          // Session expired, create new one
          const newSessionId = await createSession();
          if (newSessionId) {
            currentSessionId = newSessionId;
            localStorage.setItem('acadsort_session_id', newSessionId);
          }
        }
      } else {
        // Create new session
        const newSessionId = await createSession();
        if (newSessionId) {
          currentSessionId = newSessionId;
          localStorage.setItem('acadsort_session_id', newSessionId);
        }
      }

      if (currentSessionId) {
        setSessionId(currentSessionId);
      }

      // Check backend health
      const healthy = await checkHealth();
      setBackendReady(healthy);
      if (healthy) {
        await refreshSettings();
        await refreshPending();
      }
      setLoading(false);
    };
    init();

    const interval = setInterval(async () => {
      const healthy = await checkHealth();
      setBackendReady(healthy);
      if (healthy) {
        await refreshPending();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [checkHealth, refreshSettings, refreshPending, createSession, verifySession]);

  useEffect(() => {
    if (apiError) {
      addToast(apiError, 'error');
      const timer = setTimeout(() => clearError(), 5000);
      return () => clearTimeout(timer);
    }
  }, [apiError, addToast, clearError]);

  const handlePageChange = (page: PageId) => {
    clearError();
    setCurrentPage(page);
  };

  const handleSetupComplete = async (semesterName: string, organizationStyle: 'week' | 'type') => {
    const ok = await createSemester(semesterName, organizationStyle);
    if (ok) {
      await refreshSettings();
      setNeedsSetup(false);
      addToast('Semester configured. Welcome to AcadSort!', 'success');
    } else {
      addToast('Could not create semester. Try again.', 'error');
    }
  };

  const handleNewSemester = () => setNeedsSetup(true);

  const handleUpload = () => {
    addToast('Drop files in your Downloads folder — AcadSort will detect them automatically.', 'info', 5000);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface">
        <div className="text-center animate-fade-in">
          <div className="w-10 h-10 border-2 border-outline-variant border-t-primary rounded-full animate-spin mx-auto mb-4" />
          <p className="font-display text-title-sm text-on-surface">Loading workspace</p>
        </div>
      </div>
    );
  }

  if (!backendReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface px-4">
        <div className="text-center max-w-md card-surface p-8">
          <h1 className="font-display text-headline-md text-on-surface mb-2">Connection Error</h1>
          <p className="text-body-sm text-on-surface-variant mb-6">
            Unable to reach the local backend at 127.0.0.1:8765. Start the Python server and retry.
          </p>
          <button type="button" onClick={() => window.location.reload()} className="btn-primary mx-auto">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (needsSetup) {
    return <SetupWizard onComplete={handleSetupComplete} onCancel={() => settings && setNeedsSetup(false)} />;
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard settings={settings} onNewSemester={handleNewSemester} />;
      case 'library':
        return <Library searchQuery={searchQuery} />;
      case 'review':
        return <ReviewQueue />;
      case 'courses':
        return <Courses searchQuery={searchQuery} />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard settings={settings} onNewSemester={handleNewSemester} />;
    }
  };

  return (
    <AppShell
      currentPage={currentPage}
      onPageChange={handlePageChange}
      semesterName={settings?.semester_name}
      pendingCount={pendingCount}
      searchQuery={searchQuery}
      onSearchChange={setSearchQuery}
      onUpload={handleUpload}
    >
      {renderPage()}
    </AppShell>
  );
}

export function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </ErrorBoundary>
  );
}
