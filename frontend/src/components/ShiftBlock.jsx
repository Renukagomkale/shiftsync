import { positionColor } from "../lib/positions";
import { timeOf } from "../lib/time";

export default function ShiftBlock({ shift, tz, showWorker = true }) {
  const open = shift.assigned_to === null;
  const color = open ? "border border-dashed border-ink" : positionColor(shift.position);
  return (
    <div className={`rounded-xl px-3 py-2 text-sm ${color}`}>
      <p className="font-mono text-xs">
        {timeOf(shift.start, tz)} to {timeOf(shift.end, tz)}
      </p>
      <p className="font-medium">{shift.position}</p>
      {showWorker && <p className="text-xs opacity-80">{open ? "Needs cover" : shift.assigned_to_name}</p>}
    </div>
  );
}
