import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  HiOutlineBars3,
  HiOutlineBell,
  HiOutlineUser,
  HiOutlineCog6Tooth,
  HiOutlineArrowRightOnRectangle
} from 'react-icons/hi2';

export default function Header({ title, subtitle, collapsed, onToggle }) {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const initials = user?.name
    ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  return (
    <header className={`header ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="header-left">
        <button className="header-toggle" onClick={onToggle}>
          <HiOutlineBars3 />
        </button>
        <div>
          <div className="header-title">{title || 'Dashboard'}</div>
          {subtitle && <div className="header-subtitle">{subtitle}</div>}
        </div>
      </div>
      <div className="header-right">
        <button className="header-icon-btn">
          <HiOutlineBell />
          <span className="header-badge" />
        </button>
        <div style={{ position: 'relative' }} ref={dropdownRef}>
          <div
            className="header-user-info"
            onClick={() => setShowDropdown(!showDropdown)}
          >
            <div className="header-avatar">{initials}</div>
            <div>
              <div className="header-user-name">{user?.name || 'User'}</div>
              <div className="header-user-role">
                {isAdmin ? 'Administrator' : 'User'}
              </div>
            </div>
          </div>
          {showDropdown && (
            <div className="dropdown-menu">
              <button
                className="dropdown-item"
                onClick={() => {
                  setShowDropdown(false);
                  navigate(isAdmin ? '/admin/settings' : '/profile');
                }}
              >
                <HiOutlineUser /> Profile
              </button>
              <button
                className="dropdown-item"
                onClick={() => {
                  setShowDropdown(false);
                  navigate(isAdmin ? '/admin/settings' : '/settings');
                }}
              >
                <HiOutlineCog6Tooth /> Settings
              </button>
              <div className="dropdown-divider" />
              <button
                className="dropdown-item"
                onClick={() => {
                  setShowDropdown(false);
                  logout();
                }}
                style={{ color: '#ef4444' }}
              >
                <HiOutlineArrowRightOnRectangle /> Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
