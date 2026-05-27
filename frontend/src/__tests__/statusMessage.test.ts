import { describe, it, expect } from 'vitest';
import { getHubStatusMessage } from '../lib/statusMessage';

describe('getHubStatusMessage', () => {
  it('prompts when nothing is organized', () => {
    const msg = getHubStatusMessage({
      stats: null,
      filesSorted: 0,
      inQueue: 0,
      recentActivityCount: 0,
    });
    expect(msg).toMatch(/No files organized yet/i);
  });

  it('mentions queue when files are pending', () => {
    const msg = getHubStatusMessage({
      stats: { total_pending: 3, total_confirmed: 5, total_rejected: 0, avg_confidence: 0.8 },
      filesSorted: 5,
      inQueue: 3,
      recentActivityCount: 2,
    });
    expect(msg).toMatch(/review queue/i);
  });

  it('celebrates clear queue when organized', () => {
    const msg = getHubStatusMessage({
      stats: { total_pending: 0, total_confirmed: 10, total_rejected: 0, avg_confidence: 0.92 },
      filesSorted: 10,
      inQueue: 0,
      recentActivityCount: 4,
    });
    expect(msg).toMatch(/organized/i);
    expect(msg).toMatch(/clear/i);
  });
});
