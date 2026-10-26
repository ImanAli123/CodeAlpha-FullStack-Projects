const $ = (id) => document.getElementById(id);
let token, me, socket, local, key, screen;
const peers = {}, names = {};
const ICE = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] }; // add a TURN server for restrictive NATs

// ---------- Auth ----------
async function authReq(path) {
  const r = await fetch('/api/' + path, { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: $('u').value, password: $('p').value }) });
  const d = await r.json();
  if (!r.ok) return ($('err').textContent = d.error || 'Error');
  token = d.token; me = d.name; $('auth').style.display = 'none'; $('lobby').style.display = 'flex';
}
$('login').onclick = () => authReq('login'); $('reg').onclick = () => authReq('register');

// ---------- E2E chat encryption (AES-GCM, key derived from room passphrase) ----------
async function deriveKey(pass, room) {
  const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pass), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey({ name: 'PBKDF2', salt: new TextEncoder().encode('meetboard:' + room), iterations: 150000, hash: 'SHA-256' },
    base, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
}
const b64 = (b) => btoa(String.fromCharCode(...new Uint8Array(b)));
const unb64 = (s) => Uint8Array.from(atob(s), c => c.charCodeAt(0));
async function enc(text) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, new TextEncoder().encode(text));
  return { iv: b64(iv), ct: b64(ct) };
}
async function dec(o) {
  try { return new TextDecoder().decode(await crypto.subtle.decrypt({ name: 'AES-GCM', iv: unb64(o.iv) }, key, unb64(o.ct))); }
  catch { return '[could not decrypt: wrong passphrase]'; }
}

// ---------- Join ----------
$('join').onclick = async () => {
  const room = $('room').value.trim();
  key = await deriveKey($('pass').value, room);
  local = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  $('lobby').style.display = 'none'; $('app').style.display = 'grid';
  addTile('me', local, me + ' (you)', true);
  socket = io({ auth: { token } });
  socket.on('connect', () => socket.emit('join', room));
  socket.on('peers', (list) => list.forEach(p => { names[p.id] = p.name; connect(p.id, true); }));
  socket.on('peer-joined', (p) => { names[p.id] = p.name; });
  socket.on('peer-left', (id) => { peers[id]?.close(); delete peers[id]; $('t-' + id)?.remove(); });
  socket.on('signal', onSignal);
  socket.on('chat', async (m) => log(m.name, await dec(m.msg)));
  socket.on('file', (f) => logFile(f.name, f));
  socket.on('draw', drawSeg); socket.on('board-history', (h) => h.forEach(drawSeg));
  socket.on('clear', () => ctx.clearRect(0, 0, board.width, board.height));
  socket.on('connect_error', () => alert('Auth failed, please log in again'));
};

// ---------- WebRTC (full mesh; fine for small rooms, use an SFU for large ones) ----------
function makePC(id) {
  const pc = new RTCPeerConnection(ICE); peers[id] = pc;
  local.getTracks().forEach(t => pc.addTrack(t, local));
  pc.onicecandidate = (e) => e.candidate && socket.emit('signal', { to: id, data: { ice: e.candidate } });
  pc.ontrack = (e) => addTile(id, e.streams[0], names[id] || id.slice(0, 5));
  return pc;
}
async function connect(id, initiator) {
  const pc = makePC(id);
  if (initiator) { await pc.setLocalDescription(await pc.createOffer()); socket.emit('signal', { to: id, data: { sdp: pc.localDescription } }); }
}
async function onSignal({ from, data }) {
  const pc = peers[from] || makePC(from);
  if (data.sdp) {
    await pc.setRemoteDescription(data.sdp);
    if (data.sdp.type === 'offer') { await pc.setLocalDescription(await pc.createAnswer()); socket.emit('signal', { to: from, data: { sdp: pc.localDescription } }); }
  } else if (data.ice) { try { await pc.addIceCandidate(data.ice); } catch {} }
}
function addTile(id, stream, label, muted) {
  let t = $('t-' + id);
  if (!t) { t = document.createElement('div'); t.className = 'tile'; t.id = 't-' + id;
    t.innerHTML = '<video autoplay playsinline></video><span></span>'; $('grid').append(t); }
  const v = t.querySelector('video'); v.srcObject = stream; v.muted = !!muted; t.querySelector('span').textContent = label;
}

