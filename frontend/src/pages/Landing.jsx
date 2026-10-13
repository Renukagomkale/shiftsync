import { Link } from "react-router-dom";
import Blob from "../components/Blob.jsx";
import { useSession } from "../session.jsx";

const preview = [
  ["06:00 to 12:00", "Baker", "Arjun", "bg-butter"],
  ["08:00 to 14:00", "Barista", "Maya", "bg-tangerine"],
  ["12:00 to 18:00", "Cashier", "Needs cover", "border border-dashed border-ink"],
];

export default function Landing() {
  const { user } = useSession();

  return (
    <main className="relative mx-auto min-h-screen max-w-6xl overflow-hidden px-5">
      <header className="flex items-center justify-between py-6">
        <p className="font-display text-xl font-bold">ShiftSync</p>
        <div className="flex gap-2">
          {user ? (
            <Link to="/app" className="pill pill-solid">Open the app</Link>
          ) : (
            <>
              <Link to="/login" className="pill">Log in</Link>
              <Link to="/login?mode=register&role=manager" className="pill pill-solid">Create a business</Link>
            </>
          )}
        </div>
      </header>

      <section className="grid items-center gap-10 pt-10 md:grid-cols-[1.1fr_1fr] md:pt-20">
        <div className="relative z-10 max-w-lg">
          <h1 className="font-display text-5xl font-bold leading-[1.05] md:text-7xl">Who is working Thursday?</h1>
          <p className="mt-6 max-w-md text-lg">
            Plan the week, hand out shifts and let your team swap among themselves. No more scrolling through the group chat to find out who said yes.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/login?mode=register&role=manager" className="pill pill-solid">Set up my team</Link>
            <Link to="/login?mode=register&role=worker" className="pill">I have a join code</Link>
          </div>
          <p className="mt-10 max-w-sm text-sm opacity-80">
            Built for cafes, shops and clinics with 5 to 30 part-time staff.
          </p>
        </div>

        <div className="relative h-[520px] md:h-[640px]">
          <Blob className="absolute -right-10 top-0 h-full w-full md:-right-24" />
          <div className="absolute left-4 top-24 w-56 rotate-[-3deg] space-y-2 rounded-2xl bg-paper p-4 shadow-xl md:left-0 md:top-32">
            <p className="font-display text-sm font-bold">Monday</p>
            {preview.map(([time, position, who, color]) => (
              <div key={position} className={`rounded-xl px-3 py-2 text-sm ${color}`}>
                <p className="font-mono text-xs">{time}</p>
                <p className="font-medium">{position}</p>
                <p className="text-xs opacity-80">{who}</p>
              </div>
            ))}
          </div>
          <div className="absolute bottom-16 right-6 w-52 rotate-2 rounded-2xl bg-butter p-4 text-sm shadow-xl">
            <p className="font-medium">Arjun wants to swap Wednesday</p>
            <p className="mt-1 text-xs">Waiting for Maya to accept</p>
          </div>
        </div>
      </section>
    </main>
  );
}
