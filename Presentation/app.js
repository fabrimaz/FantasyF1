// ════════════════════════════════════════════════════════════════════════
// FANTASY F1 - CLIENT APP
// ════════════════════════════════════════════════════════════════════════

// ────────────────────────────────────────────────────────────────────────
// DATA & CONSTANTS
// ────────────────────────────────────────────────────────────────────────

let DRIVERS = [];  // Fetched from API
let CONSTRUCTORS = [];  // Fetched from API
let LEAGUES_DB = {};  // Fetched from API when needed

// ────────────────────────────────────────────────────────────────────────
// STATE
// ────────────────────────────────────────────────────────────────────────

let currentUser = null;
let authMode = 'login';
let selDrivers = [];
let selConstrs = [];

const BUDGET = 100;
let myLeagues = ['POLE24'];
let activeLeague = 'POLE24';
const API_BASE = 'http://localhost:5000/api';

// ────────────────────────────────────────────────────────────────────────
// INITIALIZATION
// ────────────────────────────────────────────────────────────────────────

async function initApp() {
  try {
    const driversResp = await fetch(API_BASE + '/drivers');
    DRIVERS = await driversResp.json();
    
    const constrsResp = await fetch(API_BASE + '/constructors');
    CONSTRUCTORS = await constrsResp.json();
    
    const leaguesResp = await fetch(API_BASE + '/leagues');
    const leagues = await leaguesResp.json();
    leagues.forEach(l => { LEAGUES_DB[l.code] = l; });
  } catch(e) {
    console.error('Failed to load reference data:', e);
    showToast('Errore caricamento dati', false);
  }
}

// Load data when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

// ────────────────────────────────────────────────────────────────────────
// UTILITY FUNCTIONS
// ────────────────────────────────────────────────────────────────────────

function $(id) { return document.getElementById(id); }

let toastTimer = null;
function showToast(msg, ok = false) {
  let t = document.getElementById('toast-el');
  if(!t) { 
    t = document.createElement('div');
    t.id = 'toast-el';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.className = 'toast' + (ok ? ' ok' : '');
  t.style.display = 'block';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.style.display = 'none', 3000);
}

function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  $('screen-' + name).classList.add('active');
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  if(name === 'team') document.querySelectorAll('.nav-tab')[0].classList.add('active');
  if(name === 'leagues') document.querySelectorAll('.nav-tab')[1].classList.add('active');
}

function goTo(screen) { 
  showScreen(screen); 
  if(screen === 'leagues') renderLeagues(); 
}

// ────────────────────────────────────────────────────────────────────────
// AUTHENTICATION
// ────────────────────────────────────────────────────────────────────────

function switchMode(mode) {
  authMode = mode;
  $('tab-login').className = 'login-tab' + (mode === 'login' ? ' active' : '');
  $('tab-register').className = 'login-tab' + (mode === 'register' ? ' active' : '');
  $('field-username').style.display = mode === 'register' ? 'flex' : 'none';
  $('login-error').style.display = 'none';
  $('auth-btn').textContent = mode === 'login' ? '→ Entra in pista' : '→ Crea account';
}

function showErr(msg) { 
  const el = $('login-error'); 
  el.textContent = '! ' + msg; 
  el.style.display = 'block'; 
}

