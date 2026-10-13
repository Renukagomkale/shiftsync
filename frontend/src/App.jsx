import { Navigate, Route, Routes } from "react-router-dom";
import { useSession } from "./session.jsx";
import Layout from "./components/Layout.jsx";
import { Loading } from "./components/States.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Setup from "./pages/Setup.jsx";
import Schedule from "./pages/Schedule.jsx";
import MyShifts from "./pages/MyShifts.jsx";
import Swaps from "./pages/Swaps.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Settings from "./pages/Settings.jsx";

const homeFor = (user) => (user.role === "manager" ? "/schedule" : "/my-shifts");

function Guard({ role, children }) {
  const { user, loading } = useSession();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.business) return <Navigate to="/setup" replace />;
  if (role && user.role !== role) return <Navigate to={homeFor(user)} replace />;
  return children;
}

function Home() {
  const { user } = useSession();
  return <Navigate to={user.business ? homeFor(user) : "/setup"} replace />;
}

export default function App() {
  const { user, loading } = useSession();
  if (loading) return <Loading />;

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={user ? <Navigate to="/app" replace /> : <Login />} />
      <Route path="/setup" element={user ? <Setup /> : <Navigate to="/login" replace />} />
      <Route path="/app" element={user ? <Home /> : <Navigate to="/login" replace />} />
      <Route element={<Layout />}>
        <Route path="/schedule" element={<Guard role="manager"><Schedule /></Guard>} />
        <Route path="/dashboard" element={<Guard role="manager"><Dashboard /></Guard>} />
        <Route path="/settings" element={<Guard role="manager"><Settings /></Guard>} />
        <Route path="/my-shifts" element={<Guard role="worker"><MyShifts /></Guard>} />
        <Route path="/swaps" element={<Guard><Swaps /></Guard>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
