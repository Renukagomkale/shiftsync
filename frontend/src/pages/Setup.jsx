import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { errorMessages } from "../api";
import { ErrorList } from "../components/States.jsx";
import { useSession } from "../session.jsx";

const zones = Intl.supportedValuesOf("timeZone");
const browserZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

export default function Setup() {
  const { user, refreshUser, logout } = useSession();
  const navigate = useNavigate();
  const isManager = user.role === "manager";
  const [name, setName] = useState("");
  const [timezone, setTimezone] = useState(zones.includes(browserZone) ? browserZone : "UTC");
  const [code, setCode] = useState("");
  const [errors, setErrors] = useState([]);
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setErrors([]);
    try {
      if (isManager) await api.post("/business/", { name, timezone });
      else await api.post("/business/join/", { join_code: code });
      await refreshUser();
      navigate("/app");
    } catch (error) {
      setErrors(errorMessages(error));
      setBusy(false);
    }
  };

  const field = "mt-1 w-full rounded-xl border border-ink bg-paper px-4 py-2.5";

  return (
    <main className="mx-auto grid min-h-screen max-w-xl content-center px-5">
      <form onSubmit={submit} className="space-y-4">
        <h1 className="font-display text-4xl font-bold">{isManager ? "Name your business" : "Join your team"}</h1>
        <p>
          {isManager
            ? "You will get a join code to share with your team once this is saved."
            : "Ask your manager for the 8 character join code."}
        </p>
        {isManager ? (
          <>
            <label className="block text-sm">
              Business name
              <input required value={name} onChange={(event) => setName(event.target.value)} className={field} />
            </label>
            <label className="block text-sm">
              Timezone
              <select value={timezone} onChange={(event) => setTimezone(event.target.value)} className={field}>
                {zones.map((zone) => (
                  <option key={zone}>{zone}</option>
                ))}
              </select>
            </label>
          </>
        ) : (
          <label className="block text-sm">
            Join code
            <input
              required
              maxLength={8}
              value={code}
              onChange={(event) => setCode(event.target.value.toUpperCase())}
              className={`${field} font-mono tracking-widest`}
            />
          </label>
        )}
        <ErrorList messages={errors} />
        <div className="flex items-center gap-4">
          <button disabled={busy} className="pill pill-solid">
            {busy ? "One moment" : isManager ? "Create business" : "Join team"}
          </button>
          <button type="button" onClick={logout} className="text-sm underline underline-offset-4">
            Log out
          </button>
        </div>
      </form>
    </main>
  );
}