function doAuth() {
  const email = $('inp-email').value.trim();
  const pw = $('inp-password').value;
  $('login-error').style.display = 'none';
  
  const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register';
  const payload = authMode === 'login' 
    ? {email, password: pw}
    : {username: $('inp-username').value.trim(), email, password: pw};
  
  if(!email || !pw) { showErr('Compila tutti i campi'); return; }
  if(authMode === 'register' && !payload.username) { showErr('Compila tutti i campi'); return; }
  
  fetch(API_BASE + endpoint, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(data => {
    if(data.error) { showErr(data.error); return; }
    setUser(data.user);
  })
  .catch(e => showErr('Errore: ' + e.message));
}

function setUser(u) {
  currentUser = u;
  $('nav-username').textContent = u.username;
  $('nav').style.display = 'flex';
  showScreen('team');
  renderTeamBuilder();
}

function logout() {
  currentUser = null;
  selDrivers = [];
  selConstrs = [];
  $('nav').style.display = 'none';
  showScreen('login');
}

// ────────────────────────────────────────────────────────────────────────
// TEAM BUILDER
// ────────────────────────────────────────────────────────────────────────

function calcSpent() { 
  return selDrivers.reduce((s,d) => s+d.price, 0) + selConstrs.reduce((s,c) => s+c.price, 0); 
}

function calcRem() { 
  return BUDGET - calcSpent(); 
}

function renderTeamBuilder() { 
  renderDriverGrid(); 
  renderConstrGrid(); 
  renderSlots(); 
  updateBudget(); 
}

function renderDriverGrid() {
  $('drivers-grid').innerHTML = DRIVERS.map(d => {
    const sel = !!selDrivers.find(x => x.id === d.id);
    const dis = !sel && (selDrivers.length >= 5 || calcRem() - d.price < 0);
    return `<div class="sel-card${sel ? ' sel-active' : ''}${dis ? ' sel-disabled' : ''}"
      style="border-left-color:${sel ? d.color : 'transparent'}"
      onclick="toggleDriver(${d.id})">
      <div class="sel-check">&#10003;</div>
      <div class="driver-num">${d.num}</div>
      <div class="driver-name">${d.name}</div>
      <div class="driver-team"><span class="team-dot" style="background:${d.color}"></span>${d.team}</div>
      <div class="driver-bottom">
        <div class="driver-price">$${d.price}M</div>
        <div class="driver-pts">${d.pts} pts</div>
      </div>
    </div>`;
  }).join('');
}

function renderConstrGrid() {
  $('constructors-grid').innerHTML = CONSTRUCTORS.map(c => {
    const sel = !!selConstrs.find(x => x.id === c.id);
    const dis = !sel && (selConstrs.length >= 2 || calcRem() - c.price < 0);
    return `<div class="sel-card${sel ? ' sel-active' : ''}${dis ? ' sel-disabled' : ''}"
      style="border-left-color:${sel ? c.color : 'transparent'}"
      onclick="toggleConstr(${c.id})">
      <div class="sel-check">&#10003;</div>
      <div style="display:flex;align-items:center;gap:10px">
        <div style="width:4px;height:36px;background:${c.color};border-radius:2px;flex-shrink:0"></div>
        <div>
          <div class="driver-name">${c.name}</div>
          <div class="driver-pts">${c.pts} pts</div>
        </div>
      </div>
      <div class="driver-price" style="margin-top:10px">$${c.price}M</div>
    </div>`;
  }).join('');
}

function renderSlots() {
  $('driver-slots').innerHTML = [0,1,2,3,4].map(i => {
    const d = selDrivers[i];
    return `<div class="slot${d ? '' : ' slot-empty'}">
      <div class="slot-type">P${i+1}</div>
      ${d ? `<div class="slot-bar" style="background:${d.color}"></div>
        <div class="slot-name">${d.name.split(' ').slice(-1)[0]}</div>
        <div class="slot-price">$${d.price}M</div>` :
        `<div class="slot-name">Libero</div>`}
    </div>`;
  }).join('');

  $('constr-slots').innerHTML = [0,1].map(i => {
    const c = selConstrs[i];
    return `<div class="slot${c ? '' : ' slot-empty'}">
      <div class="slot-type">S${i+1}</div>
      ${c ? `<div class="slot-bar" style="background:${c.color}"></div>
        <div class="slot-name">${c.name.split(' ')[0]}</div>
        <div class="slot-price">$${c.price}M</div>` :
        `<div class="slot-name">Libero</div>`}
    </div>`;
  }).join('');

  $('driver-count').textContent = selDrivers.length + '/5';
  $('constr-count').textContent = selConstrs.length + '/2';
  const ok = selDrivers.length === 5 && selConstrs.length === 2;
  $('save-btn').disabled = !ok;
  $('team-status').textContent = ok ? 'Team completo!' : 'Seleziona piloti e scuderie';
}

function updateBudget() {
  const rem = calcRem(), s = calcSpent();
  $('budget-left').textContent = '$' + rem.toFixed(1) + 'M';
  $('budget-spent').textContent = '$' + s.toFixed(1) + 'M';
  $('budget-fill').style.width = Math.max(0, (rem/BUDGET)*100) + '%';
  $('budget-fill').style.background = rem < 10 
    ? 'linear-gradient(90deg,#e8002d,#aa0020)' 
    : 'linear-gradient(90deg,var(--gold),#e09000)';
}

function toggleDriver(id) {
  const d = DRIVERS.find(x => x.id === id);
  const idx = selDrivers.findIndex(x => x.id === id);
  if(idx >= 0) { selDrivers.splice(idx, 1); }
  else {
    if(selDrivers.length >= 5) { showToast('Max 5 piloti'); return; }
    if(calcRem() - d.price < 0) { showToast('Budget insufficiente!'); return; }
    selDrivers.push(d);
  }
  renderTeamBuilder();
}

function toggleConstr(id) {
  const c = CONSTRUCTORS.find(x => x.id === id);
  const idx = selConstrs.findIndex(x => x.id === id);
  if(idx >= 0) { selConstrs.splice(idx, 1); }
  else {
    if(selConstrs.length >= 2) { showToast('Max 2 scuderie'); return; }
    if(calcRem() - c.price < 0) { showToast('Budget insufficiente!'); return; }
    selConstrs.push(c);
  }
  renderTeamBuilder();
}

function saveTeam() {
  fetch(API_BASE + '/team/' + currentUser.id, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      drivers: selDrivers,
      constructors: selConstrs
    })
  })
  .then(r => r.json())
  .then(data => {
    if(data.error) { showToast('Errore nel salvataggio'); return; }
    showToast('Team salvato! Buona gara!', true);
    setTimeout(() => goTo('leagues'), 1200);
  })
  .catch(e => showToast('Errore: ' + e.message));
}

