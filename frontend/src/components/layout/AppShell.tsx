import { ReactNode, useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopAppBar } from './TopAppBar';
import { Icon } from '../ui/Icon';
import type { PageId } from '../../types/navigation';
import { PAGE_LABELS } from '../../types/navigation';

interface AppShellProps {
  children: ReactNode;
  currentPage: PageId;
  onPageChange: (page: PageId) => void;
  semesterName?: string;
  pendingCount?: number;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onUpload?: () => void;
}

const MOBILE_NAV: PageId[] = ['dashboard', 'library', 'review', 'courses', 'settings'];

export function AppShell({
  children,
  currentPage,
  onPageChange,
  semesterName,
  pendingCount,
  searchQuery,
  onSearchChange,
  onUpload,
}: AppShellProps) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-surface flex">
      <Sidebar
        currentPage={currentPage}
        onPageChange={(p) => {
          onPageChange(p);
          setMobileNavOpen(false);
        }}
        semesterName={semesterName}
        pendingCount={pendingCount}
        onUpload={onUpload}
      />

      {mobileNavOpen && (
        <div
          className="md:hidden fixed inset-0 z-[60] bg-black/60"
          onClick={() => setMobileNavOpen(false)}
          role="presentation"
        />
      )}
      {mobileNavOpen && (
        <div className="md:hidden fixed left-0 top-0 bottom-0 w-[220px] z-[70] bg-surface-container border-r border-outline-variant p-4 pt-16">
          {MOBILE_NAV.map((id) => (
            <button
              key={id}
              type="button"
              onClick={() => {
                onPageChange(id);
                setMobileNavOpen(false);
              }}
              className={currentPage === id ? 'nav-item-active w-full text-left mb-1' : 'nav-item w-full text-left mb-1'}
            >
              {PAGE_LABELS[id]}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 flex flex-col md:ml-sidebar-width min-h-screen">
        <TopAppBar
          currentPage={currentPage}
          searchQuery={searchQuery}
          onSearchChange={onSearchChange}
          onMenuOpen={() => setMobileNavOpen(true)}
          showMobileMenu
        />

        <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface-container border-t border-outline-variant flex justify-around py-2 px-1">
          {(['dashboard', 'review', 'library', 'settings'] as PageId[]).map((id) => (
            <button
              key={id}
              type="button"
              onClick={() => onPageChange(id)}
              className={`flex flex-col items-center gap-0.5 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${
                currentPage === id ? 'text-primary' : 'text-on-surface-variant'
              }`}
            >
              <Icon
                name={id === 'dashboard' ? 'dashboard' : id === 'review' ? 'checklist' : id === 'library' ? 'auto_stories' : 'settings'}
                size={22}
                filled={currentPage === id}
              />
              {id === 'review' ? 'Queue' : PAGE_LABELS[id].split(' ')[0]}
            </button>
          ))}
        </nav>

        <main className="flex-1 pt-14 md:pt-12 px-margin-mobile md:px-margin-desktop pb-24 md:pb-12 overflow-x-hidden animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
}
