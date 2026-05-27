import { useState, useEffect, useMemo } from 'react';
import { useBackendAPI } from '../hooks/useBackendAPI';
import { useToast } from '../components/Toast';
import { Icon } from '../components/ui/Icon';
import { courseColor } from '../lib/courseColors';
import { fileIcon } from '../lib/courseColors';
import { formatConfidence } from '../lib/format';
import { getSessionGreeting } from '../lib/greetings';
import { getHubStatusMessage } from '../lib/statusMessage';
import type { QueueStats, FileRecord, Course, Settings } from '../types/api';

interface DashboardProps {
  settings: Settings | null;
  onNewSemester?: () => void;
}

export function Dashboard({ settings, onNewSemester }: DashboardProps) {
  const { getQueueStats, getRecentFiles, getCoursesList } = useBackendAPI();
  const { addToast } = useToast();
  const [stats, setStats] = useState<QueueStats | null>(null);
  const [recentFiles, setRecentFiles] = useState<FileRecord[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [sessionGreeting] = useState(() => getSessionGreeting());

  const loadData = async () => {
    try {
      const [statsData, filesData, coursesData] = await Promise.all([
        getQueueStats(),
        getRecentFiles(),
        getCoursesList(),
      ]);
      setStats(statsData);
      setRecentFiles(filesData);
      setCourses(coursesData);
    } catch {
      addToast('Failed to load dashboard', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const courseBreakdown = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const f of recentFiles) {
      const code = f.course || 'Unknown';
      counts[code] = (counts[code] || 0) + 1;
    }
    return courses
      .map((c) => ({ code: c.code, name: c.name, count: counts[c.code] || 0 }))
      .filter((c) => c.count > 0)
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);
  }, [courses, recentFiles]);

  const maxCount = Math.max(...courseBreakdown.map((c) => c.count), 1);
  const filesSorted = (stats?.total_confirmed ?? 0) + recentFiles.filter((f) => f.status === 'AUTO_MOVED').length;
  const inQueue = stats?.total_pending ?? 0;
  const accuracy = stats?.avg_confidence ? Math.round(stats.avg_confidence * 100) : 0;
  const organizedPct = filesSorted > 0 ? Math.min(Math.round((filesSorted / (filesSorted + inQueue + 1)) * 100), 100) : 0;
  const ringOffset = 238.76 - (238.76 * organizedPct) / 100;

  const statusMessage = getHubStatusMessage({
    stats,
    filesSorted,
    inQueue,
    recentActivityCount: recentFiles.length,
  });

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="max-w-[960px] mx-auto w-full">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <h2 className="font-display text-display-lg-mobile md:text-display-lg text-on-surface tracking-tight leading-tight">
            {sessionGreeting}
          </h2>
          <p className="text-body-md text-on-surface-variant mt-2 max-w-lg leading-relaxed">
            {statusMessage}
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {settings && (
            <span className="bg-surface-container-high text-on-surface-variant label-caps px-4 py-2 rounded-full border border-outline-variant">
              {settings.semester_name}
            </span>
          )}
          <button
            type="button"
            onClick={onNewSemester}
            className="border border-outline-variant text-primary hover:bg-surface-variant hover:border-outline label-caps px-4 py-2 rounded-full transition-colors"
          >
            New Semester
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-card-gap auto-rows-fr">
        <StatCard icon="folder_open" value={filesSorted} label="Files Sorted" />
        <StatCard
          icon="hourglass_empty"
          value={inQueue}
          label="In Queue"
          highlight
          pulse={inQueue > 0}
        />
        <StatCard icon="verified" value={`${accuracy}%`} label="Auto-sort Accuracy" accent="tertiary" />
        <div className="card-surface flex items-center justify-center min-h-[9.5rem] p-4 shadow-sm overflow-hidden">
          <div className="relative">
            <svg className="w-24 h-24 -rotate-90" viewBox="0 0 96 96">
              <circle cx="48" cy="48" r="38" fill="transparent" stroke="currentColor" strokeWidth="6" className="text-surface-variant" />
              <circle
                cx="48"
                cy="48"
                r="38"
                fill="transparent"
                stroke="currentColor"
                strokeWidth="6"
                strokeLinecap="round"
                className="text-primary transition-all duration-1000"
                strokeDasharray="238.76"
                strokeDashoffset={ringOffset}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-display text-title-sm text-on-surface">{organizedPct}%</span>
              <span className="label-caps text-outline text-[10px] tracking-widest">ORGANIZED</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-card-gap mt-card-gap">
        <div className="col-span-1 lg:col-span-2 card-surface p-6 shadow-sm overflow-hidden">
          <h3 className="font-display text-title-sm text-on-surface mb-6 leading-snug">Course Breakdown</h3>
          {courseBreakdown.length === 0 ? (
            <p className="text-body-sm text-on-surface-variant">No organized files yet. Drop files in Downloads to get started.</p>
          ) : (
            <div className="flex flex-col gap-5">
              {courseBreakdown.map((c) => (
                <div key={c.code} className="flex items-center gap-4 group">
                  <div
                    className="w-1.5 h-8 rounded-full shrink-0 opacity-80 group-hover:opacity-100"
                    style={{ backgroundColor: courseColor(c.code) }}
                  />
                  <div className="w-28 text-body-sm text-on-surface truncate">{c.code}</div>
                  <div className="flex-grow bg-surface-container-highest h-1.5 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${(c.count / maxCount) * 100}%`,
                        backgroundColor: courseColor(c.code),
                      }}
                    />
                  </div>
                  <div className="w-20 text-right font-mono text-code-path text-on-surface-variant">
                    {String(c.count).padStart(2, '0')}{' '}
                    <span className="text-outline">files</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card-surface p-6 shadow-sm flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-display text-title-sm text-on-surface">Recent Auto-moves</h3>
            <span className="label-caps text-outline border border-surface-variant px-2 py-0.5 rounded-md">TODAY</span>
          </div>
          {recentFiles.length === 0 ? (
            <p className="text-body-sm text-on-surface-variant flex-1">No recent activity.</p>
          ) : (
            <div className="flex flex-col gap-6 relative flex-1">
              <div className="absolute left-[11px] top-6 bottom-4 w-px bg-surface-variant z-0" />
              {recentFiles.slice(0, 5).map((file) => (
                <div key={file.id} className="flex gap-4 relative z-10 group">
                  <div className="shrink-0 bg-surface-container-low py-1">
                    <span className="inline-flex bg-surface-variant p-1.5 rounded-md group-hover:text-primary transition-colors">
                      <Icon name={fileIcon(file.material_type, file.name)} size={20} className="text-secondary" />
                    </span>
                  </div>
                  <div className="min-w-0">
                    <div className="text-body-sm text-on-surface group-hover:text-primary transition-colors truncate">
                      {file.name}
                    </div>
                    <div className="text-body-sm text-on-surface-variant mt-0.5">
                      {file.course ? `Moved to ${file.course}` : 'Processed'}
                    </div>
                    <div className="font-mono text-code-path text-outline mt-1">
                      {formatConfidence(file.confidence)} confidence
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  value,
  label,
  highlight,
  pulse,
}: {
  icon: string;
  value: string | number;
  label: string;
  highlight?: boolean;
  pulse?: boolean;
  accent?: 'tertiary';
}) {
  return (
    <div
      className={`card-surface-interactive min-h-[9.5rem] p-4 flex flex-col shadow-sm overflow-hidden ${
        highlight ? 'border-primary/30 hover:border-primary/60' : ''
      }`}
    >
      <div className="flex justify-between items-start shrink-0 gap-2">
        <div className={`p-2 rounded-lg shrink-0 ${highlight ? 'bg-primary/10' : 'bg-surface-container-highest'}`}>
          <Icon name={icon} size={22} className={highlight ? 'text-primary' : 'text-outline'} />
        </div>
        {pulse && (
          <span className="relative flex h-2.5 w-2.5 shrink-0 mt-1">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary" />
          </span>
        )}
      </div>
      <div className="mt-auto pt-4 min-h-0">
        <p
          className={`font-display text-2xl md:text-[1.35rem] leading-none tabular-nums ${
            highlight ? 'text-primary' : 'text-on-surface'
          }`}
        >
          {value}
        </p>
        <p
          className={`text-[0.8125rem] leading-snug mt-2 line-clamp-2 ${
            highlight ? 'text-primary/80' : 'text-on-surface-variant'
          }`}
        >
          {label}
        </p>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="max-w-[960px] mx-auto animate-pulse space-y-6">
      <div className="h-16 bg-surface-container-low rounded-card" />
      <div className="grid grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 bg-surface-container-low rounded-card" />
        ))}
      </div>
      <div className="h-64 bg-surface-container-low rounded-card" />
    </div>
  );
}
