import { useState } from "react";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import api from "../api";
import ShiftBlock from "../components/ShiftBlock.jsx";
import ShiftModal from "../components/ShiftModal.jsx";
import { ErrorBox, Loading } from "../components/States.jsx";
import { dayKey, formatKey, mondayOf, shiftDays, todayKey } from "../lib/time";
import { positionColor } from "../lib/positions";
import useFetch from "../lib/useFetch";
import { useSession } from "../session.jsx";

export default function Schedule() {
  const { user } = useSession();
  const tz = user.business.timezone;
  const [weekStart, setWeekStart] = useState(() => mondayOf(todayKey(tz)));
  const [modal, setModal] = useState(null);

  const shifts = useFetch(
    () =>
      api
        .get("/shifts/", { params: { from: weekStart, to: shiftDays(weekStart, 7), page_size: 500 } })
        .then((response) => response.data.results),
    [weekStart]
  );
  const members = useFetch(() => api.get("/business/members/").then((response) => response.data), []);

  const days = Array.from({ length: 7 }, (_, index) => shiftDays(weekStart, index));
  const byDay = {};
  (shifts.data ?? []).forEach((shift) => (byDay[dayKey(shift.start, tz)] ??= []).push(shift));
  const positions = [...new Set((shifts.data ?? []).map((shift) => shift.position))];
  const today = todayKey(tz);

  const saved = () => {
    setModal(null);
    shifts.reload();
  };

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl font-bold">Week of {formatKey(weekStart, "d MMM")}</h1>
          <div className="mt-3 flex flex-wrap gap-4 text-sm">
            {positions.map((name) => (
              <span key={name} className="flex items-center gap-2">
                <span className={`h-3 w-3 rounded-full ${positionColor(name)}`} />
                {name}
              </span>
            ))}
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full border border-dashed border-ink" />
              Needs cover
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <button aria-label="Previous week" onClick={() => setWeekStart(shiftDays(weekStart, -7))} className="pill px-3">
            <ChevronLeft size={16} />
          </button>
          <button aria-label="Next week" onClick={() => setWeekStart(shiftDays(weekStart, 7))} className="pill px-3">
            <ChevronRight size={16} />
          </button>
          <button onClick={() => setModal({ shift: null })} className="pill pill-solid flex items-center gap-1">
            <Plus size={16} /> New shift
          </button>
        </div>
      </div>

      {shifts.error && (
        <div className="mt-8">
          <ErrorBox error={shifts.error} onRetry={shifts.reload} />
        </div>
      )}
      {shifts.loading && !shifts.data && <Loading label="Loading the week" />}
      {shifts.data && (
        <>
          {shifts.data.length === 0 && (
            <p className="mt-6">No shifts this week yet. Use New shift to add the first one.</p>
          )}
          <div className="mt-8 overflow-x-auto rounded-3xl bg-paper p-4">
            <div className="grid min-w-[880px] grid-cols-7 gap-x-3">
              {days.map((day) => (
                <div key={day} className="border-l border-dashed border-ink/40 pl-3 first:border-l-0 first:pl-0">
                  <p className={`pb-2 font-display font-bold ${day === today ? "border-b-2 border-tangerine" : "border-b border-ink/20"}`}>
                    {formatKey(day, "EEE")} <span className="font-mono text-sm font-normal">{formatKey(day, "d")}</span>
                  </p>
                  <div className="mt-3 space-y-2">
                    {(byDay[day] ?? []).map((shift) => (
                      <button key={shift.id} onClick={() => setModal({ shift })} className="block w-full text-left">
                        <ShiftBlock shift={shift} tz={tz} />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {modal && members.data && (
        <ShiftModal
          shift={modal.shift}
          tz={tz}
          members={members.data}
          defaultDate={today >= weekStart && today < shiftDays(weekStart, 7) ? today : weekStart}
          onClose={() => setModal(null)}
          onSaved={saved}
        />
      )}
    </section>
  );
}
