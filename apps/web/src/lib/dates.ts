// Dates as the API sends them: ISO calendar days ("2027-09-01"), or timestamps whose day is the
// one they name. Read from the digits, never through `Date` in the browser's time zone, so a
// day never moves by one in a time zone west of London. Shared by Options and Routes.

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
] as const;

const DAY = /^(\d{4})-(\d{2})-(\d{2})(?:T.*)?$/;

type Day = { year: number; month: number; day: number };

const daysIn = (year: number, month: number): number =>
  month === 2
    ? year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
      ? 29
      : 28
    : [4, 6, 9, 11].includes(month)
      ? 30
      : 31;

function read(iso: string): Day | null {
  const match = DAY.exec(iso);
  if (match === null) return null;
  const [year, month, day] = [Number(match[1]), Number(match[2]), Number(match[3])];
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > daysIn(year, month)) return null;
  return { year, month, day };
}

function day(iso: string): Day {
  const found = read(iso);
  if (found === null) throw new Error(`not a calendar date: ${iso}`);
  return found;
}

/** "1 September 2027". */
export function formatDay(iso: string): string {
  const { year, month, day: date } = day(iso);
  return `${date} ${MONTHS[month - 1]} ${year}`;
}

/** "September 2027": an intake month, or a month of the plan. */
export function formatMonth(iso: string): string {
  const { year, month } = day(iso);
  return `${MONTHS[month - 1]} ${year}`;
}

/** A date box's value (`<input type="date">` gives "YYYY-MM-DD") that is a real day. */
export function isDayInput(text: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(text) && read(text) !== null;
}

/** Today's calendar day for planning dates, independent of the browser's time zone. */
export function londonToday(): string {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/London",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const part = (type: string) => parts.find((item) => item.type === type)?.value ?? "";
  return `${part("year")}-${part("month")}-${part("day")}`;
}
