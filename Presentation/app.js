// ════════════════════════════════════════════════════════════════════════
// FANTASY F1 - CLIENT APP
// ════════════════════════════════════════════════════════════════════════

// ────────────────────────────────────────────────────────────────────────
// DATA & CONSTANTS
// ────────────────────────────────────────────────────────────────────────

let DRIVERS = [];  // Fetched from API
let CONSTRUCTORS = [];  // Fetched from API
let LEAGUES_DB = {};  // Fetched from API when needed
let GRANDPRIX = [];  // Fetched from API

// ────────────────────────────────────────────────────────────────────────
// STATE
// ────────────────────────────────────────────────────────────────────────

let currentUser = null;
let authMode = 'login';
let selDrivers = [];
let selConstrs = [];
let selectedGP = null;  // Currently selected Grand Prix
let teamCanEdit = true;  // Whether team can be edited based on lock_date
let selectedLeagueGP = null;  // Selected GP for league view

const BUDGET = 100;
let myLeagues = ['POLE24'];
let activeLeague = 'POLE24';
const API_BASE = 'http://localhost:5000/api';

// ────────────────────────────────────────────────────────────────────────
// INITIALIZATION
// ────────────────────────────────────────────────────────────────────────

async function initApp() {
  try {
    const [driversResp, constrsResp, leaguesResp, gpsResp] = await Promise.all([
      fetch(API_BASE + '/drivers'),
      fetch(API_BASE + '/constructors'),
      fetch(API_BASE + '/leagues'),
      fetch(API_BASE + '/grandprix')
    ]);
    
    DRIVERS = await driversResp.json();
    CONSTRUCTORS = await constrsResp.json();
    const leagues = await leaguesResp.json();
    GRANDPRIX = await gpsResp.json();
    
    console.log('DRIVERS:', DRIVERS.length);
    console.log('CONSTRUCTORS:', CONSTRUCTORS.length);
    console.log('GRANDPRIX:', GRANDPRIX.length);
    
    leagues.forEach(l => { LEAGUES_DB[l.code] = l; });
    
    // Set current GP (the one with status='current', or first future one)
    selectedGP = GRANDPRIX.find(gp => gp.status === 'current') || GRANDPRIX.find(gp => gp.status === 'future');
    console.log('Selected GP:', selectedGP, " ", selectedGP.status);
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
  if(name === 'admin') {
    const adminTab = document.querySelectorAll('.nav-tab')[2];
    if(adminTab) adminTab.classList.add('active');
  }
}

function goTo(screen) { 
  showScreen(screen); 
  if(screen === 'leagues') renderLeagues();
  if(screen === 'admin') renderAdmin();
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

async function setUser(u) {
  currentUser = u;
  $('nav-username').textContent = u.username;
  $('nav').style.display = 'flex';
  
  // Mostra tab admin solo se Administrator
  const adminTab = $('nav-admin-tab');
  if(u.role === 'Administrator') {
    adminTab.style.display = 'block';
  } else {
    adminTab.style.display = 'none';
  }
  
  // Fetch user's leagues
  try {
    const resp = await fetch(API_BASE + '/leagues/user/' + u.id);
    myLeagues = await resp.json();
    myLeagues = myLeagues.map(l => l.code);  // Extract codes
    activeLeague = myLeagues[0] || null;
  } catch(e) {
    console.error('Error fetching user leagues:', e);
    myLeagues = [];
    activeLeague = null;
  }
  
  showScreen('team');
  renderTeamBuilder();
}

function logout() {
  currentUser = null;
  selDrivers = [];
  selConstrs = [];
  myLeagues = [];
  activeLeague = null;
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
  renderGPSelector();
  loadTeamForGP();
  renderDriverGrid(); 
  renderConstrGrid(); 
  renderSlots(); 
  updateBudget(); 
}

function renderGPSelector() {
  const gpSelector = $('gp-selector');
  gpSelector.innerHTML = GRANDPRIX.map(gp => {
    const isSelected = selectedGP && gp.id === selectedGP.id;
    return `<option value="${gp.id}" ${isSelected ? 'selected' : ''}>
      ${gp.name}${gp.status === 'current' ? ' (attualmente modificabile)' : gp.status === 'future' ? ' (prossimamente)' : ''}
    </option>`;
  }).join('');
}

async function loadTeamForGP() {
  if (!selectedGP || !currentUser) return;
  
  try {
    const resp = await fetch(API_BASE + `/team/${currentUser.id}/${selectedGP.id}`);
    const team = await resp.json();
    
    selDrivers = team.drivers || [];
    selConstrs = team.constructors || [];
    teamCanEdit = team.can_edit;
    console.log('Team loaded - can_edit:', teamCanEdit);
    
    // Disable save button if team is locked or incomplete
    $('save-btn').disabled = !teamCanEdit || team.drivers.length !== 5 || team.constructors.length !== 2;
  } catch(e) {
    console.error('Error loading team:', e);
    selDrivers = [];
    selConstrs = [];
    teamCanEdit = false;
  }
}

function renderDriverGrid() {
  console.log('renderDriverGrid - DRIVERS:', DRIVERS.length, 'selDrivers:', selDrivers.length, 'budget left:', calcRem());
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
  if (!teamCanEdit) { showToast('Team bloccato - qualifiche iniziate!'); return; }
  
  const d = DRIVERS.find(x => x.id === id);
  const idx = selDrivers.findIndex(x => x.id === id);
  if(idx >= 0) { selDrivers.splice(idx, 1); }
  else {
    if(selDrivers.length >= 5) { showToast('Max 5 piloti'); return; }
    if(calcRem() - d.price < 0) { showToast('Budget insufficiente!'); return; }
    selDrivers.push(d);
  }
  // Render only the UI, don't reload from server
  renderDriverGrid(); 
  renderConstrGrid(); 
  renderSlots(); 
  updateBudget();
}

function toggleConstr(id) {
  if (!teamCanEdit) { showToast('Team bloccato - qualifiche iniziate!'); return; }
  
  const c = CONSTRUCTORS.find(x => x.id === id);
  const idx = selConstrs.findIndex(x => x.id === id);
  if(idx >= 0) { selConstrs.splice(idx, 1); }
  else {
    if(selConstrs.length >= 2) { showToast('Max 2 scuderie'); return; }
    if(calcRem() - c.price < 0) { showToast('Budget insufficiente!'); return; }
    selConstrs.push(c);
  }
  // Render only the UI, don't reload from server
  renderDriverGrid(); 
  renderConstrGrid(); 
  renderSlots(); 
  updateBudget();
}

function saveTeam() {
  if (!selectedGP) { showToast('Seleziona un Grand Prix'); return; }
  if (!teamCanEdit) { showToast('Team bloccato - qualifiche iniziate!'); return; }
  
  fetch(API_BASE + '/team/' + currentUser.id + '/' + selectedGP.id, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      drivers: selDrivers,
      constructors: selConstrs
    })
  })
  .then(r => r.json())
  .then(data => {
    if(data.error) { showToast(data.error); return; }
    showToast('Team salvato per ' + selectedGP.name + '!', true);
  })
  .catch(e => showToast('Errore: ' + e.message));
}

