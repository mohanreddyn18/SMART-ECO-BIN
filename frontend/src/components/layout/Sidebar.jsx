import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  HiOutlineHome,
  HiOutlineCamera,
  HiOutlineClock,
  HiOutlineChartBar,
  HiOutlineShieldCheck,
  HiOutlineExclamationTriangle,
  HiOutlineLightBulb,
  HiOutlineChatBubbleLeftRight,
  HiOutlineUser,
  HiOutlineCog6Tooth,
  HiOutlineArrowRightOnRectangle,
  HiOutlineUsers,
  HiOutlineDocumentText,
  HiOutlineCpuChip
} from 'react-icons/hi2';

const userNavItems = [
  { section: 'Main', items: [
    { to: '/dashboard', icon: HiOutlineHome, label: 'Dashboard' },
    { to: '/detect', icon: HiOutlineCamera, label: 'Waste Detection' },
    { to: '/history', icon: HiOutlineClock, label: 'Classification History' },
    { to: '/analytics', icon: HiOutlineChartBar, label: 'Waste Analytics' },
  ]},
  { section: 'Intelligence', items: [
    { to: '/sanitation', icon: HiOutlineShieldCheck, label: 'Sanitation Intelligence' },
    { to: '/anomalies', icon: HiOutlineExclamationTriangle, label: 'Anomaly Detection' },
    { to: '/predictions', icon: HiOutlineLightBulb, label: 'Predictive Insights' },
  ]},
  { section: 'AI Assistant', items: [
    { to: '/wasteai', icon: HiOutlineChatBubbleLeftRight, label: 'WasteAI' },
  ]},
  { section: 'Account', items: [
    { to: '/profile', icon: HiOutlineUser, label: 'Profile' },
    { to: '/settings', icon: HiOutlineCog6Tooth, label: 'Settings' },
  ]}
];

const adminNavItems = [
  { section: 'Overview', items: [
    { to: '/admin/dashboard', icon: HiOutlineHome, label: 'Dashboard' },
    { to: '/admin/users', icon: HiOutlineUsers, label: 'Users' },
    { to: '/admin/records', icon: HiOutlineDocumentText, label: 'Waste Records' },
    { to: '/admin/analytics', icon: HiOutlineChartBar, label: 'Waste Analytics' },
  ]},
  { section: 'Intelligence', items: [
    { to: '/admin/sanitation', icon: HiOutlineShieldCheck, label: 'Sanitation Intelligence' },
    { to: '/admin/anomalies', icon: HiOutlineExclamationTriangle, label: 'Anomaly Detection' },
    { to: '/admin/predictions', icon: HiOutlineLightBulb, label: 'Predictive Insights' },
  ]},
  { section: 'AI', items: [
    { to: '/admin/sanitationai', icon: HiOutlineCpuChip, label: 'SanitationAI' },
  ]},
  { section: 'System', items: [
    { to: '/admin/settings', icon: HiOutlineCog6Tooth, label: 'Settings' },
  ]}
];

export default function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const { isAdmin, logout } = useAuth();
  const location = useLocation();
  const navItems = isAdmin ? adminNavItems : userNavItems;

  return (
    <>
      {mobileOpen && (
        <div className="sidebar-overlay show" onClick={onMobileClose} />
      )}
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">E</div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-name">EcoSort AI</span>
            <span className="sidebar-brand-tagline">
              {isAdmin ? 'Admin Panel' : 'Smart Waste'}
            </span>
          </div>
        </div>

        {navItems.map((section) => (
          <div className="sidebar-section" key={section.section}>
            <div className="sidebar-section-title">{section.section}</div>
            <nav className="sidebar-nav">
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `sidebar-link ${isActive ? 'active' : ''}`
                  }
                  onClick={onMobileClose}
                >
                  <span className="sidebar-link-icon">
                    <item.icon />
                  </span>
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </nav>
          </div>
        ))}

        <div className="sidebar-footer">
          <button className="sidebar-link" onClick={logout} style={{ width: '100%' }}>
            <span className="sidebar-link-icon">
              <HiOutlineArrowRightOnRectangle />
            </span>
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