// ---------- Controls ----------
$('mic').onclick = (e) => { const t = local.getAudioTracks()[0]; t.enabled = !t.enabled; e.target.textContent = t.enabled ? 'Mute' : 'Unmute'; };
$('cam').onclick = (e) => { const t = local.getVideoTracks()[0]; t.enabled = !t.enabled; e.target.textContent = t.enabled ? 'Camera off' : 'Camera on'; };
const setVideo = (track) => Object.values(peers).forEach(pc => pc.getSenders().find(s => s.track?.kind === 'video')?.replaceTrack(track));
$('scr').onclick = async (e) => {
  if (screen) return stopShare();
  screen = await navigator.mediaDevices.getDisplayMedia({ video: true });
  const track = screen.getVideoTracks()[0]; setVideo(track); addTile('me', screen, me + ' (screen)', true);
  track.onended = stopShare; e.target.textContent = 'Stop sharing';
};
function stopShare() { screen?.getTracks().forEach(t => t.stop()); screen = null; setVideo(local.getVideoTracks()[0]); addTile('me', local, me + ' (you)', true); $('scr').textContent = 'Share screen'; }
$('leave').onclick = () => location.reload();

// ---------- Chat + files ----------
function log(name, text) { const d = document.createElement('div'); d.textContent = name + ': ' + text; $('log').append(d); $('log').scrollTop = 1e9; }
function logFile(name, f) {
  const d = document.createElement('div'), a = document.createElement('a');
  a.textContent = f.fileName; a.href = '#'; a.onclick = async (ev) => { ev.preventDefault();
    const r = await fetch('/api/files/' + f.id, { headers: { Authorization: 'Bearer ' + token } });
    const u = URL.createObjectURL(await r.blob()), l = document.createElement('a'); l.href = u; l.download = f.fileName; l.click(); };
  d.append(name + ' shared: ', a); $('log').append(d);
}
$('msg').onkeydown = async (e) => { if (e.key !== 'Enter' || !e.target.value) return;
  socket.emit('chat', await enc(e.target.value)); log('me', e.target.value); e.target.value = ''; };
$('file').onchange = async (e) => {
  const f = e.target.files[0]; if (!f) return; const fd = new FormData(); fd.append('file', f);
  const r = await fetch('/api/upload', { method: 'POST', headers: { Authorization: 'Bearer ' + token }, body: fd });
  const d = await r.json(); if (!r.ok) return alert(d.error);
  const info = { id: d.id, fileName: d.name }; socket.emit('file', info); logFile('me', info); e.target.value = '';
};

// ---------- Whiteboard (normalized coordinates, synced + replayed for late joiners) ----------
const board = $('board'), ctx = board.getContext('2d'); let drawing = false, last;
$('wb').onclick = () => { const on = board.style.display !== 'block'; board.style.display = on ? 'block' : 'none'; $('grid').style.display = on ? 'none' : 'grid';
  if (on) { board.width = board.clientWidth; board.height = board.clientHeight; } };
$('clr').onclick = () => { ctx.clearRect(0, 0, board.width, board.height); socket.emit('clear'); };
const pos = (e) => { const r = board.getBoundingClientRect(); return [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]; };
function drawSeg(d) { ctx.strokeStyle = d.c; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.beginPath();
  ctx.moveTo(d.a[0] * board.width, d.a[1] * board.height); ctx.lineTo(d.b[0] * board.width, d.b[1] * board.height); ctx.stroke(); }
board.onpointerdown = (e) => { drawing = true; last = pos(e); };
board.onpointermove = (e) => { if (!drawing) return; const p = pos(e), d = { a: last, b: p, c: $('color').value }; drawSeg(d); socket.emit('draw', d); last = p; };
board.onpointerup = board.onpointerleave = () => drawing = false;