function changeGP(gpId) {
  const newGP = GRANDPRIX.find(gp => gp.id === parseInt(gpId));
  if (newGP && newGP !== selectedGP) {
    selectedGP = newGP;
    renderTeamBuilder();  // This will call loadTeamForGP() which sets teamCanEdit
  }
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
  $('lb-members').textContent = l.members + ' manager';

  // GP Selector
  $('gp-selector-league').innerHTML = GRANDPRIX.map(gp => {
    const isSelected = selectedLeagueGP && gp.id === selectedLeagueGP.id;
    return `<option value="${gp.id}" ${isSelected ? 'selected' : ''}>
      Gran Premio del ${gp.name}
    </option>`;
  }).join('');

  // Load results for selected GP
  if (selectedLeagueGP) {
    loadLeagueGPResults();
  }
}

async function loadLeagueGPResults() {
  if (!selectedLeagueGP || !activeLeague) return;
  
  try {
    // Get league ID from code
    const leagueResp = await fetch(API_BASE + '/leagues/' + activeLeague);
    const leagueData = await leagueResp.json();
    
    const resultsResp = await fetch(API_BASE + '/league/' + leagueData.id + '/gp/' + selectedLeagueGP.id);
    const resultsData = await resultsResp.json();
    
    console.log('League GP results:', resultsData);
    
    // Render results
    const results = resultsData.results || [];
    $('lb-round').textContent = 'Gran Premio del ' + resultsData.gp.name;
    
    if (results.length === 0) {
      $('lb-body').innerHTML = '<tr><td colspan="4" style="text-align:center;padding:20px">Nessun risultato ancora per questo GP</td></tr>';
      return;
    }
    
    $('lb-body').innerHTML = results.map((r, idx) => {
      return `<tr>
        <td><span class="lb-pos${idx <= 2 ? ' gold' : ''}">${idx + 1}</span></td>
        <td><div class="lb-name">${r.username}</div></td>
        <td><span class="lb-pts">${r.points} pts</span></td>
        <td></td>
      </tr>`;
    }).join('');
  } catch(e) {
    console.error('Error loading league GP results:', e);
    $('lb-body').innerHTML = '<tr><td colspan="4">Errore nel caricamento</td></tr>';
  }
}

