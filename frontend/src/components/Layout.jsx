import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useSession } from "../session.jsx";
import NotificationBell from "./NotificationBell.jsx";

const links = {
  manager: [
    ["/schedule", "Schedule"],
    ["/swaps", "Swaps"],
    ["/dashboard", "Dashboard"],
    ["/settings", "Settings"],
  ],
  worker: [
    ["/my-shifts", "My shifts"],
    ["/swaps", "Swaps"],
  ],
};

export default function Layout() {
  const { user, logout } = useSession();
  const navigate = useNavigate();

  if (!user) return <Outlet />;

  const leave = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="mx-auto max-w-6xl px-5 pb-16">
      <header className="flex flex-wrap items-center justify-between gap-4 py-6">
        <div className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-ink font-display text-lg text-tangerine">S</span>
          <div className="leading-tight">
            <p className="font-display text-lg font-bold">ShiftSync</p>
            <p className="text-xs opacity-70">
              {user.business?.name}
              {user.role === "manager" && user.business ? `, join code ${user.business.join_code}` : ""}
            </p>
          </div>
        </div>
        <nav className="flex flex-wrap items-center gap-2">
          {links[user.role].map(([to, label]) => (
            <NavLink key={to} to={to} className={({ isActive }) => `pill ${isActive ? "pill-solid" : ""}`}>
              {label}
            </NavLink>
          ))}
          <NotificationBell />
          <button onClick={leave} className="pill border-dashed">
            {user.name}: Log out
          </button>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
