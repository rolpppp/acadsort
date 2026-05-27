import type { QueueStats } from '../types/api';

export interface HubStatusInput {
  stats: QueueStats | null;
  filesSorted: number;
  inQueue: number;
  recentActivityCount: number;
}

/** Subtitle under the dashboard greeting — reflects live queue / organize state. */
export function getHubStatusMessage({
  stats,
  filesSorted,
  inQueue,
  recentActivityCount,
}: HubStatusInput): string {
  const rejected = stats?.total_rejected ?? 0;
  const avgConfidence = stats?.avg_confidence ?? 0;

  if (filesSorted === 0 && inQueue === 0) {
    return 'No files organized yet. Save something to Downloads and AcadSort will pick it up.';
  }

  if (inQueue > 0 && filesSorted === 0) {
    const fileWord = inQueue === 1 ? 'file needs' : 'files need';
    return `${inQueue} ${fileWord} your review in the queue — confirm or edit when you're ready.`;
  }

  if (inQueue > 0) {
    const queuePart =
      inQueue === 1
        ? '1 file is waiting in your review queue'
        : `${inQueue} files are waiting in your review queue`;
    const sortedPart =
      filesSorted === 1 ? '1 file is already sorted' : `${filesSorted} files are sorted`;
    return `${sortedPart}. ${queuePart.charAt(0).toUpperCase() + queuePart.slice(1)}.`;
  }

  if (inQueue === 0 && filesSorted > 0) {
    const confidenceNote =
      avgConfidence >= 0.85
        ? ' Auto-sort confidence is strong.'
        : avgConfidence > 0
          ? ' Some items may need a quick glance now and then.'
          : '';

    if (recentActivityCount > 0) {
      return `Your academic hub is organized — ${filesSorted} file${filesSorted === 1 ? '' : 's'} sorted and the queue is clear.${confidenceNote}`;
    }

    return `Everything in the queue is handled. ${filesSorted} file${filesSorted === 1 ? ' is' : 's are'} sorted this semester.${confidenceNote}`;
  }

  if (rejected > 0) {
    return `${rejected} file${rejected === 1 ? ' was' : 's were'} skipped earlier. The rest of your hub looks good.`;
  }

  return 'Your workspace is ready. Drop new files in Downloads whenever you need them sorted.';
}
