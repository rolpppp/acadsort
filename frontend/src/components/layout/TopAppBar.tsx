import { Icon } from '../ui/Icon';
import type { PageId } from '../../types/navigation';

interface TopAppBarProps {
  currentPage: PageId;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onMenuOpen?: () => void;
  showMobileMenu?: boolean;
}

export function TopAppBar({
  currentPage,
  searchQuery,
  onSearchChange,
  onMenuOpen,
  showMobileMenu,
}: TopAppBarProps) {
  const showSearch = currentPage === 'library' || currentPage === 'courses';

  return (
    <>
      <header className="md:hidden h-14 w-full fixed top-0 z-50 bg-surface border-b border-outline-variant flex justify-between items-center px-margin-mobile">
        <span className="font-display text-headline-md font-bold text-primary">AcadSort</span>
        <div className="flex gap-3">
          {showMobileMenu && (
            <button type="button" onClick={onMenuOpen} className="text-on-surface-variant hover:text-primary">
              <Icon name="menu" />
            </button>
          )}
          <button type="button" className="text-on-surface-variant hover:text-primary">
            <Icon name="notifications" />
          </button>
        </div>
      </header>

      <header className="h-12 w-full fixed top-0 z-40 bg-surface border-b border-outline-variant hidden md:flex justify-between items-center px-margin-desktop md:ml-sidebar-width md:w-[calc(100%-220px)]">
        <div className="flex items-center gap-6 h-full text-body-sm text-on-surface-variant">
          <span className={currentPage === 'library' ? 'text-primary font-medium' : ''}>Documents</span>
          <span className="opacity-50 cursor-not-allowed" title="Coming soon">
            Flashcards
          </span>
          <span className="opacity-50 cursor-not-allowed" title="Coming soon">
            Summaries
          </span>
        </div>

        {showSearch && (
          <div className="flex items-center gap-5">
            <div className="relative group">
              <Icon
                name="search"
                size={18}
                className="absolute left-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant group-focus-within:text-primary"
              />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder="Search library..."
                className="bg-surface-container text-on-surface font-body-sm rounded-full pl-9 pr-4 py-1.5 w-64 border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
              />
            </div>
            <button type="button" className="text-on-surface-variant hover:text-primary transition-colors">
              <Icon name="notifications" />
            </button>
            <button type="button" className="text-on-surface-variant hover:text-primary transition-colors">
              <Icon name="account_circle" />
            </button>
          </div>
        )}
      </header>
    </>
  );
}