function changeLeagueGP(gpId) {
  const newGP = GRANDPRIX.find(gp => gp.id === parseInt(gpId));
  if (newGP) {
    selectedLeagueGP = newGP;
    loadLeagueGPResults();
  }
}

function selectLeague(code) { 
  activeLeague = code;
  // Set default GP to first future/current one
  selectedLeagueGP = GRANDPRIX.find(gp => gp.status === 'current') || GRANDPRIX.find(gp => gp.status === 'future') || GRANDPRIX[0];
  renderLeagues(); 
}

// ────────────────────────────────────────────────────────────────────────
// ADMIN PANEL
// ────────────────────────────────────────────────────────────────────────

async function renderAdmin() {
  // Carica lo stato del gioco
  try {
    const resp = await fetch(API_BASE + '/game/state');
    const gameState = await resp.json();
    
    // Popola il campo data
    const dateInput = $('gamestate-date');
    const date = new Date(gameState.current_date);
    dateInput.value = date.toISOString().slice(0, 16);  // Formato per datetime-local
  } catch(e) {
    console.error('Error loading game state:', e);
    showToast('Errore caricamento stato gioco', false);
  }
}

async function updateGameDate() {
  if(!currentUser || currentUser.role !== 'Administrator') {
    showToast('Solo admin può modificare la data', false);
    return;
  }
  
  const dateInput = $('gamestate-date');
  const dateStr = dateInput.value;
  if(!dateStr) {
    showToast('Seleziona una data', false);
    return;
  }
  
  // Il formato datetime-local è già nel formato corretto: YYYY-MM-DDTHH:mm
  // Convertiamo semplicemente aggiungendo :00 per i secondi
  const isoDate = dateStr + ':00';
  
  try {
    const resp = await fetch(API_BASE + '/game/state', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        admin_id: currentUser.id,
        current_date: isoDate
      })
    });
    
    const data = await resp.json();
    if(data.error) {
      showToast(data.error, false);
      return;
    }
    
    showToast('Data gioco aggiornata con successo!', true);
    // Ricarica tutte le viste per riflettere i nuovi stati dei GP
    renderTeamBuilder();
    renderLeagues();
  } catch(e) {
    showToast('Errore: ' + e.message, false);
  }
}

async function resetGameDate() {
  if(!currentUser || currentUser.role !== 'Administrator') {
    showToast('Solo admin può resettare la data', false);
    return;
  }
  
  if(!confirm('Sei sicuro? La data verrà resettata a now con offset 0')) {
    return;
  }
  
  try {
    const resp = await fetch(API_BASE + '/game/state/reset', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        admin_id: currentUser.id
      })
    });
    
    const data = await resp.json();
    if(data.error) {
      showToast(data.error, false);
      return;
    }
    
    showToast('Data ripristinata con successo!', true);
    renderAdmin();
    renderTeamBuilder();
    renderLeagues();
  } catch(e) {
    showToast('Errore: ' + e.message, false);
  }
}
