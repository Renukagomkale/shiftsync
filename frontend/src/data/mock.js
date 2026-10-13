import { addDays, format } from "date-fns";

export const positions = {
  Barista: "bg-tangerine",
  Cashier: "bg-mint",
  Baker: "bg-butter",
  Floor: "bg-rose",
};

export const workers = [
  { id: 1, name: "Maya Joshi" },
  { id: 2, name: "Arjun Rao" },
  { id: 3, name: "Sana Khan" },
  { id: 4, name: "Dev Patil" },
];

export const maxHoursPerWeek = 30;

const pattern = [
  [0, "Baker", "06:00", "12:00", 2],
  [0, "Barista", "08:00", "14:00", 1],
  [0, "Cashier", "12:00", "18:00", 3],
  [1, "Barista", "08:00", "14:00", null],
  [1, "Floor", "12:00", "20:00", 4],
  [1, "Cashier", "14:00", "20:00", 3],
  [2, "Baker", "06:00", "12:00", 2],
  [2, "Barista", "12:00", "18:00", 1],
  [3, "Barista", "08:00", "14:00", 1],
  [3, "Cashier", "08:00", "14:00", null],
  [3, "Floor", "14:00", "20:00", 4],
  [4, "Baker", "06:00", "12:00", 2],
  [4, "Barista", "12:00", "20:00", 1],
  [4, "Cashier", "12:00", "20:00", 3],
  [5, "Barista", "09:00", "15:00", 4],
  [5, "Floor", "09:00", "17:00", null],
  [6, "Barista", "09:00", "15:00", 1],
];

export function buildWeek(weekStart) {
  return Array.from({ length: 7 }, (_, offset) => {
    const date = addDays(weekStart, offset);
    const key = format(date, "yyyy-MM-dd");
    const shifts = pattern
      .filter((row) => row[0] === offset)
      .map((row, i) => ({
        id: `${key}-${i}`,
        date,
        position: row[1],
        start: row[2],
        end: row[3],
        workerId: row[4],
      }));
    return { date, shifts };
  });
}

export const shiftHours = (shift) => Number(shift.end.slice(0, 2)) - Number(shift.start.slice(0, 2));

export const workerName = (id) => workers.find((w) => w.id === id)?.name ?? "Open";

export const initialSwaps = [
  { id: 1, shift: "Wed 06:00 to 12:00, Baker", from: 2, to: 1, status: "pending_peer" },
  { id: 2, shift: "Thu 14:00 to 20:00, Floor", from: 4, to: 3, status: "pending_manager" },
  { id: 3, shift: "Fri 12:00 to 18:00, Cashier", from: 3, to: null, status: "pending_peer" },
  { id: 4, shift: "Sat 09:00 to 15:00, Barista", from: 1, to: 4, status: "approved" },
  { id: 5, shift: "Tue 12:00 to 20:00, Floor", from: 4, to: 2, status: "rejected" },
];
