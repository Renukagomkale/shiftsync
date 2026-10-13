import { addDays, format, parseISO, startOfWeek } from "date-fns";

const parts = (ms, tz) =>
  Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: tz,
      hourCycle: "h23",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
      .formatToParts(ms)
      .map((part) => [part.type, part.value])
  );

export const dayKey = (iso, tz) => {
  const p = parts(new Date(iso).getTime(), tz);
  return `${p.year}-${p.month}-${p.day}`;
};

export const timeOf = (iso, tz) => {
  const p = parts(new Date(iso).getTime(), tz);
  return `${p.hour}:${p.minute}`;
};

export const todayKey = (tz) => dayKey(new Date().toISOString(), tz);

const offsetOf = (ms, tz) => {
  const p = parts(ms, tz);
  const asUtc = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute);
  return asUtc - Math.floor(ms / 60000) * 60000;
};

export function toUtcIso(dateKey, time, tz) {
  const [year, month, day] = dateKey.split("-").map(Number);
  const [hour, minute] = time.split(":").map(Number);
  const wallClock = Date.UTC(year, month - 1, day, hour, minute);
  const firstGuess = wallClock - offsetOf(wallClock, tz);
  return new Date(wallClock - offsetOf(firstGuess, tz)).toISOString();
}

export const shiftDays = (key, count) => format(addDays(parseISO(key), count), "yyyy-MM-dd");

export const mondayOf = (key) => format(startOfWeek(parseISO(key), { weekStartsOn: 1 }), "yyyy-MM-dd");

export const formatKey = (key, pattern) => format(parseISO(key), pattern);

export const hoursOf = (shift) => (new Date(shift.end) - new Date(shift.start)) / 36e5;

export const shiftLabel = (shift, tz) =>
  `${formatKey(dayKey(shift.start, tz), "EEE d MMM")}, ${timeOf(shift.start, tz)} to ${timeOf(shift.end, tz)}, ${shift.position}`;
