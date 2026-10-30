/**
 * Utility functions for EcoSort AI
 */

export function formatDate(dateStr) {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatTimeAgo(dateStr) {
  if (!dateStr) return '—';
  const now = new Date();
  const date = new Date(dateStr);
  const diff = now - date;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return 'Just now';
}

export function formatConfidence(value) {
  if (typeof value !== 'number') return '—';
  return `${value.toFixed(1)}%`;
}

export function capitalizeFirst(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function classToDisplayName(className) {
  if (!className) return '';
  return className
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function getConfidenceColor(confidence) {
  if (confidence >= 90) return '#10b981';
  if (confidence >= 75) return '#3b82f6';
  if (confidence >= 60) return '#f59e0b';
  return '#ef4444';
}

export function getConfidenceBadgeClass(confidence) {
  if (confidence >= 90) return 'badge-success';
  if (confidence >= 75) return 'badge-info';
  if (confidence >= 60) return 'badge-warning';
  return 'badge-danger';
}

export function getStatusColor(status) {
  switch (status?.toUpperCase()) {
    case 'GOOD': return 'green';
    case 'ATTENTION REQUIRED': return 'amber';
    case 'CRITICAL': return 'red';
    default: return 'gray';
  }
}

export function getImageMimeType(file) {
  if (!file) return null;

  const supportedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
  const declaredType = file.type?.toLowerCase();
  if (supportedTypes.includes(declaredType)) return declaredType;

  const extension = file.name?.split('.').pop()?.toLowerCase();
  const typesByExtension = {
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    png: 'image/png',
    webp: 'image/webp'
  };
  return typesByExtension[extension] || null;
}

export function validateImageFile(file) {
  const maxSize = 10 * 1024 * 1024; // 10MB

  if (!file) return { valid: false, error: 'No file selected' };
  if (!getImageMimeType(file)) {
    return { valid: false, error: 'Invalid file type. Please upload JPG, JPEG, PNG, or WebP images.' };
  }
  if (file.size > maxSize) {
    return { valid: false, error: 'File too large. Maximum size is 10MB.' };
  }
  return { valid: true, error: null };
}
