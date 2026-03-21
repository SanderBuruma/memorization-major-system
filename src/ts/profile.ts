import { appState, MODES, MASTERY_THRESHOLDS } from './state';

function activityLevel(count: number): number {
  if (count === 0) return 0;
  if (count <= 5) return 1;
  if (count <= 15) return 2;
  if (count <= 30) return 3;
  return 4;
}

function renderHeatmap(): string {
  const today = new Date();
  const dayOfWeek = (today.getDay() + 6) % 7; // 0=Mon ... 6=Sun
  const totalDays = 12 * 7 + dayOfWeek + 1;
  const startDate = new Date(today);
  startDate.setDate(today.getDate() - totalDays + 1);

  // Build weeks array: each week is an array of 7 day slots (Mon=0 .. Sun=6)
  const weeks: ({ key: string; count: number } | null)[][] = [];
  let currentWeek: ({ key: string; count: number } | null)[] = [];
  const d = new Date(startDate);
  for (let i = 0; i < totalDays; i++) {
    const key = d.toISOString().slice(0, 10);
    const dow = (d.getDay() + 6) % 7;
    if (dow === 0 && currentWeek.length > 0) {
      while (currentWeek.length < 7) currentWeek.push(null);
      weeks.push(currentWeek);
      currentWeek = [];
    }
    currentWeek.push({ key, count: appState.activityLog[key] ?? 0 });
    d.setDate(d.getDate() + 1);
  }
  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) currentWeek.push(null);
    weeks.push(currentWeek);
  }

  // Month labels row — one <td> per week, label on first week of each month
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  let monthRow = '<tr><td></td>'; // empty cell above day labels
  let lastMonth = -1;
  for (const week of weeks) {
    const firstDay = week.find(d => d !== null);
    if (firstDay) {
      const month = parseInt(firstDay.key.slice(5, 7)) - 1;
      if (month !== lastMonth) {
        monthRow += `<td class="hm-month">${monthNames[month]}</td>`;
        lastMonth = month;
      } else {
        monthRow += '<td></td>';
      }
    } else {
      monthRow += '<td></td>';
    }
  }
  monthRow += '</tr>';

  // Day rows — 7 rows (Mon-Sun), with day label in first column
  const dayLabels = ['Mon', '', 'Wed', '', 'Fri', '', ''];
  let bodyRows = '';
  for (let row = 0; row < 7; row++) {
    bodyRows += `<tr><td class="hm-day">${dayLabels[row]}</td>`;
    for (const week of weeks) {
      const day = week[row];
      if (day) {
        const level = activityLevel(day.count);
        const tooltip = `${day.key}: ${day.count} answer${day.count !== 1 ? 's' : ''}`;
        bodyRows += `<td><div class="hm-cell activity-${level}" title="${tooltip}"></div></td>`;
      } else {
        bodyRows += '<td></td>';
      }
    }
    bodyRows += '</tr>';
  }

  return `<div class="card"><h2>Activity</h2>`
    + `<div class="heatmap-container">`
    + `<table class="hm-table">${monthRow}${bodyRows}</table>`
    + `</div></div>`;
}

