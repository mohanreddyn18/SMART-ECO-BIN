const STORAGE_KEY = 'smart-eco-bin.pages.history.v1';
const USER_KEY = 'smart-eco-bin.pages.profile.v1';

export function readHistory() {
  try {
    const records = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    return Array.isArray(records) ? records : [];
  } catch {
    return [];
  }
}

export function saveClassification(result, fileName) {
  const record = {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    fileName,
    ...result,
    timestamp: new Date().toISOString()
  };
  const records = [record, ...readHistory()].slice(0, 500);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
  return records;
}

export function readProfile() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
  } catch {
    return null;
  }
}

export function saveProfile(name, email) {
  const profile = { name, email };
  localStorage.setItem(USER_KEY, JSON.stringify(profile));
  return profile;
}

export function clearHistory() {
  localStorage.removeItem(STORAGE_KEY);
}
