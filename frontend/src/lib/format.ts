export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatTimeLabel(date?: string | Date): string {
  if (!date) return 'Recently';
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 86400000) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  if (diff < 172800000) return 'Yesterday';
  return d.toLocaleDateString();
}
