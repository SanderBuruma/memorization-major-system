/* ================================================================== */
/*  Profile stats                                                      */
/* ================================================================== */
function renderProfile(){
  var el = document.getElementById('profile-content');
  var allKeys = S.keys.length ? S.keys : [];
  var combined = allKeys.map(function(k){
    return (MODES.quiz.scores[k] || 0) + (MODES.reverse.scores[k] || 0) + (MODES.mixed.scores[k] || 0);
  });
  var n = allKeys.length || 1;
  var qCov = Math.round(allKeys.filter(function(k){ return MODES.quiz.scores[k] !== undefined; }).length / n * 100);
  var rCov = Math.round(allKeys.filter(function(k){ return MODES.reverse.scores[k] !== undefined; }).length / n * 100);
  var mCov = Math.round(allKeys.filter(function(k){ return MODES.mixed.scores[k] !== undefined; }).length / n * 100);
  var cAtt = S.conKeys.filter(function(k){ return MODES.consonant.scores[k] !== undefined; }).length;
  var cCov = S.conKeys.length ? Math.round(cAtt / S.conKeys.length * 100) : 0;
  var mast = [0, 0, 0, 0, 0];
  combined.forEach(function(s){
    if(s <= -3) mast[0]++;
    else if(s < 0) mast[1]++;
    else if(s <= 3) mast[2]++;
    else if(s <= 8) mast[3]++;
    else mast[4]++;
  });
  var sorted = combined.slice().sort(function(a, b){ return a - b; });
  var sMin = sorted[0] || 0, sMax = sorted[sorted.length - 1] || 0;
  var sMean = combined.length ? (combined.reduce(function(a, b){ return a + b; }, 0) / combined.length).toFixed(1) : 0;
  var sMed = 0;
  if(sorted.length){
    var mid = Math.floor(sorted.length / 2);
    sMed = sorted.length % 2 ? sorted[mid] : ((sorted[mid - 1] + sorted[mid]) / 2);
  }
  var cScores = S.conKeys.map(function(k){ return MODES.consonant.scores[k] || 0; }).sort(function(a, b){ return a - b; });
  var cMed = 0;
  if(cScores.length){
    var cm = Math.floor(cScores.length / 2);
    cMed = cScores.length % 2 ? cScores[cm] : ((cScores[cm - 1] + cScores[cm]) / 2);
  }
  var pct = S.score.total > 0 ? (S.score.correct / S.score.total * 100).toFixed(1) : 0;
  var labels = ['Struggling', 'Weak', 'Learning', 'Good', 'Mastered'];
  var mastMax = Math.max.apply(null, mast) || 1;
  var html = '<div class="card"><h2>Overall</h2>'
    + '<div class="stat-row"><span class="label">Total attempts</span><span class="value">' + S.score.total + '</span></div>'
    + '<div class="stat-row"><span class="label">Accuracy</span><span class="value">' + pct + '%</span></div>'
    + '</div>'
    + '<div class="card"><h2>Coverage by mode</h2><div class="cov-grid">'
    + '<div class="cov-item"><div class="cov-pct">' + qCov + '%</div><div class="cov-label"># &rarr; Word</div></div>'
    + '<div class="cov-item"><div class="cov-pct">' + rCov + '%</div><div class="cov-label">Word &rarr; #</div></div>'
    + '<div class="cov-item"><div class="cov-pct">' + mCov + '%</div><div class="cov-label">Mixed</div></div>'
    + '<div class="cov-item"><div class="cov-pct">' + cCov + '%</div><div class="cov-label">Sound &rarr; #</div></div>'
    + '</div></div>'
    + '<div class="card"><h2>Mastery distribution</h2>';
  for(var i = 0; i < 5; i++){
    var w = Math.round(mast[i] / mastMax * 100);
    html += '<div class="bar-row m' + i + '"><span class="bar-label">' + labels[i] + '</span>'
      + '<div class="bar-track"><div class="bar-fill" style="width:' + w + '%"></div></div>'
      + '<span class="bar-count">' + mast[i] + '</span></div>';
  }
  html += '</div>'
    + '<div class="card"><h2>Combined score</h2>'
    + '<div class="stat-row"><span class="label">Median</span><span class="value">' + sMed + '</span></div>'
    + '<div class="stat-row"><span class="label">Mean</span><span class="value">' + sMean + '</span></div>'
    + '<div class="stat-row"><span class="label">Min</span><span class="value">' + sMin + '</span></div>'
    + '<div class="stat-row"><span class="label">Max</span><span class="value">' + sMax + '</span></div>'
    + '</div>'
    + '<div class="card"><h2>Consonant sounds</h2>'
    + '<div class="stat-row"><span class="label">Coverage</span><span class="value">' + cCov + '%</span></div>'
    + '<div class="stat-row"><span class="label">Median score</span><span class="value">' + cMed + '</span></div>'
    + '</div>';
  el.innerHTML = html;
}
