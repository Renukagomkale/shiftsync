import { useState } from "react";
import api, { errorMessages } from "../api";
import { ErrorList } from "../components/States.jsx";
import { useSession } from "../session.jsx";

export default function Settings() {
  const { user, refreshUser } = useSession();
  const business = user.business;
  const [form, setForm] = useState({
    name: business.name,
    max_hours_per_week: business.max_hours_per_week,
    min_rest_hours: business.min_rest_hours,
  });
  const [errors, setErrors] = useState([]);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  const set = (key) => (event) => {
    setForm({ ...form, [key]: event.target.value });
    setSaved(false);
  };

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setErrors([]);
    try {
      await api.patch("/business/", {
        name: form.name.trim(),
        max_hours_per_week: Number(form.max_hours_per_week),
        min_rest_hours: Number(form.min_rest_hours),
      });
      await refreshUser();
      setSaved(true);
    } catch (error) {
      setErrors(errorMessages(error));
    } finally {
      setBusy(false);
    }
  };

  const copyCode = async () => {
    await navigator.clipboard.writeText(business.join_code);
    setCopied(true);
  };

  const field = "mt-1 w-full rounded-xl border border-ink bg-paper px-4 py-2.5";

  return (
    <section className="grid gap-12 md:grid-cols-[1.3fr_1fr]">
      <form onSubmit={submit} className="max-w-md space-y-4">
        <h1 className="font-display text-4xl font-bold">Scheduling rules</h1>
        <p>These limits apply every time someone is assigned a shift or a swap is approved.</p>
        <label className="block text-sm">
          Business name
          <input required value={form.name} onChange={set("name")} className={field} />
        </label>
        <label className="block text-sm">
          Maximum hours per person per week
          <input type="number" min="1" max="168" required value={form.max_hours_per_week} onChange={set("max_hours_per_week")} className={field} />
        </label>
        <label className="block text-sm">
          Minimum rest between shifts (hours)
          <input type="number" min="0" max="24" required value={form.min_rest_hours} onChange={set("min_rest_hours")} className={field} />
        </label>
        <p className="text-xs opacity-70">Set rest to 0 if you allow back-to-back shifts.</p>
        <ErrorList messages={errors} />
        {saved && <p className="rounded-xl bg-mint px-4 py-2 text-sm">Saved.</p>}
        <button disabled={busy} className="pill pill-solid">
          {busy ? "Saving" : "Save rules"}
        </button>
      </form>

      <div>
        <h2 className="font-display text-2xl font-bold">Invite your team</h2>
        <p className="mt-3 text-sm">Share this code. Team members enter it after they create an account.</p>
        <p className="mt-4 font-mono text-3xl tracking-widest">{business.join_code}</p>
        <button onClick={copyCode} className="pill mt-4">
          {copied ? "Copied" : "Copy code"}
        </button>
        <p className="mt-8 text-sm opacity-70">Timezone: {business.timezone}</p>
      </div>
    </section>
  );
}
