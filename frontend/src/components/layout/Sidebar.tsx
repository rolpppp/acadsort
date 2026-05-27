import { Icon } from '../ui/Icon';
import type { PageId } from '../../types/navigation';
import { PAGE_LABELS } from '../../types/navigation';

interface SidebarProps {
  currentPage: PageId;
  onPageChange: (page: PageId) => void;
  semesterName?: string;
  pendingCount?: number;
  onUpload?: () => void;
}

const NAV_ITEMS: { id: PageId; icon: string }[] = [
  { id: 'dashboard', icon: 'dashboard' },
  { id: 'library', icon: 'auto_stories' },
  { id: 'review', icon: 'checklist' },
  { id: 'courses', icon: 'school' },
];

export function Sidebar({
  currentPage,
  onPageChange,
  semesterName = 'No semester',
  pendingCount = 0,
  onUpload,
}: SidebarProps) {
  return (
    <nav className="hidden md:flex w-sidebar-width h-screen fixed left-0 top-0 bg-surface-container border-r border-outline-variant flex-col py-8 px-4 gap-4 z-50">
      <div className="px-2">
        <h1 className="font-display text-headline-md font-extrabold text-primary tracking-tight">
          AcadSort
        </h1>
        <p className="text-on-surface-variant text-body-sm mt-1 truncate">{semesterName}</p>
      </div>

      <button type="button" onClick={onUpload} className="btn-primary w-full mt-1">
        <Icon name="upload" size={18} />
        Upload Files
      </button>

      <div className="flex flex-col gap-1 mt-2 flex-1">
        {NAV_ITEMS.map(({ id, icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => onPageChange(id)}
            className={currentPage === id ? 'nav-item-active w-full text-left' : 'nav-item w-full text-left'}
            data-active={currentPage === id ? 'true' : 'false'}
          >
            <Icon name={icon} size={22} filled={currentPage === id} />
            <span className="label-caps">{PAGE_LABELS[id]}</span>
            {id === 'review' && pendingCount > 0 && (
              <span className="ml-auto bg-primary/20 text-primary text-[10px] font-bold px-2 py-0.5 rounded-full">
                {pendingCount}
              </span>
            )}
          </button>
        ))}

        <button
          type="button"
          onClick={() => onPageChange('settings')}
          className={
            currentPage === 'settings'
              ? 'nav-item-active w-full text-left mt-auto'
              : 'nav-item w-full text-left mt-auto'
          }
          data-active={currentPage === 'settings' ? 'true' : 'false'}
        >
          <Icon name="settings" size={22} filled={currentPage === 'settings'} />
          <span className="label-caps">Settings</span>
        </button>
      </div>
    </nav>
  );
}
