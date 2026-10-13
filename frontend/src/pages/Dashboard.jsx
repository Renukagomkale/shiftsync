import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../api";
import ShiftBlock from "../components/ShiftBlock.jsx";
import ShiftModal from "../components/ShiftModal.jsx";
import { ErrorBox, Loading } from "../components/States.jsx";
import { dayKey, formatKey } from "../lib/time";
import useFetch from "../lib/useFetch";
import { useSession } from "../session.jsx";

export default function Dashboard() {
  const { user } = useSession();
  const tz = user.business.timezone;
  const [assigning, setAssigning] = useState(null);

  const summary = useFetch(() => api.get("/dashboard/summary/").then((response) => response.data), []);
  const members = useFetch(() => api.get("/business/members/").then((response) => response.data), []);
  const data = summary.data;

  return (
    <section>
      <h1 className="font-display text-4xl font-bold">This week at a glance</h1>
      {summary.error && (
        <div className="mt-6">
          <ErrorBox error={summary.error} onRetry={summary.reload} />
        </div>
      )}
      {summary.loading && !data && <Loading />}
      {data && (
        <>
          <p className="mt-3 text-lg">
            {data.unassigned_shifts.length} shifts need cover.{" "}
            <Link to="/swaps" className="underline underline-offset-4">
              {data.pending_swaps} swaps waiting for your approval.
            </Link>
          </p>

          <div className="mt-10 grid gap-12 md:grid-cols-[1.4fr_1fr]">
            <div>
              <h2 className="font-display text-2xl font-bold">Needs cover</h2>
              <ul className="mt-4 divide-y divide-dashed divide-ink/40">
                {data.unassigned_shifts.map((shift) => (
                  <li key={shift.id} className="flex items-center gap-4 py-3">
                    <p className="w-24 font-display font-bold">{formatKey(dayKey(shift.start, tz), "EEE d MMM")}</p>
                    <div className="flex-1">
                      <ShiftBlock shift={shift} tz={tz} showWorker={false} />
                    </div>
                    <button onClick={() => setAssigning(shift)} className="pill">Assign</button>
                  </li>
                ))}
                {data.unassigned_shifts.length === 0 && <li className="py-3">Every shift this week has someone on it.</li>}
              </ul>
            </div>

            <div>
              <h2 className="font-display text-2xl font-bold">Hours per person</h2>
              <ul className="mt-4 space-y-4">
                {data.hours_per_worker.map((worker) => (
                  <li key={worker.worker_id}>
                    <div className="flex justify-between text-sm">
                      <span>{worker.name}</span>
                      <span className="font-mono">
                        {worker.hours} / {data.max_hours_per_week} h
                      </span>
                    </div>
                    <div className="mt-1 h-3 rounded-full bg-paper">
                      <div
                        className="h-3 rounded-full bg-ink"
                        style={{ width: `${Math.min(100, (worker.hours / data.max_hours_per_week) * 100)}%` }}
                      />
                    </div>
                  </li>
                ))}
                {data.hours_per_worker.length === 0 && <li>No team members have joined yet. Share your join code.</li>}
              </ul>
            </div>
          </div>
        </>
      )}

      {assigning && members.data && (
        <ShiftModal
          shift={assigning}
          tz={tz}
          members={members.data}
          onClose={() => setAssigning(null)}
          onSaved={() => {
            setAssigning(null);
            summary.reload();
          }}
        />
      )}
    </section>
  );
}
