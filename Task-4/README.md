# MeetBoard: Real-Time Video Conferencing & Collaboration App

A multi-user video conferencing app with screen sharing, file sharing, a shared whiteboard, encrypted chat, and secure user authentication. Built for CodeAlpha Task 4.

## Features

- **Multi-user video calling** using WebRTC (peer-to-peer media)
- **Screen sharing** that replaces your camera feed for everyone in the room
- **File sharing** (up to 25 MB) through authenticated uploads and downloads
- **Collaborative whiteboard** synced live, with drawing history for late joiners
- **Encrypted chat**: AES-256-GCM in the browser, with the key derived from a room passphrase
- **User authentication** with bcrypt password hashing and JWT sessions
- Mute and camera toggles, color picker, clear board

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML, CSS, vanilla JavaScript |
| Real-time media | WebRTC (`RTCPeerConnection`, `getUserMedia`, `getDisplayMedia`) |
| Signaling / real-time events | Socket.io |
| Backend | Node.js, Express |
| Security | bcryptjs, jsonwebtoken, Helmet, express-rate-limit, Web Crypto API |
| File uploads | Multer |

## Project Structure

```
rtc-app/
├── package.json
├── server.js          # Express server, auth, uploads, Socket.io signaling
└── public/
    ├── index.html     # UI
    └── app.js         # WebRTC, chat encryption, whiteboard, controls
```

## Getting Started

### Prerequisites
- [Node.js](https://nodejs.org) 18 or newer

### Install and run

```bash
cd rtc-app
npm install
```

Windows (PowerShell):
```powershell
$env:JWT_SECRET="replace-with-a-long-random-string"; npm start
```

Mac/Linux:
```bash
JWT_SECRET=$(openssl rand -hex 32) npm start
```

Open **http://localhost:3000**.

### Try it out
1. Open two browser windows (one normal, one incognito).
2. Create a different account in each (username: letters, numbers, `_ . -`; password: 8+ characters).
3. Join the same room name with the same passphrase.
4. Allow camera and microphone access.

### Testing from other devices
Browsers only allow camera access over HTTPS (except on `localhost`). Generate a self-signed certificate and restart:

```bash
mkdir cert
openssl req -x509 -newkey rsa:2048 -nodes -keyout cert/key.pem -out cert/cert.pem -days 365 -subj "/CN=localhost"
```

Then open `https://<your-computer-ip>:3000` and accept the certificate warning.

## How It Works

1. **Authentication:** users register or log in over REST. The server returns a JWT, which is required for file endpoints and for the Socket.io handshake.
2. **Signaling:** when a user joins a room, Socket.io relays WebRTC offers, answers, and ICE candidates between peers. Media itself flows directly between browsers.
3. **Whiteboard:** strokes are sent as normalized coordinates, so they render correctly at any canvas size. The server keeps stroke history per room.
4. **Chat encryption:** messages are encrypted in the browser, so the server only relays ciphertext.

## Security

- WebRTC media is always encrypted (DTLS-SRTP)
- Passwords hashed with bcrypt (cost factor 12)
- JWTs expire after 8 hours; unauthenticated socket connections are rejected
- Login and registration are rate-limited
- Security headers via Helmet
- Uploads are size-limited, stored under random names, and only downloadable by logged-in users
- Use HTTPS in any real deployment

## Known Limitations

- Uses a full mesh topology, which works well for roughly 4-6 participants. Larger rooms need an SFU such as mediasoup or LiveKit.
- Only a public STUN server is configured. Some restrictive networks need a TURN server (for example coturn).
- Users are stored in a JSON file. A production setup should use a database.
- Uploaded files are not encrypted client-side.

## Future Improvements

- Client-side encryption for file uploads
- Database-backed user storage
- TURN server support
- Participant list and join/leave notifications
- Whiteboard eraser, brush sizes, and undo
- Meeting recording

## License

MIT