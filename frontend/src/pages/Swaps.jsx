import { useEffect, useState } from "react";
import { Ban, Check, Clock, Hourglass, X } from "lucide-react";
import api, { errorMessages } from "../api";
import { ErrorBox, ErrorList, Loading } from "../components/States.jsx";
import { shiftLabel } from "../lib/time";
import { useSession } from "../session.jsx";

const statusInfo = {
  pending_peer: { label: "Waiting for coworker", Icon: Clock },
  pending_manager: { label: "Waiting for manager", Icon: Hourglass },
  approved: { label: "Approved", Icon: Check },
  rejected: { label: "Declined", Icon: X },
  cancelled: { label: "Cancelled", Icon: Ban },
};

export default function Swaps() {
  const { user } = useSession();
  const tz = user.business.timezone;
  const [state, setState] = useState({ items: [], next: null, loading: true, error: null });
  const [busyId, setBusyId] = useState(null);
  const [actionErrors, setActionErrors] = useState([]);

  const load = async (url, append) => {
    try {
      const { data } = await api.get(url);
      setState((current) => ({
        items: append ? [...current.items, ...data.results] : data.results,
        next: data.next,
        loading: false,
        error: null,
      }));
    } catch (error) {
      setState((current) => ({ ...current, loading: false, error }));
    }
  };

  useEffect(() => {
    load("/swaps/", false);
  }, []);

  const act = async (swap, action) => {
    setBusyId(swap.id);
    setActionErrors([]);
    try {
      await api.patch(`/swaps/${swap.id}/`, { action });
      await load("/swaps/", false);
    } catch (error) {
      setActionErrors(errorMessages(error));
    } finally {
      setBusyId(null);
    }
  };

  const options = (swap) => {
    const mine = swap.requested_by === user.id;
    const list = [];
    if (user.role === "manager" && swap.status === "pending_manager") {
      list.push(["approve", "Approve", true], ["reject", "Reject", false]);
    }
    if (!mine && swap.status === "pending_peer" && (swap.target_worker === null || swap.target_worker === user.id)) {
      list.push(["accept", "Accept swap", true]);
      if (swap.target_worker === user.id) list.push(["decline", "Decline", false]);
    }
    if (mine && ["pending_peer", "pending_manager"].includes(swap.status)) list.push(["cancel", "Cancel request", false]);
    return list;
  };

  return (
    <section className="max-w-3xl">
      <h1 className="font-display text-4xl font-bold">Swap requests</h1>
      <p className="mt-3">A coworker accepts first, then the manager approves. The shift only moves after both.</p>

      <div className="mt-6">
        <ErrorList messages={actionErrors} />
      </div>
      {state.error && <ErrorBox error={state.error} onRetry={() => load("/swaps/", false)} />}
      {state.loading && <Loading />}
      {!state.loading && !state.error && (
        <ul className="mt-4 divide-y divide-dashed divide-ink/40">
          {state.items.map((swap) => {
            const { label, Icon } = statusInfo[swap.status];
            return (
              <li key={swap.id} className="flex flex-wrap items-center justify-between gap-4 py-5">
                <div>
                  <p className="font-display text-xl font-bold">{shiftLabel(swap.shift, tz)}</p>
                  <p className="text-sm">
                    {swap.requested_by_name} to {swap.target_worker_name ?? "anyone available"}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="flex items-center gap-1.5 rounded-full bg-paper px-3 py-1 text-sm">
                    <Icon size={14} /> {label}
                  </span>
                  {options(swap).map(([action, text, primary]) => (
                    <button
                      key={action}
                      disabled={busyId === swap.id}
                      onClick={() => act(swap, action)}
                      className={`pill ${primary ? "pill-solid" : ""}`}
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </li>
            );
          })}
          {state.items.length === 0 && (
            <li className="py-6">No swap requests yet. Workers can ask for one from their My shifts page.</li>
          )}
        </ul>
      )}
      {state.next && (
        <button onClick={() => load(state.next, true)} className="pill mt-6">
          Show older requests
        </button>
      )}
    </section>
  );
}
