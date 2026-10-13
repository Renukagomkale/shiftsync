import { formatDistanceToNow } from "date-fns";
import { Bell } from "lucide-react";
import { useEffect, useState } from "react";
import api from "../api";

export default function NotificationBell() {
  const [count, setCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);

  useEffect(() => {
    const load = () =>
      api
        .get("/notifications/unread-count/")
        .then((response) => setCount(response.data.count))
        .catch(() => {});
    load();
    const timer = setInterval(load, 30000);
    return () => clearInterval(timer);
  }, []);

  const toggle = async () => {
    setOpen(!open);
    if (!open) {
      const { data } = await api.get("/notifications/");
      setItems(data.results);
    }
  };

  const readAll = async () => {
    await api.post("/notifications/read-all/");
    setCount(0);
    setItems(items.map((item) => ({ ...item, is_read: true })));
  };

  return (
    <div className="relative">
      <button onClick={toggle} aria-label={`Notifications, ${count} unread`} className="pill relative px-3">
        <Bell size={16} />
        {count > 0 && (
          <span className="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-tangerine px-1 text-xs font-medium">
            {count}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-10 mt-2 w-80 max-w-[85vw] rounded-2xl border border-ink bg-paper p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <p className="font-display font-bold">Notifications</p>
            <button onClick={readAll} className="text-xs underline underline-offset-4">
              Mark all read
            </button>
          </div>
          <ul className="mt-3 max-h-80 divide-y divide-dashed divide-ink/40 overflow-y-auto">
            {items.map((item) => (
              <li key={item.id} className="py-2 text-sm">
                <p className={item.is_read ? "opacity-70" : "font-medium"}>{item.message}</p>
                <p className="text-xs opacity-60">{formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}</p>
              </li>
            ))}
            {items.length === 0 && <li className="py-3 text-sm">Nothing yet. Swap updates will show up here.</li>}
          </ul>
        </div>
      )}
    </div>
  );
}
