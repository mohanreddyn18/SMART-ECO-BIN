import React from 'react';

export default function StatCard({ title, value, subtitle, icon, trend, color = 'primary' }) {
  return (
    <div className={`stat-card card-${color}`}>
      <div className="stat-header">
        <span className="stat-title">{title}</span>
        {icon && <span className="stat-icon">{icon}</span>}
      </div>
      <div className="stat-value">{value}</div>
      {(subtitle || trend) && (
        <div className="stat-footer">
          {trend && (
            <span className={`stat-trend ${trend.positive ? 'positive' : 'negative'}`}>
              {trend.positive ? '↑' : '↓'} {trend.label}
            </span>
          )}
          {subtitle && <span className="stat-subtitle">{subtitle}</span>}
        </div>
      )}
    </div>
  );
}
