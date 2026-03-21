/* ================================================================== */
/*  Theme toggle                                                       */
/* ================================================================== */
var sunSVG = '<svg viewBox="0 0 24 24"><path d="M12 7a5 5 0 100 10 5 5 0 000-10zm0-3a1 1 0 01-1-1V1a1 1 0 112 0v2a1 1 0 01-1 1zm0 18a1 1 0 01-1-1v-2a1 1 0 112 0v2a1 1 0 01-1 1zm9-9a1 1 0 01-1 1h-2a1 1 0 110-2h2a1 1 0 011 1zM5 12a1 1 0 01-1 1H2a1 1 0 110-2h2a1 1 0 011 1zm13.07-5.66a1 1 0 01-.71-.29l-1.41-1.42a1 1 0 111.41-1.41l1.42 1.41a1 1 0 01-.71 1.71zM7.05 19.07a1 1 0 01-.71-.29l-1.41-1.42a1 1 0 111.41-1.41l1.42 1.41a1 1 0 01-.71 1.71zM19.07 19.07a1 1 0 01-.71-.29 1 1 0 010-1.42l1.42-1.41a1 1 0 111.41 1.41l-1.41 1.42a1 1 0 01-.71.29zM7.05 7.05a1 1 0 01-.71-.29 1 1 0 010-1.42l1.42-1.41a1 1 0 011.41 1.41L7.76 6.76a1 1 0 01-.71.29z"/></svg>';
var moonSVG = '<svg viewBox="0 0 24 24"><path d="M12.3 4.9a7.45 7.45 0 006.8 6.8 7.5 7.5 0 01-9.5 5.8A7.5 7.5 0 0112.3 4.9M12 2a10 10 0 100 20 10 10 0 000-20z"/></svg>';

function toggleTheme(){
  var current = document.documentElement.getAttribute('data-theme');
  var next = current === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateToggleIcon();
  saveState();
}

function updateToggleIcon(){
  var btn = document.getElementById('theme-toggle');
  var isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  btn.innerHTML = isDark ? sunSVG : moonSVG;
}

var savedTheme = localStorage.getItem('theme');
if(savedTheme) document.documentElement.setAttribute('data-theme', savedTheme);
updateToggleIcon();
