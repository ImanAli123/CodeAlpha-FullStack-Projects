// Backend: auth (bcrypt + JWT), file upload, Socket.io signaling for WebRTC
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const express = require('express'), helmet = require('helmet'), rateLimit = require('express-rate-limit');
const bcrypt = require('bcryptjs'), jwt = require('jsonwebtoken'), multer = require('multer');

const SECRET = process.env.JWT_SECRET || crypto.randomBytes(32).toString('hex'); // set JWT_SECRET in production
const PORT = process.env.PORT || 3000;
const app = express();

// HTTPS if certs exist (getUserMedia needs HTTPS except on localhost)
let server;
if (fs.existsSync('cert/key.pem') && fs.existsSync('cert/cert.pem')) {
  server = require('https').createServer({ key: fs.readFileSync('cert/key.pem'), cert: fs.readFileSync('cert/cert.pem') }, app);
} else server = require('http').createServer(app);
const io = require('socket.io')(server);

app.use(helmet());
app.use(express.json({ limit: '10kb' }));
app.use(express.static(path.join(__dirname, 'public')));

// --- Users (JSON file store; swap for a real DB in production) ---
const DB = 'users.json';
const users = fs.existsSync(DB) ? JSON.parse(fs.readFileSync(DB)) : {};
const save = () => fs.writeFileSync(DB, JSON.stringify(users));
const sign = (u) => jwt.sign({ name: u }, SECRET, { expiresIn: '8h' });

const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 30 });
app.post('/api/register', limiter, async (req, res) => {
  const { username, password } = req.body || {};
    if (!/^[\w.-]{3,20}$/.test(username || ''))
    return res.status(400).json({ error: 'Username must be 3-20 characters: letters, numbers, _ . - only (no spaces or @)' });
  if ((password || '').length < 8)
    return res.status(400).json({ error: 'Password must be at least 8 characters' });
  if (users[username]) return res.status(409).json({ error: 'Username taken' });
  users[username] = await bcrypt.hash(password, 12); save();
  res.json({ token: sign(username), name: username });
});
app.post('/api/login', limiter, async (req, res) => {
  const { username, password } = req.body || {};
  const hash = users[username];
  if (!hash || !(await bcrypt.compare(password || '', hash))) return res.status(401).json({ error: 'Invalid credentials' });
  res.json({ token: sign(username), name: username });
});

const auth = (req, res, next) => {
  try { req.user = jwt.verify((req.headers.authorization || '').slice(7) || req.query.token, SECRET); next(); }
  catch { res.status(401).json({ error: 'Unauthorized' }); }
};

// --- File sharing ---
fs.mkdirSync('uploads', { recursive: true });
const upload = multer({ dest: 'uploads/', limits: { fileSize: 25 * 1024 * 1024 } });
const meta = {}; // id -> original name
app.post('/api/upload', auth, upload.single('file'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file' });
  meta[req.file.filename] = req.file.originalname;
  res.json({ id: req.file.filename, name: req.file.originalname });
});
app.get('/api/files/:id', auth, (req, res) => {
  if (!/^[a-f0-9]{32}$/.test(req.params.id) || !meta[req.params.id]) return res.sendStatus(404);
  res.download(path.join(__dirname, 'uploads', req.params.id), meta[req.params.id]);
});

// --- Real-time: signaling, chat, whiteboard ---
io.use((s, next) => {
  try { s.user = jwt.verify(s.handshake.auth.token, SECRET).name; next(); }
  catch { next(new Error('unauthorized')); }
});
const boards = {}; // room -> stroke history for late joiners
io.on('connection', (s) => {
  s.on('join', (room) => {
    if (typeof room !== 'string' || !/^[\w-]{1,40}$/.test(room)) return;
    s.room = room; s.join(room);
    const peers = [...(io.sockets.adapter.rooms.get(room) || [])].filter(id => id !== s.id)
      .map(id => ({ id, name: io.sockets.sockets.get(id).user }));
    s.emit('peers', peers);
    s.emit('board-history', boards[room] || []);
    s.to(room).emit('peer-joined', { id: s.id, name: s.user });
  });
  s.on('signal', ({ to, data }) => io.to(to).emit('signal', { from: s.id, data })); // SDP + ICE relay
  s.on('chat', (msg) => s.room && s.to(s.room).emit('chat', { name: s.user, msg })); // msg is E2E-encrypted client-side
  s.on('file', (f) => s.room && s.to(s.room).emit('file', { name: s.user, ...f }));
  s.on('draw', (d) => {
    if (!s.room) return;
    (boards[s.room] ||= []).push(d);
    if (boards[s.room].length > 20000) boards[s.room].shift();
    s.to(s.room).emit('draw', d);
  });
  s.on('clear', () => { if (s.room) { boards[s.room] = []; s.to(s.room).emit('clear'); } });
  s.on('disconnect', () => s.room && s.to(s.room).emit('peer-left', s.id));
});

server.listen(PORT, () => console.log(`Running on ${server instanceof require('https').Server ? 'https' : 'http'}://localhost:${PORT}`));