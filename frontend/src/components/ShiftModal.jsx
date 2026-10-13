import { useState } from "react";
import api, { errorMessages } from "../api";
import { positionNames } from "../lib/positions";
import { dayKey, shiftDays, timeOf, toUtcIso } from "../lib/time";
import Modal from "./Modal.jsx";
import { ErrorList } from "./States.jsx";

const startingForm = (shift, tz, defaultDate) =>
  shift
    ? {
        position: shift.position,
        date: dayKey(shift.start, tz),
        start: timeOf(shift.start, tz),
        end: timeOf(shift.end, tz),
        assigned_to: shift.assigned_to ?? "",
        notes: shift.notes,
      }
    : { position: "", date: defaultDate, start: "09:00", end: "17:00", assigned_to: "", notes: "" };

export default function ShiftModal({ shift, tz, members, defaultDate, onClose, onSaved }) {
  const [form, setForm] = useState(() => startingForm(shift, tz, defaultDate));
  const [errors, setErrors] = useState([]);
  const [saving, setSaving] = useState(false);

  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value });

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setErrors([]);
    const endDate = form.end <= form.start ? shiftDays(form.date, 1) : form.date;
    const body = {
      position: form.position.trim(),
      start: toUtcIso(form.date, form.start, tz),
      end: toUtcIso(endDate, form.end, tz),
      assigned_to: form.assigned_to ? Number(form.assigned_to) : null,
      notes: form.notes,
    };
    try {
      await (shift ? api.patch(`/shifts/${shift.id}/`, body) : api.post("/shifts/", body));
      onSaved();
    } catch (error) {
      setErrors(errorMessages(error));
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!window.confirm("Delete this shift?")) return;
    try {
      await api.delete(`/shifts/${shift.id}/`);
      onSaved();
    } catch (error) {
      setErrors(errorMessages(error));
    }
  };

  const field = "mt-1 w-full rounded-xl border border-ink bg-white/60 px-3 py-2";

  return (
    <Modal title={shift ? "Edit shift" : "New shift"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4 text-sm">
        <label className="block">
          Position
          <input list="positions" required value={form.position} onChange={set("position")} className={field} />
          <datalist id="positions">
            {positionNames.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
        </label>
        <label className="block">
          Date
          <input type="date" required value={form.date} onChange={set("date")} className={field} />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            Starts
            <input type="time" required value={form.start} onChange={set("start")} className={field} />
          </label>
          <label className="block">
            Ends
            <input type="time" required value={form.end} onChange={set("end")} className={field} />
          </label>
        </div>
        <p className="-mt-2 text-xs opacity-70">If the end time is earlier than the start, the shift ends the next day.</p>
        <label className="block">
          Assigned to
          <select value={form.assigned_to} onChange={set("assigned_to")} className={field}>
            <option value="">Nobody yet</option>
            {members.map((member) => (
              <option key={member.id} value={member.id}>
                {member.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          Notes
          <input value={form.notes} maxLength={300} onChange={set("notes")} className={field} />
        </label>
        <ErrorList messages={errors} />
        <div className="flex flex-wrap items-center gap-3">
          <button disabled={saving} className="pill pill-solid">
            {saving ? "Saving" : "Save shift"}
          </button>
          <button type="button" onClick={onClose} className="pill">
            Cancel
          </button>
          {shift && (
            <button type="button" onClick={remove} className="ml-auto text-sm underline underline-offset-4">
              Delete shift
            </button>
          )}
        </div>
      </form>
    </Modal>
  );
}
