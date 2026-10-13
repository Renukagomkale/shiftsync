import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Blob from "../components/Blob.jsx";
import { ErrorList } from "../components/States.jsx";
import { errorMessages } from "../api";
import { useSession } from "../session.jsx";

export default function Login() {
  const { login, register } = useSession();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [mode, setMode] = useState(params.get("mode") === "register" ? "register" : "login");
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: params.get("role") === "worker" ? "worker" : "manager",
  });
  const [errors, setErrors] = useState([]);
  const [busy, setBusy] = useState(false);

  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  const registering = mode === "register";

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setErrors([]);
    try {
      await (registering ? register(form) : login(form.email, form.password));
      navigate("/app");
    } catch (error) {
      setErrors(errorMessages(error));
      setBusy(false);
    }
  };

  const field = "mt-1 w-full rounded-xl border border-ink bg-paper px-4 py-2.5";

  return (
    <main className="relative mx-auto grid min-h-screen max-w-5xl items-center gap-8 overflow-hidden px-5 md:grid-cols-[1fr_1.2fr]">
      <Blob className="absolute -left-40 top-1/2 hidden h-[900px] -translate-y-1/2 md:block" />
      <div className="relative z-10 hidden pl-10 text-paper md:block">
        <Link to="/" className="font-display text-2xl font-bold">ShiftSync</Link>
        <p className="mt-6 max-w-[14rem] text-sm opacity-90">One calendar for the whole team. Everyone sees the same week.</p>
      </div>

      <form onSubmit={submit} className="relative z-10 space-y-4 py-16">
        <h1 className="font-display text-4xl font-bold">{registering ? "Create your account" : "Welcome back"}</h1>
        {registering && (
          <>
            <label className="block text-sm">
              Your name
              <input required value={form.name} onChange={set("name")} className={field} />
            </label>
            <fieldset className="flex gap-3 text-sm">
              <legend className="mb-1">I am a</legend>
              {[
                ["manager", "Manager"],
                ["worker", "Team member"],
              ].map(([value, label]) => (
                <label key={value} className={`pill cursor-pointer ${form.role === value ? "pill-solid" : ""}`}>
                  <input
                    type="radio"
                    name="role"
                    value={value}
                    checked={form.role === value}
                    onChange={set("role")}
                    className="sr-only"
                  />
                  {label}
                </label>
              ))}
            </fieldset>
          </>
        )}
        <label className="block text-sm">
          Email
          <input type="email" required value={form.email} onChange={set("email")} className={field} />
        </label>
        <label className="block text-sm">
          Password
          <input type="password" required value={form.password} onChange={set("password")} className={field} />
        </label>
        <ErrorList messages={errors} />
        <div className="flex flex-wrap items-center gap-4">
          <button disabled={busy} className="pill pill-solid">
            {busy ? "One moment" : registering ? "Create account" : "Log in"}
          </button>
          <button type="button" onClick={() => setMode(registering ? "login" : "register")} className="text-sm underline underline-offset-4">
            {registering ? "I already have an account" : "Create an account"}
          </button>
        </div>
      </form>
    </main>
  );
}
