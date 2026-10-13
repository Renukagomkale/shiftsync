import { useState } from "react";
import { Repeat } from "lucide-react";
import api from "../api";
import ShiftBlock from "../components/ShiftBlock.jsx";
import { ErrorBox, Loading } from "../components/States.jsx";
import SwapModal from "../components/SwapModal.jsx";
import { dayKey, formatKey, hoursOf, mondayOf, shiftDays, todayKey } from "../lib/time";
import useFetch from "../lib/useFetch";
import { useSession } from "../session.jsx";

export default function MyShifts() {
  const { user } = useSession();
  const tz = user.business.timezone;
  const weekStart = mondayOf(todayKey(tz));
  const weekEnd = shiftDays(weekStart, 7);
  const [swapping, setSwapping] = useState(null);
  const [sent, setSent] = useState(false);

  const shifts = useFetch(
    () => api.get("/shifts/mine/", { params: { from: weekStart, page_size: 200 } }).then((response) => response.data.results),
    [weekStart]
  );
  const members = useFetch(() => api.get("/business/members/").then((response) => response.data), []);

  const thisWeek = (shifts.data ?? []).filter((shift) => dayKey(shift.start, tz) < weekEnd);
  const total = thisWeek.reduce((sum, shift) => sum + hoursOf(shift), 0);

  return (
    <section className="grid gap-10 md:grid-cols-[1fr_2fr]">
      <div>
        <h1 className="font-display text-4xl font-bold">Hi {user.name.split(" ")[0]}</h1>
        {shifts.data && (
          <p className="mt-4 text-lg">
            You work <span className="font-mono font-medium">{total} hours</span> across {thisWeek.length} shifts this week.
          </p>
        )}
        {sent && <p className="mt-4 rounded-xl bg-mint px-4 py-2 text-sm">Swap request sent. You will get a notification when someone answers.</p>}
      </div>

      <div>
        {shifts.error && <ErrorBox error={shifts.error} onRetry={shifts.reload} />}
        {shifts.loading && !shifts.data && <Loading />}
        {shifts.data && (
          <ul className="divide-y divide-dashed divide-ink/40">
            {shifts.data.map((shift) => (
              <li key={shift.id} className="flex items-center gap-5 py-4">
                <div className="w-20 shrink-0">
                  <p className="font-display text-2xl font-bold">{formatKey(dayKey(shift.start, tz), "EEE")}</p>
                  <p className="font-mono text-sm">{formatKey(dayKey(shift.start, tz), "d MMM")}</p>
                </div>
                <div className="flex-1">
                  <ShiftBlock shift={shift} tz={tz} showWorker={false} />
                  {shift.notes && <p className="mt-1 text-xs opacity-70">{shift.notes}</p>}
                </div>
                {new Date(shift.start) > new Date() && (
                  <button onClick={() => setSwapping(shift)} className="pill flex items-center gap-1">
                    <Repeat size={14} /> Request swap
                  </button>
                )}
              </li>
            ))}
            {shifts.data.length === 0 && (
              <li className="py-6">No shifts yet. They will appear here once your manager assigns them to you.</li>
            )}
          </ul>
        )}
      </div>

      {swapping && members.data && (
        <SwapModal
          shift={swapping}
          tz={tz}
          members={members.data}
          currentUserId={user.id}
          onClose={() => setSwapping(null)}
          onSaved={() => {
            setSwapping(null);
            setSent(true);
          }}
        />
      )}
    </section>
  );
}
