// Deterministic code over the made-up list: the only source of what the world shows.
// Nothing here guesses. A role is joined to another only by the essential skills both list,
// never by shared words in their titles.
import type { Role } from "./data.ts";

/** An unexpected connection needs at least this many shared essential skills. */
export const MIN_CONNECTION_SHARED = 4;
/** A first destination needs at least this many shared essential skills. */
export const MIN_DESTINATION_SHARED = 3;
/** The first scatter shows at most this many destinations. */
export const MAX_DESTINATIONS = 5;
const MAX_MATCHES = 6;

export type Destination = { readonly role: Role; readonly shared: readonly string[] };

export type Connection = Destination & {
  /** The destination's essential skills the person's role does not list: not known yet. */
  readonly unknown: readonly string[];
};

export const titleWords = (title: string): Set<string> =>
  new Set(title.toLowerCase().split(/[^a-z]+/).filter(Boolean));

const byTitle = (a: Role, b: Role): number => a.title.localeCompare(b.title);

export function matchRoles(query: string, roles: readonly Role[]): Role[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const ranked: { role: Role; rank: number }[] = [];
  for (const role of roles) {
    const title = role.title.toLowerCase();
    if (title.startsWith(q)) ranked.push({ role, rank: 0 });
    else if (title.split(/\s+/).some((word, i) => i > 0 && word.startsWith(q)))
      ranked.push({ role, rank: 1 });
  }
  ranked.sort((a, b) => a.rank - b.rank || byTitle(a.role, b.role));
  return ranked.slice(0, MAX_MATCHES).map((r) => r.role);
}

/** The essential skills both roles list, in the person's order. */
export const sharedSkills = (person: Role, other: Role): string[] =>
  person.skills.filter((s) => other.skills.includes(s));

const ranked = (person: Role, candidates: readonly Role[]): Destination[] =>
  candidates
    .map((role) => ({ role, shared: sharedSkills(person, role) }))
    .sort((a, b) => b.shared.length - a.shared.length || byTitle(a.role, b.role));

/**
 * The role from another field, sharing no word with the person's title, that shares the most
 * essential skills (at least MIN_CONNECTION_SHARED; ties broken by title). Null when none does:
 * a revelation with no source is not shown.
 */
export function unexpectedConnection(person: Role, roles: readonly Role[]): Connection | null {
  const words = titleWords(person.title);
  const eligible = roles.filter(
    (r) => r.field !== person.field && ![...titleWords(r.title)].some((w) => words.has(w)),
  );
  const best = ranked(person, eligible)[0];
  if (!best || best.shared.length < MIN_CONNECTION_SHARED) return null;
  return { ...best, unknown: best.role.skills.filter((s) => !person.skills.includes(s)) };
}

/**
 * The first scatter: up to MAX_DESTINATIONS other roles sharing at least MIN_DESTINATION_SHARED
 * essential skills, chosen by count, then listed by title so that position never means rank.
 */
export function destinationsFor(
  person: Role,
  roles: readonly Role[],
  exclude: ReadonlySet<string>,
): Destination[] {
  const candidates = roles.filter((r) => r.id !== person.id && !exclude.has(r.id));
  return ranked(person, candidates)
    .filter((d) => d.shared.length >= MIN_DESTINATION_SHARED)
    .slice(0, MAX_DESTINATIONS)
    .sort((a, b) => byTitle(a.role, b.role));
}

/** Built only from computed facts, and about the two roles, never about the person. */
export function connectionSentence(person: Role, found: Connection): string {
  const first = person.plural;
  const second = found.role.plural.charAt(0).toLowerCase() + found.role.plural.slice(1);
  return `${first} and ${keepAcronym(second, found.role.plural)} share ${found.shared.length} essential skills.`;
}

// "HR advisers" and "IT support technicians" keep their capitals mid-sentence.
const keepAcronym = (lowered: string, original: string): string =>
  /^[A-Z]{2}\b/.test(original) ? original : lowered;
