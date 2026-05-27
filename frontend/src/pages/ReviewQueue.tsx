import { useState, useEffect, useCallback } from 'react';
import { useBackendAPI } from '../hooks/useBackendAPI';
import { useToast } from '../components/Toast';
import { Icon } from '../components/ui/Icon';
import { courseColor } from '../lib/courseColors';
import { formatConfidence } from '../lib/format';
import type { FileRecord, Course } from '../types/api';

export function ReviewQueue() {
  const { getPendingFiles, confirmFile, rejectFile, getCoursesList } = useBackendAPI();
  const { addToast } = useToast();
  const [pendingFiles, setPendingFiles] = useState<FileRecord[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeIndex, setActiveIndex] = useState(0);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [editing, setEditing] = useState(false);
  const [autoConfirm, setAutoConfirm] = useState(false);

  const loadData = async () => {
    try {
      const [filesData, coursesData] = await Promise.all([getPendingFiles(), getCoursesList()]);
      setPendingFiles(filesData);
      setCourses(coursesData);
      setActiveIndex((i) => Math.min(i, Math.max(0, filesData.length - 1)));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  const currentFile = pendingFiles[activeIndex];

  const handleConfirm = async () => {
    if (!currentFile) return;
    const course = selectedCourse || currentFile.course;
    if (!course) {
      addToast('Select a course before confirming', 'error');
      return;
    }
    const ok = await confirmFile(currentFile.id, course);
    if (ok) {
      addToast(`${currentFile.name} organized to ${course}.`, 'success');
      setPendingFiles((prev) => prev.filter((f) => f.id !== currentFile.id));
      setSelectedCourse('');
      setEditing(false);
    } else {
      addToast('Failed to confirm file', 'error');
    }
  };

  const handleSkip = () => {
    if (activeIndex < pendingFiles.length - 1) {
      setActiveIndex((i) => i + 1);
    } else {
      setActiveIndex(0);
    }
    setEditing(false);
    setSelectedCourse('');
  };

  const handleReject = async () => {
    if (!currentFile) return;
    const ok = await rejectFile(currentFile.id);
    if (ok) {
      addToast('File skipped from queue', 'info');
      setPendingFiles((prev) => prev.filter((f) => f.id !== currentFile.id));
      setEditing(false);
    }
  };

  const onKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!currentFile || editing) return;
      if (e.key === 'c' || e.key === 'C') handleConfirm();
      if (e.key === 's' || e.key === 'S') handleSkip();
      if (e.key === 'e' || e.key === 'E') setEditing(true);
      if (e.key === 'ArrowDown') setActiveIndex((i) => Math.min(i + 1, pendingFiles.length - 1));
      if (e.key === 'ArrowUp') setActiveIndex((i) => Math.max(i - 1, 0));
    },
    [currentFile, editing, pendingFiles.length]
  );

  useEffect(() => {
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onKeyDown]);

  if (loading) {
    return (
      <div className="max-w-[680px] mx-auto animate-pulse space-y-4">
        <div className="h-12 bg-surface-container-low rounded-card" />
        <div className="h-64 bg-surface-container-low rounded-card" />
      </div>
    );
  }

  if (pendingFiles.length === 0) {
    return (
      <div className="max-w-[680px] mx-auto text-center py-20">
        <Icon name="check_circle" size={48} className="text-primary mx-auto mb-4" />
        <h1 className="font-display text-display-lg-mobile text-on-surface">Queue clear</h1>
        <p className="text-body-md text-on-surface-variant mt-2">No files need your attention right now.</p>
      </div>
    );
  }

  const stackBehind = pendingFiles.filter((_, i) => i !== activeIndex).slice(0, 2);

  return (
    <div className="w-full max-w-[680px] mx-auto flex flex-col pb-8">
      <div className="flex flex-col gap-2 mb-8 mt-4 md:mt-0">
        <div className="flex justify-between items-end gap-4">
          <div>
            <h1 className="font-display text-display-lg-mobile md:text-display-lg text-on-surface">Review Queue</h1>
            <p className="text-body-md text-on-surface-variant mt-1">
              {pendingFiles.length} file{pendingFiles.length !== 1 ? 's' : ''} need your attention
            </p>
          </div>
          <div className="hidden sm:flex items-center gap-3 pb-2">
            <span className="text-body-sm text-on-surface-variant">Auto-confirm &gt; 85%</span>
            <button
              type="button"
              role="switch"
              aria-checked={autoConfirm}
              onClick={() => setAutoConfirm(!autoConfirm)}
              className={`w-10 h-6 rounded-full relative transition-colors ${autoConfirm ? 'bg-primary-container' : 'bg-surface-variant'}`}
            >
              <span
                className={`absolute top-1 w-4 h-4 rounded-full bg-on-primary-container shadow transition-transform ${
                  autoConfirm ? 'right-1' : 'left-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-4 mb-8 card-surface p-3 items-center justify-center sm:justify-start">
        <span className="label-caps text-on-surface-variant mr-1">Shortcuts</span>
        {[
          ['C', 'Confirm'],
          ['E', 'Edit'],
          ['S', 'Skip'],
          ['↑↓', 'Nav'],
        ].map(([key, label]) => (
          <div key={key} className="flex items-center gap-2">
            <kbd className="font-mono text-code-path bg-surface-variant text-on-surface px-2 py-0.5 rounded border border-outline-variant min-w-[24px] text-center">
              {key}
            </kbd>
            <span className="text-body-sm text-on-surface-variant">{label}</span>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-card-gap relative">
        {currentFile && (
          <div className="bg-surface-container border border-outline-variant rounded-card p-5 md:p-6 flex flex-col gap-5 z-10 hover:border-border-interaction transition-colors shadow-card">
            <div className="flex justify-between items-start gap-4">
              <div className="flex flex-col gap-1.5 min-w-0">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: courseColor(currentFile.course) }} />
                  <span className="label-caps text-tertiary">
                    {currentFile.course || 'Unknown course'}
                    {currentFile.material_type ? ` · ${currentFile.material_type}` : ''}
                  </span>
                </div>
                <h3 className="font-mono text-title-sm text-on-surface break-all">{currentFile.name}</h3>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <div className="flex items-center gap-1.5 text-primary">
                  <Icon name="psychology" size={18} />
                  <span className="label-caps font-bold">{formatConfidence(currentFile.confidence)} MATCH</span>
                </div>
                <div className="w-24 h-1.5 bg-surface-variant rounded-full overflow-hidden mt-1">
                  <div className="h-full bg-primary rounded-full" style={{ width: `${currentFile.confidence * 100}%` }} />
                </div>
                <span className="text-[11px] text-on-surface-variant">
                  {currentFile.confidence >= 0.85 ? 'High confidence' : 'Needs human review'}
                </span>
              </div>
            </div>

            {currentFile.snippet && (
              <div className="bg-surface-container-low rounded-lg p-4 border border-surface-variant">
                <p className="text-body-sm text-on-surface-variant italic border-l-2 border-primary pl-3 line-clamp-4">
                  &ldquo;{currentFile.snippet.substring(0, 280)}
                  {currentFile.snippet.length > 280 ? '…' : ''}&rdquo;
                </p>
              </div>
            )}

            {editing && (
              <div>
                <label className="label-caps text-on-surface-variant block mb-2">Correct course</label>
                <select
                  value={selectedCourse}
                  onChange={(e) => setSelectedCourse(e.target.value)}
                  className="input-field"
                >
                  <option value="">Select course…</option>
                  {courses.map((c) => (
                    <option key={c.id} value={c.code}>
                      {c.code} — {c.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex items-center gap-3 pt-2 flex-wrap">
              <button type="button" onClick={handleConfirm} className="btn-primary">
                <Icon name="check_circle" size={18} />
                Confirm
              </button>
              <button type="button" onClick={() => setEditing(true)} className="btn-secondary">
                <Icon name="edit_document" size={18} />
                Edit Tags
              </button>
              <div className="flex-1" />
              <button type="button" onClick={handleSkip} className="btn-ghost">
                Skip
                <Icon name="arrow_forward" size={18} />
              </button>
              <button type="button" onClick={handleReject} className="btn-ghost text-error hover:text-error">
                Reject
              </button>
            </div>
          </div>
        )}

        {stackBehind.map((file, idx) => (
          <div
            key={file.id}
            className="bg-surface-container border border-surface-variant rounded-card p-5 flex flex-col gap-4 pointer-events-none"
            style={{
              opacity: idx === 0 ? 0.7 : 0.4,
              transform: `scale(${idx === 0 ? 0.98 : 0.96}) translateY(-${(idx + 1) * 8}px)`,
              marginTop: idx === 0 ? '-8px' : '-16px',
              zIndex: -10 - idx,
            }}
          >
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: courseColor(file.course) }} />
                <span className="label-caps text-on-surface-variant">{file.course || 'Unknown'}</span>
              </div>
              <h3 className="font-mono text-title-sm text-on-surface opacity-80 truncate">{file.name}</h3>
            </div>
            <div className="h-2 w-1/3 bg-surface-variant rounded-full" />
          </div>
        ))}
      </div>

      <p className="text-center text-body-sm text-outline mt-8">
        {activeIndex + 1} of {pendingFiles.length} in queue
      </p>
    </div>
  );
}
