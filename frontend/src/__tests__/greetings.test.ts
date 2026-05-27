import { describe, it, expect, beforeEach } from 'vitest';
import { getGreetingPeriod, getSessionGreeting } from '../lib/greetings';

describe('greetings', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('maps hours to greeting periods', () => {
    expect(getGreetingPeriod(2)).toBe('midnight');
    expect(getGreetingPeriod(5)).toBe('early_morning');
    expect(getGreetingPeriod(8)).toBe('morning');
    expect(getGreetingPeriod(13)).toBe('lunch');
    expect(getGreetingPeriod(15)).toBe('afternoon');
    expect(getGreetingPeriod(20)).toBe('evening');
    expect(getGreetingPeriod(23)).toBe('late_night');
  });

  it('returns the same greeting within a session', () => {
    const first = getSessionGreeting();
    const second = getSessionGreeting();
    expect(first).toBe(second);
    expect(first.length).toBeGreaterThan(0);
  });
});
