import { useState } from "react";
import api, { errorMessages } from "../api";
import { shiftLabel } from "../lib/time";
import Modal from "./Modal.jsx";
import { ErrorList } from "./States.jsx";

export default function SwapModal({ shift, tz, members, currentUserId, onClose, onSaved }) {
  const [target, setTarget] = useState("");
  const [errors, setErrors] = useState([]);
  const [saving, setSaving] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setErrors([]);
    try {
      await api.post("/swaps/", { shift: shift.id, target_worker: target ? Number(target) : null });
      onSaved();
    } catch (error) {
      setErrors(errorMessages(error));
      setSaving(false);
    }
  };

  return (
    <Modal title="Request a swap" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4 text-sm">
        <p className="font-medium">{shiftLabel(shift, tz)}</p>
        <label className="block">
          Who should take it?
          <select
            value={target}
            onChange={(event) => setTarget(event.target.value)}
            className="mt-1 w-full rounded-xl border border-ink bg-white/60 px-3 py-2"
          >
            <option value="">Anyone available</option>
            {members
              .filter((member) => member.id !== currentUserId && member.role === "worker")
              .map((member) => (
                <option key={member.id} value={member.id}>
                  {member.name}
                </option>
              ))}
          </select>
        </label>
        <ErrorList messages={errors} />
        <div className="flex gap-3">
          <button disabled={saving} className="pill pill-solid">
            {saving ? "Sending" : "Send request"}
          </button>
          <button type="button" onClick={onClose} className="pill">
            Cancel
          </button>
        </div>
      </form>
    </Modal>
  );
}
