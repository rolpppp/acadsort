import greetingsRaw from '../data/greetings.txt?raw';

export type GreetingPeriod =
  | 'midnight'
  | 'late_night'
  | 'early_morning'
  | 'morning'
  | 'late_morning'
  | 'lunch'
  | 'afternoon'
  | 'late_afternoon'
  | 'evening'
  | 'night';

const SESSION_KEY = 'acadsort-session-greeting';

function parseGreetingsFile(raw: string): Record<GreetingPeriod, string[]> {
  const result = {} as Record<GreetingPeriod, string[]>;
  let current: GreetingPeriod | null = null;

  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    const section = trimmed.match(/^\[([a-z_]+)\]$/);
    if (section) {
      current = section[1] as GreetingPeriod;
      if (!result[current]) result[current] = [];
      continue;
    }

    if (current) {
      result[current].push(trimmed);
    }
  }

  return result;
}

const GREETINGS_BY_PERIOD = parseGreetingsFile(greetingsRaw);

export function getGreetingPeriod(hour: number = new Date().getHours()): GreetingPeriod {
  if (hour >= 0 && hour < 4) return 'midnight';
  if (hour >= 4 && hour < 6) return 'early_morning';
  if (hour >= 6 && hour < 10) return 'morning';
  if (hour >= 10 && hour < 12) return 'late_morning';
  if (hour >= 12 && hour < 14) return 'lunch';
  if (hour >= 14 && hour < 17) return 'afternoon';
  if (hour >= 17 && hour < 19) return 'late_afternoon';
  if (hour >= 19 && hour < 22) return 'evening';
  if (hour >= 22 && hour < 24) return 'late_night';
  return 'night';
}

function pickRandom<T>(items: T[]): T {
  return items[Math.floor(Math.random() * items.length)];
}

/** One greeting per browser session, keyed by time-of-day category. */
export function getSessionGreeting(): string {
  if (typeof sessionStorage !== 'undefined') {
    const cached = sessionStorage.getItem(SESSION_KEY);
    if (cached) return cached;
  }

  const period = getGreetingPeriod();
  const pool = GREETINGS_BY_PERIOD[period] ?? GREETINGS_BY_PERIOD.morning ?? ['Hello, Isko.'];
  const greeting = pickRandom(pool);

  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.setItem(SESSION_KEY, greeting);
  }

  return greeting;
}