export function renderProfile(): void {
  const el = document.getElementById('profile-content')!;
  const allKeys = appState.keys;
  const combined = allKeys.map((key) =>
    (MODES.quiz.scores[key] ?? 0) + (MODES.reverse.scores[key] ?? 0) + (MODES.mixed.scores[key] ?? 0)
  );
  const totalKeys = allKeys.length || 1;
  const qCov = Math.round(allKeys.filter((key) => MODES.quiz.scores[key] !== undefined).length / totalKeys * 100);
  const rCov = Math.round(allKeys.filter((key) => MODES.reverse.scores[key] !== undefined).length / totalKeys * 100);
  const mCov = Math.round(allKeys.filter((key) => MODES.mixed.scores[key] !== undefined).length / totalKeys * 100);
  const cAtt = appState.conKeys.filter((key) => MODES.consonant.scores[key] !== undefined).length;
  const cCov = appState.conKeys.length ? Math.round(cAtt / appState.conKeys.length * 100) : 0;
  const [t0, t1, t2, t3] = MASTERY_THRESHOLDS;
  const mast = [0, 0, 0, 0, 0];
  combined.forEach((score) => {
    if (score <= t0) mast[0]++;
    else if (score < t1) mast[1]++;
    else if (score <= t2) mast[2]++;
    else if (score <= t3) mast[3]++;
    else mast[4]++;
  });
  const sorted = combined.slice().sort((a, b) => a - b);
  const sMin = sorted[0] ?? 0, sMax = sorted[sorted.length - 1] ?? 0;
  const sMean = combined.length ? (combined.reduce((a, b) => a + b, 0) / combined.length).toFixed(1) : 0;
  let sMed = 0;
  if (sorted.length) {
    const mid = Math.floor(sorted.length / 2);
    sMed = sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }
  const cScores = appState.conKeys.map((key) => MODES.consonant.scores[key] ?? 0).sort((a, b) => a - b);
  let cMed = 0;
  if (cScores.length) {
    const cm = Math.floor(cScores.length / 2);
    cMed = cScores.length % 2 ? cScores[cm] : (cScores[cm - 1] + cScores[cm]) / 2;
  }
  const pct = appState.score.total > 0 ? (appState.score.correct / appState.score.total * 100).toFixed(1) : 0;
  const labels = ['Struggling', 'Weak', 'Learning', 'Good', 'Mastered'];
  const mastMax = Math.max(...mast) || 1;
  let html = renderHeatmap()
    + `<div class="card"><h2>Overall</h2>`
    + `<div class="stat-row"><span class="label">Total attempts</span><span class="value">${appState.score.total}</span></div>`
    + `<div class="stat-row"><span class="label">Accuracy</span><span class="value">${pct}%</span></div>`
    + `</div>`
    + `<div class="card"><h2>Coverage by mode</h2><div class="cov-grid">`
    + `<div class="cov-item"><div class="cov-pct">${qCov}%</div><div class="cov-label"># &rarr; Word</div></div>`
    + `<div class="cov-item"><div class="cov-pct">${rCov}%</div><div class="cov-label">Word &rarr; #</div></div>`
    + `<div class="cov-item"><div class="cov-pct">${mCov}%</div><div class="cov-label">Mixed</div></div>`
    + `<div class="cov-item"><div class="cov-pct">${cCov}%</div><div class="cov-label">Sound &rarr; #</div></div>`
    + `</div></div>`
    + `<div class="card"><h2>Mastery distribution</h2>`;
  for (let tier = 0; tier < 5; tier++) {
    const barWidth = Math.round(mast[tier] / mastMax * 100);
    html += `<div class="bar-row m${tier}"><span class="bar-label">${labels[tier]}</span>`
      + `<div class="bar-track"><div class="bar-fill" style="width:${barWidth}%"></div></div>`
      + `<span class="bar-count">${mast[tier]}</span></div>`;
  }
  html += `</div>`
    + `<div class="card"><h2>Combined score</h2>`
    + `<div class="stat-row"><span class="label">Median</span><span class="value">${sMed}</span></div>`
    + `<div class="stat-row"><span class="label">Mean</span><span class="value">${sMean}</span></div>`
    + `<div class="stat-row"><span class="label">Min</span><span class="value">${sMin}</span></div>`
    + `<div class="stat-row"><span class="label">Max</span><span class="value">${sMax}</span></div>`
    + `</div>`
    + `<div class="card"><h2>Consonant sounds</h2>`
    + `<div class="stat-row"><span class="label">Coverage</span><span class="value">${cCov}%</span></div>`
    + `<div class="stat-row"><span class="label">Median score</span><span class="value">${cMed}</span></div>`
    + `</div>`;
  el.innerHTML = html;
}
