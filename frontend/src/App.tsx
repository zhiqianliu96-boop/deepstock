import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/SettingsPage';

function NavBar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-2 text-sm transition-colors ${
      isActive ? 'text-accent-cyan border-b-2 border-accent-cyan' : 'text-text-muted hover:text-text-secondary'
    }`;

  return (
    <nav className="border-b border-border bg-bg-secondary/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-12">
        <div className="flex items-center gap-1">
          <NavLink to="/" className="text-text-primary font-bold text-sm mr-6">
            Deep<span className="text-accent-cyan">Stock</span>
          </NavLink>
          <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
          <NavLink to="/history" className={linkClass}>History</NavLink>
          <NavLink to="/settings" className={linkClass}>Settings</NavLink>
        </div>
        <div className="text-text-muted text-xs">
          v1.0
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-bg-primary">
        <NavBar />
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
