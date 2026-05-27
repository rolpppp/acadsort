/** Course palette from Scholar Noir design — harmonious hues for quick scanning */
const COURSE_PALETTE = [
  '#8E9B90',
  '#A88C7D',
  '#7D8FA8',
  '#9E8B9A',
  '#8A9E8B',
  '#9E9A7D',
  '#7D9E9A',
  '#9E7D8A',
] as const;

export function courseColor(code: string | null | undefined): string {
  if (!code) return '#9a8f83';
  let hash = 0;
  for (let i = 0; i < code.length; i++) {
    hash = code.charCodeAt(i) + ((hash << 5) - hash);
  }
  return COURSE_PALETTE[Math.abs(hash) % COURSE_PALETTE.length];
}

export function fileIcon(materialType?: string, name?: string): string {
  const ext = name?.split('.').pop()?.toLowerCase() ?? '';
  if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) return 'image';
  if (['epub', 'mobi'].includes(ext)) return 'menu_book';
  if (materialType?.toLowerCase().includes('lab')) return 'science';
  if (materialType?.toLowerCase().includes('exam')) return 'quiz';
  return 'description';
}
