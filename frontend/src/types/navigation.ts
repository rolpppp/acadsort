export type PageId = 'dashboard' | 'library' | 'review' | 'courses' | 'settings';

export const PAGE_LABELS: Record<PageId, string> = {
  dashboard: 'Dashboard',
  library: 'Library',
  review: 'Review Queue',
  courses: 'Courses',
  settings: 'Settings',
};