// ────────────────────────────────────────────────────────────────────────
// LEAGUES & LEADERBOARDS
// ────────────────────────────────────────────────────────────────────────

function joinLeague() {
  const code = $('inp-code').value.trim().toUpperCase();
  if(!code) { showToast('Inserisci un codice lega'); return; }
  
  fetch(API_BASE + '/leagues/join/' + currentUser.id + '/' + code, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'}
  })
  .then(r => r.json())
  .then(data => {
    if(data.error) { showToast(data.error); return; }
    myLeagues.push(code);
    activeLeague = code;
    $('inp-code').value = '';
    showToast('Entrato in "' + data.league.name + '"!', true);
    renderLeagues();
  })
  .catch(e => showToast('Errore: ' + e.message));
}

function renderLeagues() {
  // Render my leagues list
  $('my-leagues-list').innerHTML = myLeagues.map(code => {
    const l = LEAGUES_DB[code] || {name:code, members:0};
    return `<div class="league-list-item${activeLeague === code ? ' active' : ''}" onclick="selectLeague('${code}')">
      <div><div class="lli-name">${l.name}</div><div class="lli-sub">${l.members} partecipanti</div></div>
      <div class="lli-arrow">&#8250;</div>
    </div>`;
  }).join('');

  // Leaderboard info
  const leagueCode = activeLeague;
  const l = LEAGUES_DB[leagueCode] || {name:leagueCode, members:0, round:'Round 14'};
  
  $('lb-name').textContent = l.name;
  $('lb-round').textContent = l.round;
  $('lb-members').textContent = l.members + ' manager';

  // Podium
  const [p1, p2, p3] = [LB[0], LB[1], LB[2]];
  $('podium').innerHTML =
    `<div class="podium-card p2"><div class="pod-pos">2</div><div class="pod-name">${p2.name}</div><div class="pod-team">${p2.team}</div><div class="pod-pts">${p2.pts}</div></div>
     <div class="podium-card p1"><div class="pod-pos">1</div><div class="pod-name">${p1.name}</div><div class="pod-team">${p1.team}</div><div class="pod-pts">${p1.pts}</div></div>
     <div class="podium-card p3"><div class="pod-pos">3</div><div class="pod-name">${p3.name}</div><div class="pod-team">${p3.team}</div><div class="pod-pts">${p3.pts}</div></div>`;

  // Leaderboard table
  $('lb-body').innerHTML = LB.map(r => {
    const chHtml = r.ch.startsWith('+') ? `<span class="ch-up">&#8593; ${r.ch}</span>` :
                   r.ch === '0' ? `<span class="ch-eq">&#8212;</span>` :
                   `<span class="ch-dn">&#8595; ${r.ch}</span>`;
    return `<tr class="${r.me ? 'me-row' : ''}">
      <td><span class="lb-pos${r.rank <= 3 ? ' gold' : ''}">${r.rank}</span></td>
      <td><div class="lb-name">${r.me ? '&#9658; ' : ''}${r.name}${r.me ? '<span class="me-badge">Tu</span>' : ''}</div><div class="lb-team-name">${r.team}</div></td>
      <td><span class="lb-pts">${r.pts}</span></td>
      <td>${chHtml}</td>
    </tr>`;
  }).join('');
}

function selectLeague(code) { 
  activeLeague = code; 
  renderLeagues(); 
}
