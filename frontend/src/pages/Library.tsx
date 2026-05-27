import { useState, useEffect, useMemo } from 'react';
import { useBackendAPI } from '../hooks/useBackendAPI';
import { Icon } from '../components/ui/Icon';
import { courseColor, fileIcon } from '../lib/courseColors';
import { formatConfidence } from '../lib/format';
import type { FileRecord } from '../types/api';

interface LibraryProps {
  searchQuery: string;
}

export function Library({ searchQuery }: LibraryProps) {
  const { getRecentFiles } = useBackendAPI();
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRecentFiles().then((data) => {
      setFiles(data);
      setLoading(false);
    });
    const interval = setInterval(() => getRecentFiles().then(setFiles), 5000);
    return () => clearInterval(interval);
  }, [getRecentFiles]);

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return files;
    return files.filter(
      (f) =>
        f.name.toLowerCase().includes(q) ||
        (f.course?.toLowerCase().includes(q) ?? false) ||
        f.material_type?.toLowerCase().includes(q)
    );
  }, [files, searchQuery]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto animate-pulse space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-16 bg-surface-container-low rounded-card" />
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto w-full">
      <div className="mb-8">
        <h1 className="font-display text-display-lg-mobile md:text-display-lg text-on-surface">Library</h1>
        <p className="text-body-md text-on-surface-variant mt-2">
          {filtered.length} document{filtered.length !== 1 ? 's' : ''} in your organized workspace
        </p>
      </div>

      {filtered.length === 0 ? (
        <div className="card-surface p-12 text-center">
          <Icon name="auto_stories" size={40} className="text-outline mx-auto mb-3" />
          <p className="text-on-surface-variant">No files match your search.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {filtered.map((file) => (
            <div
              key={file.id}
              className="card-surface-interactive p-4 flex items-center gap-4 group"
            >
              <div
                className="w-1 h-10 rounded-full shrink-0"
                style={{ backgroundColor: courseColor(file.course) }}
              />
              <span className="inline-flex bg-surface-variant p-2 rounded-md text-secondary group-hover:text-primary transition-colors">
                <Icon name={fileIcon(file.material_type, file.name)} size={20} />
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-body-sm text-on-surface font-medium truncate group-hover:text-primary transition-colors">
                  {file.name}
                </p>
                <p className="font-mono text-code-path text-on-surface-variant mt-0.5">
                  {file.course || 'Unassigned'} · {file.material_type} · {file.status}
                </p>
              </div>
              <div className="text-right shrink-0">
                <p className="label-caps text-primary">{formatConfidence(file.confidence)}</p>
                {file.week != null && (
                  <p className="font-mono text-code-path text-outline text-[11px]">Week {file.week}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
