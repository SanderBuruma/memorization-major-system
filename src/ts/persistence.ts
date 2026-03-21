import { S, STATE_FIELDS, rebuildWordlist } from './state';
import { updateMasteryColors, updateScore, renderGrid } from './ui';

export function getCookie(name: string): string {
  const c = document.cookie ?? '';
  const v = c.match(`(^|;)\\s*${name}\\s*=\\s*([^;]+)`);
  return v ? v.pop()! : '';
}

let _syncTimer: ReturnType<typeof setTimeout> | null = null;

export function saveState(): void {
  const state: Record<string, unknown> = {};
  STATE_FIELDS.forEach((f) => { state[f.key] = f.get(); });
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
    const s = JSON.parse(localStorage.getItem('quizState')!);
    if (!s) return;
    if (s.quizPool || s.quizMastered) {
      localStorage.removeItem('quizState');
      return;
    }
    STATE_FIELDS.forEach((f) => { f.set(s[f.key]); });
  } catch {}
}

export function applyState(s: Record<string, unknown>): void {
  STATE_FIELDS.forEach((f) => { f.set(s[f.key]); });
  rebuildWordlist();
  saveState();
  updateScore();
  renderGrid();
}
