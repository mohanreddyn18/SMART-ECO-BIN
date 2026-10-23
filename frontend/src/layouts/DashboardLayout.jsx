import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import Header from '../components/layout/Header';

const PAGE_TITLES = {
  '/dashboard': { title: 'Dashboard', subtitle: 'Overview of your waste management activity' },
  '/detect': { title: 'Waste Detection', subtitle: 'Upload and classify waste images using AI' },
  '/history': { title: 'Classification History', subtitle: 'View your past waste classifications' },
  '/analytics': { title: 'Waste Analytics', subtitle: 'Charts and insights about waste patterns' },
  '/sanitation': { title: 'Data-driven Sanitation Intelligence', subtitle: 'Software-based sanitation status analysis' },
  '/anomalies': { title: 'Anomaly Detection', subtitle: 'Detect unusual patterns in waste data' },
  '/predictions': { title: 'Predictive Insights', subtitle: 'Forecast waste trends from historical data' },
  '/wasteai': { title: 'WasteAI', subtitle: 'AI assistant for waste management questions' },
  '/profile': { title: 'Profile', subtitle: 'Manage your account information' },
  '/settings': { title: 'Settings', subtitle: 'Application preferences and configuration' },
  // Admin pages
  '/admin/dashboard': { title: 'Admin Dashboard', subtitle: 'System overview and statistics' },
  '/admin/users': { title: 'Users', subtitle: 'Manage system users' },
  '/admin/records': { title: 'Waste Records', subtitle: 'All classification records' },
  '/admin/analytics': { title: 'Waste Analytics', subtitle: 'System-wide analytics and charts' },
  '/admin/sanitation': { title: 'Data-driven Sanitation Intelligence', subtitle: 'System-wide sanitation analysis' },
  '/admin/anomalies': { title: 'Anomaly Detection', subtitle: 'System-wide anomaly analysis' },
  '/admin/predictions': { title: 'Predictive Insights', subtitle: 'System-wide predictive analytics' },
  '/admin/sanitationai': { title: 'SanitationAI', subtitle: 'AI assistant for sanitation management' },
  '/admin/settings': { title: 'Settings', subtitle: 'System configuration' },
};

export default function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const pageInfo = PAGE_TITLES[location.pathname] || { title: 'EcoSort AI', subtitle: '' };

  const handleToggle = () => {
    if (window.innerWidth <= 768) {
      setMobileOpen(!mobileOpen);
    } else {
      setCollapsed(!collapsed);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />
      <div className={`main-area ${collapsed ? 'sidebar-collapsed' : ''}`}>
        <Header
          title={pageInfo.title}
          subtitle={pageInfo.subtitle}
          collapsed={collapsed}
          onToggle={handleToggle}
        />
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
