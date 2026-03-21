import { appState, STATE_FIELDS, rebuildWordlist } from './state';
import { updateMasteryColors, renderGrid } from './ui';

export function getCookie(name: string): string {
  const cookieStr = document.cookie ?? '';
  const match = cookieStr.match(`(^|;)\\s*${name}\\s*=\\s*([^;]+)`);
  return match ? match.pop()! : '';
}

let _syncTimer: ReturnType<typeof setTimeout> | null = null;

export function saveState(): void {
  const state: Record<string, unknown> = {};
  STATE_FIELDS.forEach((field) => { state[field.key] = field.get(); });
  state.theme = document.documentElement.getAttribute('data-theme') ?? 'dark';
  localStorage.setItem('quizState', JSON.stringify(state));
  if (_syncTimer) clearTimeout(_syncTimer);
  _syncTimer = setTimeout(() => {
    fetch('/api/state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify(state),
    }).catch(() => {});
  }, 1000);
  updateMasteryColors();
}

export function loadState(): void {
  try {
    const raw = localStorage.getItem('quizState');
    if (!raw) return;
    const stored = JSON.parse(raw);
    if (!stored) return;
    if (stored.quizPool || stored.quizMastered) {
      localStorage.removeItem('quizState');
      return;
    }
    STATE_FIELDS.forEach((field) => { field.set(stored[field.key]); });
  } catch {}
}

export function applyState(state: Record<string, unknown>): void {
  STATE_FIELDS.forEach((field) => { if (field.key in state) field.set(state[field.key]); });
  rebuildWordlist();
  saveState();
  renderGrid();
}
