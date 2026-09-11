const canvas = document.querySelector('#gameCanvas');
const ctx = canvas.getContext('2d');
const menuView = document.querySelector('#menuView');
const gameView = document.querySelector('#gameView');
const notesView = document.querySelector('#notesView');
const authView = document.querySelector('#authView');
const authForm = document.querySelector('#authForm');
const passwordInput = document.querySelector('#passwordInput');
const authError = document.querySelector('#authError');
const title = document.querySelector('#gameTitle');
const kicker = document.querySelector('#gameKicker');
const hint = document.querySelector('#gameHint');
const W = canvas.width, H = canvas.height;
let activeGame = null, raf = 0, last = 0;
let soundEnabled = true;
let audioContext = null, beatTimer = 0, beatStep = 0;
const keys = {};
const pointer = { x: W / 2, y: H / 2, down: false };
const GAME_PASSWORD = '540612';
let authenticated = false;
let notesApp = null;

authForm.addEventListener('submit', event => {
  event.preventDefault();
  if (passwordInput.value === GAME_PASSWORD) {
    authenticated = true;
    authView.classList.add('hidden');
    menuView.classList.remove('hidden');
    authError.textContent = '';
    passwordInput.value = '';
    return;
  }
  authError.textContent = 'Incorrect password. Try again.';
  passwordInput.select();
});

document.querySelectorAll('[data-game]').forEach(card => card.addEventListener('click', () => startGame(card.dataset.game)));
document.querySelectorAll('[data-action="menu"]').forEach(button => button.addEventListener('click', showMenu));
document.querySelector('[data-action="sound"]').addEventListener('click', () => {
  const state = document.querySelector('#soundState');
  soundEnabled = !soundEnabled;
  state.textContent = soundEnabled ? 'ON' : 'OFF';
  if (soundEnabled) startBeat(); else stopBeat();
});
document.querySelector('#resetButton').addEventListener('click', () => activeGame?.reset());
window.addEventListener('keydown', event => {
  keys[event.key.toLowerCase()] = true;
  if (event.key === 'Escape' && activeGame) showMenu();
  if (activeGame && typeof activeGame.handleKey === 'function') {
    if (activeGame.mode === 'guess' || activeGame.mode === 'edit') {
      const isTypingInPasswordGame = activeGame.mode === 'guess' || activeGame.activeField === 'newPassword' || activeGame.activeField === 'newTitle';
      if (event.key.toLowerCase() === 'r' && !isTypingInPasswordGame) {
        activeGame.reset();
      }
      activeGame.handleKey(event);
      return;
    }
  }
  if (event.key.toLowerCase() === 'r') activeGame?.reset();
});
window.addEventListener('keyup', event => { keys[event.key.toLowerCase()] = false; });
function locate(event) { const rect = canvas.getBoundingClientRect(); pointer.x = (event.clientX - rect.left) * W / rect.width; pointer.y = (event.clientY - rect.top) * H / rect.height; }
canvas.addEventListener('pointermove', locate);
canvas.addEventListener('pointerdown', event => { locate(event); pointer.down = true; activeGame?.pointerDown(); });
window.addEventListener('pointerup', () => { pointer.down = false; activeGame?.pointerUp?.(); });
function showMenu() { if (!authenticated) return; cancelAnimationFrame(raf); activeGame = null; gameView.classList.add('hidden'); notesView.classList.add('hidden'); menuView.classList.remove('hidden'); document.querySelector('#statusText').textContent = 'ARCADE ONLINE'; }
function startGame(name) { if (!authenticated) return; if (name === 'notes') { cancelAnimationFrame(raf); activeGame = null; menuView.classList.add('hidden'); gameView.classList.add('hidden'); notesView.classList.remove('hidden'); document.querySelector('#statusText').textContent = 'NOTES OPEN'; notesApp ||= new NotesApp(); notesApp.open(); return; } cancelAnimationFrame(raf); const games = { bear: { game: BearGame, title: 'Cursor Bear', kicker: 'A WEATHER SURVIVAL GAME', hint: 'MOVE WITH THE CURSOR • WASD WIND' }, cat: { game: CatGame, title: 'Stretchy Cat Rap', kicker: 'A SPRINGY MUSIC TOY', hint: 'DRAG EITHER END OF THE CAT' }, balloon: { game: PopBalloonGame, title: 'Pop the Balloon', kicker: 'A TAP-TO-POP ARCADE GAME', hint: 'TAP THE BALLOON TO POP IT' }, guess: { game: GuessPasswordGame, title: 'Guess My Password', kicker: 'A SECRET CODE PUZZLE', hint: 'ENTER THE PASSWORD TO UNLOCK THE UPDATE FORM' }, runaway: { game: RunAwayGame, title: 'Run Away From the Cat', kicker: 'A QUICK REFLEX CHASE', hint: 'HOLD THE MOUSE AND DRAG IT AWAY FROM THE CAT' }, drawing: { game: DrawingGame, title: 'Drawing Game', kicker: 'A CREATIVE DOODLE STUDIO', hint: 'HOLD + DRAG TO DRAW • CLICK THE TOOLS TO PLAY' }, orbit: { game: OrbitGardenGame, title: 'Orbit Garden', kicker: 'A COSMIC GARDENING TOY', hint: 'MOVE THE MOON • TAP TO SEND AN ORBIT PULSE' } }; const selected = games[name]; if (!selected) return; activeGame = new selected.game(); menuView.classList.add('hidden'); notesView.classList.add('hidden'); gameView.classList.remove('hidden'); title.textContent = selected.title; kicker.textContent = selected.kicker; document.querySelector('#statusText').textContent = 'PLAYING'; hint.textContent = selected.hint; hint.classList.remove('fade'); setTimeout(() => hint.classList.add('fade'), 3500); if (soundEnabled) startBeat(); last = performance.now(); loop(last); }
function loop(now) { if (!activeGame) return; const dt = Math.min((now - last) / 1000, .033); last = now; activeGame.update(dt, now / 1000); activeGame.draw(ctx, now / 1000); raf = requestAnimationFrame(loop); }
function clamp(value, low, high) { return Math.max(low, Math.min(high, value)); }
function vector(x, y) { return { x, y }; }
function distance(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
function lerp(a, b, amount) { return vector(a.x + (b.x - a.x) * amount, a.y + (b.y - a.y) * amount); }
function roundedRect(c, x, y, width, height, radius, fill, stroke) { c.beginPath(); c.roundRect(x, y, width, height, radius); if (fill) { c.fillStyle = fill; c.fill(); } if (stroke) { c.strokeStyle = stroke; c.stroke(); } }
function startBeat() { if (beatTimer || !soundEnabled) return; audioContext ||= new AudioContext(); if (audioContext.state === 'suspended') audioContext.resume(); beatStep = 0; const tick = () => { if (!soundEnabled) return; const now = audioContext.currentTime; const oscillator = audioContext.createOscillator(); const gain = audioContext.createGain(); const frequency = [55, 55, 65.4, 49, 55, 73.4, 65.4, 49][beatStep % 8]; oscillator.type = beatStep % 4 === 2 ? 'square' : 'sine'; oscillator.frequency.setValueAtTime(frequency, now); gain.gain.setValueAtTime(.0001, now); gain.gain.exponentialRampToValueAtTime(beatStep % 2 ? .035 : .11, now + .012); gain.gain.exponentialRampToValueAtTime(.0001, now + .22); oscillator.connect(gain).connect(audioContext.destination); oscillator.start(now); oscillator.stop(now + .24); beatStep++; beatTimer = setTimeout(tick, 312); }; tick(); }
function stopBeat() { clearTimeout(beatTimer); beatTimer = 0; }

class CatGame {
  constructor() { this.reset(); }
  reset() { this.left = vector(330, 355); this.right = vector(670, 355); this.leftVelocity = vector(0, 0); this.rightVelocity = vector(0, 0); this.dragging = null; this.best = 1; this.wobble = 0; }
  pointerDown() { if (distance(pointer, this.left) < 105 || distance(pointer, this.right) < 105) { this.dragging = distance(pointer, this.left) < distance(pointer, this.right) ? 'left' : 'right'; this.wobble = 1; } }
  pointerUp() { if (this.dragging) { const point = this[this.dragging]; const home = this.dragging === 'left' ? vector(330, 355) : vector(670, 355); const velocity = this[`${this.dragging}Velocity`]; velocity.x += (home.x - point.x) * 2.5; velocity.y += (home.y - point.y) * 2.5; } this.dragging = null; }
  update(dt) { for (const [name, home] of [['left', vector(330, 355)], ['right', vector(670, 355)]]) { const point = this[name]; const velocity = this[`${name}Velocity`]; if (this.dragging === name) { point.x = clamp(pointer.x, 80, 920); point.y = clamp(pointer.y, 150, H - 115); velocity.x = velocity.y = 0; } else { velocity.x += (home.x - point.x) * 30 * dt; velocity.y += (home.y - point.y) * 30 * dt; velocity.x *= Math.pow(.84, dt * 60); velocity.y *= Math.pow(.84, dt * 60); point.x += velocity.x * dt; point.y += velocity.y * dt; } } this.wobble = Math.max(0, this.wobble - dt * 2.5); this.best = Math.max(this.best, this.ratio()); }
  ratio() { return distance(this.left, this.right) / 340; }
  draw(c, time) { c.fillStyle = '#272446'; c.fillRect(0, 0, W, H); for (let index = 0; index < 22; index++) { const barHeight = 22 + (Math.sin(time * 5 + index * .7) + 1) * 22; c.fillStyle = `hsl(${260 + index * 3}deg ${35 + index % 4 * 8}% ${35 + index * 2}%)`; c.fillRect(18 + index * 46, H - barHeight, 28, barHeight); } c.fillStyle = '#73e1db'; c.font = '700 43px Space Grotesk'; c.textAlign = 'center'; c.fillText('STRETCHY CAT RAP', W / 2, 65); c.fillStyle = '#fff7ff'; c.font = '600 20px Space Grotesk'; c.fillText('Grab either end • Pull • Release • BOING!', W / 2, 105); c.textAlign = 'left'; c.fillStyle = '#f482a1'; c.font = '700 23px Space Grotesk'; c.fillText(`STRETCH  ${this.ratio().toFixed(2)}x`, 25, 31); c.fillStyle = '#fff7ff'; c.font = '16px DM Mono'; c.fillText(`BEST ${this.best.toFixed(2)}x`, 28, 57); drawCat(c, this.left, this.right, this.dragging, time, this.wobble); c.textAlign = 'right'; c.fillText(`[M] MUSIC ${soundEnabled ? 'ON' : 'OFF'}  •  [R] RESET  •  [ESC] MENU`, W - 20, H - 18); c.textAlign = 'center'; c.fillStyle = '#ffda97'; c.font = '16px DM Mono'; c.fillText(['Pull that cat, let it snap!', 'Long cat groove with a springy back!', 'Stretch left, stretch right!', 'Feline flow all through the night!'][Math.floor(time / 2) % 4], W / 2, H - 51); }
}

function drawCat(c, left, right, dragging, time, wobble) {
  const axis = vector(right.x - left.x, right.y - left.y); const length = Math.max(1, distance(left, right)); const direction = vector(axis.x / length, axis.y / length); const normal = vector(-direction.y, direction.x); const width = clamp(116 / Math.sqrt(Math.max(.6, length / 340)), 70, 135);
  const bounce = Math.sin(time * 8) * 3 * wobble; left = vector(left.x + normal.x * bounce, left.y + normal.y * bounce); right = vector(right.x - normal.x * bounce, right.y - normal.y * bounce);
  c.fillStyle = '#181329'; c.beginPath(); c.ellipse((left.x + right.x) / 2, Math.max(left.y, right.y) + width * .62, Math.max(180, length * .92), 12, 0, 0, Math.PI * 2); c.fill();
  c.strokeStyle = '#e0a459'; c.lineWidth = 22; c.lineCap = 'round'; for (const fraction of [.18, .82]) { const hip = lerp(left, right, fraction); c.beginPath(); c.moveTo(hip.x + normal.x * width * .16, hip.y + normal.y * width * .16); c.lineTo(hip.x + direction.x * (fraction - .5) * 25, hip.y + direction.y * (fraction - .5) * 25 + width * .82); c.stroke(); c.beginPath(); c.arc(hip.x + direction.x * (fraction - .5) * 25, hip.y + direction.y * (fraction - .5) * 25 + width * .82, 16, 0, 7); c.fill(); }
  c.strokeStyle = '#ffda97'; c.lineWidth = width; c.beginPath(); c.moveTo(left.x, left.y); c.lineTo(right.x, right.y); c.stroke(); c.fillStyle = '#ffda97'; c.beginPath(); c.arc(left.x, left.y, width / 2, 0, 7); c.arc(right.x, right.y, width / 2, 0, 7); c.fill();
  c.strokeStyle = '#e0a459'; c.lineWidth = Math.max(7, width / 12); for (const fraction of [.3, .47, .64]) { const point = lerp(left, right, fraction); c.beginPath(); c.moveTo(point.x - normal.x * width * .46, point.y - normal.y * width * .46); c.lineTo(point.x - normal.x * width * .15, point.y - normal.y * width * .15); c.stroke(); }
  const tailBase = vector(left.x - direction.x * width * .28, left.y - direction.y * width * .28); c.strokeStyle = '#e0a459'; c.lineWidth = 22; c.beginPath(); c.moveTo(tailBase.x, tailBase.y); c.bezierCurveTo(tailBase.x - direction.x * 90 + normal.x * 25, tailBase.y - direction.y * 90 + normal.y * 25, tailBase.x - direction.x * 105 - normal.x * 125, tailBase.y - direction.y * 105 - normal.y * 125, tailBase.x - direction.x * 35 - normal.x * 135, tailBase.y - direction.y * 35 - normal.y * 135); c.stroke(); c.strokeStyle = '#ffda97'; c.lineWidth = 13; c.beginPath(); c.moveTo(tailBase.x, tailBase.y); c.bezierCurveTo(tailBase.x - direction.x * 90 + normal.x * 25, tailBase.y - direction.y * 90 + normal.y * 25, tailBase.x - direction.x * 105 - normal.x * 125, tailBase.y - direction.y * 105 - normal.y * 125, tailBase.x - direction.x * 35 - normal.x * 135, tailBase.y - direction.y * 35 - normal.y * 135); c.stroke();
  const head = vector(right.x + direction.x * width * .16, right.y + direction.y * width * .16); c.fillStyle = '#ffda97'; c.beginPath(); c.arc(head.x, head.y, width * .56, 0, 7); c.fill(); c.fillStyle = '#e0a459'; for (const sign of [-1, 1]) { c.beginPath(); c.moveTo(head.x - direction.x * width * .55 + normal.x * sign * width * .4, head.y - direction.y * width * .55 + normal.y * sign * width * .4); c.lineTo(head.x - direction.x * width * .05 + normal.x * sign * width * .28, head.y - direction.y * width * .05 + normal.y * sign * width * .28); c.lineTo(head.x - direction.x * width * .05 - normal.x * sign * width * .2, head.y - direction.y * width * .05 - normal.y * sign * width * .2); c.fill(); }
  c.fillStyle = '#302238'; for (const sign of [-1, 1]) { c.beginPath(); c.arc(head.x + direction.x * width * .2 + normal.x * sign * width * .2, head.y + direction.y * width * .2 + normal.y * sign * width * .2, 5, 0, 7); c.fill(); } c.fillStyle = '#f482a1'; c.beginPath(); c.arc(head.x + direction.x * width * .42, head.y + direction.y * width * .42, 7, 0, 7); c.fill();
  if (dragging) { const held = dragging === 'left' ? left : right; c.strokeStyle = '#73e1db'; c.lineWidth = 4; c.beginPath(); c.arc(held.x, held.y, width / 2 + 13, 0, 7); c.stroke(); }
}

class PopBalloonGame {
  constructor() { this.reset(); }
  reset() { this.score = 0; this.streak = 0; this.best = 0; this.elapsed = 0; this.pop = 0; this.particles = []; this.spawn(); }
  spawn() { this.balloon = vector(150 + Math.random() * 700, 180 + Math.random() * 390); this.radius = 58 + Math.random() * 18; this.color = ['#f85f79', '#ff936e', '#f5cb5c', '#5ce0d0'][this.score % 4]; }
  pointerDown() { if (distance(pointer, this.balloon) <= this.radius + 24) { this.score++; this.streak++; this.best = Math.max(this.best, this.streak); this.pop = 1; for (let index = 0; index < 18; index++) { const angle = Math.random() * Math.PI * 2; this.particles.push({ x: this.balloon.x, y: this.balloon.y, vx: Math.cos(angle) * (90 + Math.random() * 180), vy: Math.sin(angle) * (90 + Math.random() * 180), life: 1, color: this.color }); } this.spawn(); } else { this.streak = 0; } }
  update(dt) { this.elapsed += dt; this.pop = Math.max(0, this.pop - dt * 4); this.particles = this.particles.filter(particle => { particle.life -= dt * 1.8; particle.x += particle.vx * dt; particle.y += particle.vy * dt; particle.vy += 240 * dt; return particle.life > 0; }); }
  draw(c, time) { c.fillStyle = '#25384d'; c.fillRect(0, 0, W, H); c.fillStyle = '#f7d58a'; c.beginPath(); c.arc(810, 112, 56, 0, 7); c.fill(); for (let index = 0; index < 16; index++) { c.fillStyle = index % 2 ? '#36556a' : '#304b61'; c.fillRect(index * 72, 600 + Math.sin(time * 1.5 + index) * 12, 46, 100); } c.textAlign = 'left'; c.fillStyle = '#fff7df'; c.font = '700 24px Space Grotesk'; c.fillText(`POPS  ${String(this.score).padStart(2, '0')}`, 26, 42); c.fillStyle = '#f5cb5c'; c.font = '500 16px DM Mono'; c.fillText(`STREAK  ${this.streak}   BEST  ${this.best}`, 28, 69); c.textAlign = 'center'; c.fillStyle = '#fff7df'; c.font = '700 43px Space Grotesk'; c.fillText('POP THE BALLOON', W / 2, 69); c.font = '500 18px Space Grotesk'; c.fillText('Tap the balloon before it drifts away', W / 2, 104); drawBalloon(c, this.balloon, this.radius + Math.sin(time * 4) * 3, this.color); this.particles.forEach(particle => { c.globalAlpha = particle.life; c.fillStyle = particle.color; c.fillRect(particle.x, particle.y, 8, 8); }); c.globalAlpha = 1; c.textAlign = 'right'; c.fillStyle = '#d6e4e8'; c.font = '500 15px DM Mono'; c.fillText('[TAP] POP  •  [R] RESET  •  [ESC] MENU', W - 22, H - 20); }
}

function drawBalloon(c, point, radius, color) { c.save(); c.translate(point.x, point.y); c.fillStyle = color; c.shadowColor = 'rgba(0,0,0,.25)'; c.shadowBlur = 18; c.beginPath(); c.ellipse(0, 0, radius * .82, radius, -.1, 0, Math.PI * 2); c.fill(); c.shadowBlur = 0; c.fillStyle = 'rgba(255,255,255,.34)'; c.beginPath(); c.ellipse(-radius * .3, -radius * .35, radius * .13, radius * .28, -.4, 0, Math.PI * 2); c.fill(); c.fillStyle = color; c.beginPath(); c.moveTo(-8, radius * .92); c.lineTo(8, radius * .92); c.lineTo(0, radius * 1.1); c.fill(); c.strokeStyle = '#e8d8d0'; c.lineWidth = 2; c.beginPath(); c.moveTo(0, radius * 1.08); c.bezierCurveTo(16, radius * 1.5, -16, radius * 1.75, 0, radius * 2.05); c.stroke(); c.restore(); }

class GuessPasswordGame {
  constructor() {
    this.key = 'guess-my-password-state';
    this.cheat = '2217_540612';
    this.state = this.loadState();
    this.guess = '';
    this.newPassword = '';
    this.newTitle = this.state.title;
    this.mode = 'guess';
    this.activeField = 'guess';
    this.message = 'ENTER THE PASSWORD TO UNLOCK CHANGES.';
  }
  loadState() {
    try {
      const saved = JSON.parse(localStorage.getItem(this.key) || '{}');
      return {
        password: saved.password || '0000',
        title: saved.title || 'Guess My Password'
      };
    } catch {
      return { password: '0000', title: 'Guess My Password' };
    }
  }
  saveState() {
    localStorage.setItem(this.key, JSON.stringify(this.state));
  }
  handleKey(event) {
    if (!event.key || event.key === 'Escape') return;
    if (event.key === 'Enter') {
      this.submit();
      return;
    }
    if (event.key === 'Tab') {
      if (this.mode === 'edit') {
        this.activeField = this.activeField === 'newPassword' ? 'newTitle' : 'newPassword';
      }
      return;
    }
    if (event.key === 'Backspace') {
      if (this.mode === 'guess') {
        this.guess = this.guess.slice(0, -1);
      } else if (this.activeField === 'newPassword') {
        this.newPassword = this.newPassword.slice(0, -1);
      } else {
        this.newTitle = this.newTitle.slice(0, -1);
      }
      return;
    }
    if (event.key.length !== 1 || event.ctrlKey || event.metaKey || event.altKey) return;
    if (this.mode === 'guess') {
      this.guess += event.key;
    } else if (this.activeField === 'newPassword') {
      this.newPassword += event.key;
    } else {
      this.newTitle += event.key;
    }
  }
  submit() {
    if (this.mode === 'guess') {
      const guess = this.guess.trim();
      if (guess === this.state.password || guess === this.cheat) {
        this.mode = 'edit';
        this.activeField = 'newPassword';
        this.guess = '';
        this.newPassword = '';
        this.newTitle = this.state.title;
        this.message = 'PASSWORD ACCEPTED. CHOOSE A NEW PASSWORD AND TITLE.';
        return;
      }
      this.guess = '';
      this.message = 'INCORRECT PASSWORD. TRY AGAIN OR USE THE CHEAT CODE.';
      return;
    }
    const nextPassword = this.newPassword.trim();
    const nextTitle = (this.newTitle || this.state.title).trim();
    if (!nextPassword || nextPassword === this.cheat) {
      this.message = 'THE CHEAT CODE CANNOT BE YOUR NEW PASSWORD.';
      return;
    }
    this.state.password = nextPassword;
    this.state.title = nextTitle || this.state.title;
    this.saveState();
    this.mode = 'guess';
    this.activeField = 'guess';
    this.guess = '';
    this.newPassword = '';
    this.newTitle = this.state.title;
    this.message = 'PASSWORD AND TITLE SAVED.';
  }
  reset() {
    this.guess = '';
    this.newPassword = '';
    this.newTitle = this.state.title;
    this.mode = 'guess';
    this.activeField = 'guess';
    this.message = 'ENTER THE PASSWORD TO UNLOCK CHANGES.';
  }
  update() {}
  draw(c) {
    c.fillStyle = '#1b1235';
    c.fillRect(0, 0, W, H);
    c.fillStyle = '#fff5d6';
    c.font = '700 52px Space Grotesk';
    c.textAlign = 'center';
    c.fillText(this.state.title, W / 2, 82);

    c.fillStyle = '#91d5ff';
    c.font = '500 18px Space Grotesk';
    c.fillText('SECRET CODE / RENAME LOCK', W / 2, 118);

    c.fillStyle = '#2a2242';
    c.fillRect(110, 160, 780, 360);
    c.strokeStyle = '#7bc0ff';
    c.strokeRect(110, 160, 780, 360);

    c.fillStyle = '#dfe9ff';
    c.font = '600 24px Space Grotesk';
    c.textAlign = 'left';
    c.fillText(this.mode === 'guess' ? 'ENTER PASSWORD' : 'NEW PASSWORD', 145, 210);

    const guessBox = { x: 145, y: 225, w: 710, h: 54 };
    c.fillStyle = '#141827';
    c.fillRect(guessBox.x, guessBox.y, guessBox.w, guessBox.h);
    c.strokeStyle = this.mode === 'guess' && this.activeField === 'guess' ? '#90f0a2' : '#7bc0ff';
    c.strokeRect(guessBox.x, guessBox.y, guessBox.w, guessBox.h);
    c.fillStyle = '#f4f8ff';
    c.font = '700 28px DM Mono';
    c.fillText(this.mode === 'guess' ? this.guess : this.newPassword, 165, 260);

    if (this.mode === 'edit') {
      c.fillStyle = '#dfe9ff';
      c.font = '600 24px Space Grotesk';
      c.fillText('NEW GAME NAME', 145, 320);
      const nameBox = { x: 145, y: 335, w: 710, h: 54 };
      c.fillStyle = '#141827';
      c.fillRect(nameBox.x, nameBox.y, nameBox.w, nameBox.h);
      c.strokeStyle = this.activeField === 'newTitle' ? '#90f0a2' : '#7bc0ff';
      c.strokeRect(nameBox.x, nameBox.y, nameBox.w, nameBox.h);
      c.fillStyle = '#f4f8ff';
      c.font = '700 25px DM Mono';
      c.fillText(this.newTitle, 165, 370);
    }

    c.fillStyle = '#dfe9ff';
    c.font = '600 22px Space Grotesk';
    c.fillText(this.message, 145, 520);

    c.fillStyle = '#90f0a2';
    c.fillRect(690, 540, 165, 52);
    c.fillStyle = '#183124';
    c.font = '700 24px Space Grotesk';
    c.textAlign = 'center';
    c.fillText(this.mode === 'guess' ? 'TRY' : 'SAVE', 772, 575);
    c.textAlign = 'left';
  }
  pointerDown() {
    const saveButton = { x: 690, y: 540, w: 165, h: 52 };
    if (pointer.x >= saveButton.x && pointer.x <= saveButton.x + saveButton.w && pointer.y >= saveButton.y && pointer.y <= saveButton.y + saveButton.h) {
      this.submit();
      return;
    }

    if (this.mode === 'guess') {
      const guessBox = { x: 145, y: 225, w: 710, h: 54 };
      if (pointer.x >= guessBox.x && pointer.x <= guessBox.x + guessBox.w && pointer.y >= guessBox.y && pointer.y <= guessBox.y + guessBox.h) {
        this.activeField = 'guess';
      }
      return;
    }

    const newPasswordBox = { x: 145, y: 225, w: 710, h: 54 };
    const newTitleBox = { x: 145, y: 335, w: 710, h: 54 };

    if (pointer.x >= newPasswordBox.x && pointer.x <= newPasswordBox.x + newPasswordBox.w && pointer.y >= newPasswordBox.y && pointer.y <= newPasswordBox.y + newPasswordBox.h) {
      this.activeField = 'newPassword';
      return;
    }

    if (pointer.x >= newTitleBox.x && pointer.x <= newTitleBox.x + newTitleBox.w && pointer.y >= newTitleBox.y && pointer.y <= newTitleBox.y + newTitleBox.h) {
      this.activeField = 'newTitle';
    }
  }
}

class RunAwayGame {
  constructor() { this.reset(); }
  reset() { this.mouse = vector(220, 390); this.cat = vector(780, 300); this.elapsed = 0; this.best = 0; this.over = false; this.dragging = false; }
  pointerDown() { if (!this.over && distance(pointer, this.mouse) < 90) this.dragging = true; }
  pointerUp() { this.dragging = false; }
  update(dt) {
    if (this.over) return;
    if (this.dragging) {
      this.mouse.x = clamp(pointer.x, 64, W - 64);
      this.mouse.y = clamp(pointer.y, 125, H - 72);
    }
    const chase = vector(this.mouse.x - this.cat.x, this.mouse.y - this.cat.y);
    const chaseDistance = Math.max(1, distance(this.mouse, this.cat));
    const catSpeed = 92;
    this.cat.x += chase.x / chaseDistance * catSpeed * dt;
    this.cat.y += chase.y / chaseDistance * catSpeed * dt;
    this.elapsed += dt;
    this.best = Math.max(this.best, this.elapsed);
    if (distance(this.mouse, this.cat) < 58) this.over = true;
  }
  draw(c, time) {
    c.fillStyle = '#183c3a'; c.fillRect(0, 0, W, H);
    c.strokeStyle = 'rgba(128, 221, 179, .18)'; c.lineWidth = 2;
    for (let x = 0; x <= W; x += 50) { c.beginPath(); c.moveTo(x, 96); c.lineTo(x, H); c.stroke(); }
    for (let y = 110; y <= H; y += 50) { c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
    c.fillStyle = '#eaffd0'; c.font = '700 39px Space Grotesk'; c.textAlign = 'center'; c.fillText('RUN AWAY FROM THE CAT', W / 2, 62);
    c.fillStyle = '#8be0b5'; c.font = '500 17px DM Mono'; c.fillText('KEEP THE MOUSE MOVING', W / 2, 91);
    c.textAlign = 'left'; c.fillStyle = '#f8e7a2'; c.font = '700 22px Space Grotesk'; c.fillText(`TIME  ${this.elapsed.toFixed(1)}s`, 25, 40);
    c.fillStyle = '#d4f3dc'; c.font = '15px DM Mono'; c.fillText(`BEST  ${this.best.toFixed(1)}s`, 27, 67);
    drawChaseCat(c, this.cat, time); drawMouse(c, this.mouse, this.dragging, time);
    c.textAlign = 'right'; c.fillStyle = '#d4f3dc'; c.font = '15px DM Mono'; c.fillText('[HOLD + DRAG] MOVE  •  [R] RESET  •  [ESC] MENU', W - 22, H - 20);
    if (this.over) {
      c.fillStyle = 'rgba(8, 25, 25, .82)'; c.fillRect(0, 0, W, H); roundedRect(c, 245, 235, 510, 240, 18, '#351f35', '#ff9a76');
      c.textAlign = 'center'; c.fillStyle = '#fff4d6'; c.font = '700 54px Space Grotesk'; c.fillText('CAUGHT!', W / 2, 325); c.font = '20px Space Grotesk'; c.fillText(`You lasted ${this.elapsed.toFixed(1)} seconds.`, W / 2, 373); c.font = '500 14px DM Mono'; c.fillText('PRESS R OR USE RESET TO RUN AGAIN', W / 2, 425);
    }
  }
}

class NotesApp {
  constructor() {
    this.storageKey = 'game-center-notes';
    this.notes = this.load();
    this.activeId = this.notes[0]?.id || null;
    this.search = document.querySelector('#notesSearch');
    this.list = document.querySelector('#notesList');
    this.titleInput = document.querySelector('#noteTitleInput');
    this.bodyInput = document.querySelector('#noteBodyInput');
    this.colorInput = document.querySelector('#noteColor');
    this.status = document.querySelector('#saveStatus');
    this.bindEvents();
  }
  load() {
    try {
      const saved = JSON.parse(localStorage.getItem(this.storageKey) || 'null');
      if (Array.isArray(saved) && saved.length) return saved;
    } catch {}
    return [{ id: crypto.randomUUID(), title: 'Welcome to Notes', body: 'A quiet place for bright ideas.\n\nStart typing here, then pin anything you want to keep close.', color: '#f6d36f', pinned: true, updated: Date.now() }];
  }
  bindEvents() {
    document.querySelector('#newNoteButton').addEventListener('click', () => this.create());
    document.querySelector('#pinnedFilter').addEventListener('click', event => { event.currentTarget.setAttribute('aria-pressed', event.currentTarget.getAttribute('aria-pressed') !== 'true'); this.renderList(); });
    document.querySelector('#pinNoteButton').addEventListener('click', () => this.togglePin());
    document.querySelector('#deleteNoteButton').addEventListener('click', () => this.remove());
    document.querySelector('#exportNoteButton').addEventListener('click', () => this.exportNote());
    this.search.addEventListener('input', () => this.renderList());
    this.titleInput.addEventListener('input', () => this.updateActive());
    this.bodyInput.addEventListener('input', () => this.updateActive());
    this.colorInput.addEventListener('input', () => this.updateActive());
    document.addEventListener('keydown', event => {
      if (!notesView.classList.contains('hidden')) {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'n') { event.preventDefault(); this.create(); }
        if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key.toLowerCase() === 'p') { event.preventDefault(); this.togglePin(); }
      }
    });
  }
  open() { this.renderList(); this.select(this.activeId || this.notes[0]?.id); }
  active() { return this.notes.find(note => note.id === this.activeId); }
  create() { const note = { id: crypto.randomUUID(), title: 'Untitled note', body: '', color: '#b9e3d0', pinned: false, updated: Date.now() }; this.notes.unshift(note); this.activeId = note.id; this.persist(); this.renderList(); this.select(note.id); this.titleInput.focus(); this.titleInput.select(); }
  select(id) { const note = this.notes.find(item => item.id === id); if (!note) return; this.activeId = id; this.titleInput.value = note.title; this.bodyInput.value = note.body; this.colorInput.value = note.color; document.querySelector('#pinNoteButton').textContent = note.pinned ? '★ PINNED' : '☆ PIN'; document.querySelector('#pinNoteButton').setAttribute('aria-pressed', note.pinned); document.querySelector('#noteMeta').textContent = `UPDATED ${new Date(note.updated).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).toUpperCase()}`; this.renderList(); }
  updateActive() { const note = this.active(); if (!note) return; note.title = this.titleInput.value || 'Untitled note'; note.body = this.bodyInput.value; note.color = this.colorInput.value; note.updated = Date.now(); this.persist(); this.renderList(); document.querySelector('#noteMeta').textContent = 'SAVING...'; clearTimeout(this.saveLabelTimer); this.saveLabelTimer = setTimeout(() => { document.querySelector('#noteMeta').textContent = `UPDATED ${new Date(note.updated).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).toUpperCase()}`; }, 450); }
  togglePin() { const note = this.active(); if (!note) return; note.pinned = !note.pinned; note.updated = Date.now(); this.persist(); this.select(note.id); }
  remove() { if (!this.active() || !confirm('Delete this note?')) return; this.notes = this.notes.filter(note => note.id !== this.activeId); if (!this.notes.length) this.create(); else { this.activeId = this.notes[0].id; this.renderList(); this.select(this.activeId); } this.persist(); }
  persist() { localStorage.setItem(this.storageKey, JSON.stringify(this.notes)); this.status.textContent = 'ALL CHANGES SAVED'; }
  renderList() { const query = this.search.value.trim().toLowerCase(); const pinnedOnly = document.querySelector('#pinnedFilter').getAttribute('aria-pressed') === 'true'; const visible = this.notes.filter(note => (!pinnedOnly || note.pinned) && (!query || `${note.title} ${note.body}`.toLowerCase().includes(query))); document.querySelector('#notesCount').textContent = `${visible.length} ${visible.length === 1 ? 'NOTE' : 'NOTES'}`; this.list.innerHTML = visible.map(note => `<button class="note-list-item ${note.id === this.activeId ? 'selected' : ''}" data-note-id="${note.id}" style="--note-accent:${note.color}" type="button"><span class="note-item-top"><strong>${this.escape(note.title || 'Untitled note')}</strong><span>${note.pinned ? '★' : ''}</span></span><span>${this.escape(note.body.replace(/\s+/g, ' ').trim().slice(0, 72) || 'No text yet')}</span><small>${this.relative(note.updated)}</small></button>`).join('') || '<p class="empty-notes">No notes match that search.</p>'; this.list.querySelectorAll('[data-note-id]').forEach(item => item.addEventListener('click', () => this.select(item.dataset.noteId))); }
  relative(timestamp) { const minutes = Math.max(0, Math.round((Date.now() - timestamp) / 60000)); return minutes < 1 ? 'JUST NOW' : minutes < 60 ? `${minutes}M AGO` : `${Math.round(minutes / 60)}H AGO`; }
  escape(value) { return value.replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[character])); }
  exportNote() { const note = this.active(); if (!note) return; const blob = new Blob([`${note.title}\n\n${note.body}`], { type: 'text/plain' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${note.title.replace(/[^a-z0-9]+/gi, '-').toLowerCase() || 'note'}.txt`; link.click(); URL.revokeObjectURL(link.href); }
}

class OrbitGardenGame {
  constructor() { this.reset(); }
  reset() {
    this.sun = vector(W / 2, 370); this.moon = vector(W / 2 + 220, 370); this.target = vector(this.moon.x, this.moon.y); this.flowers = []; this.particles = []; this.score = 0; this.combo = 0; this.best = 0; this.energy = 100; this.elapsed = 0; this.pulse = 0; this.flare = 0; this.flareWarning = 0; this.flareAngle = 0; this.spawnTimer = 0; this.lost = false;
    for (let index = 0; index < 8; index++) this.spawnFlower();
  }
  spawnFlower() { const angle = Math.random() * Math.PI * 2; const radius = 105 + Math.random() * 240; this.flowers.push({ x: this.sun.x + Math.cos(angle) * radius, y: this.sun.y + Math.sin(angle) * radius, radius: 8 + Math.random() * 5, phase: Math.random() * 7 }); }
  pointerDown() { this.pulse = 1; this.energy = Math.max(0, this.energy - 8); }
  update(dt, time) {
    if (this.lost) return;
    this.elapsed += dt; this.target = vector(clamp(pointer.x, 45, W - 45), clamp(pointer.y, 125, H - 65)); this.moon.x += (this.target.x - this.moon.x) * Math.min(1, dt * 8); this.moon.y += (this.target.y - this.moon.y) * Math.min(1, dt * 8); this.pulse = Math.max(0, this.pulse - dt * 2.8); this.energy = Math.min(100, this.energy + dt * 2.2); this.spawnTimer -= dt;
    if (this.spawnTimer <= 0 && this.flowers.length < 12) { this.spawnFlower(); this.spawnTimer = 2.2; }
    this.flare = Math.max(0, this.flare - dt); if (this.flareWarning > 0) { this.flareWarning -= dt; if (this.flareWarning <= 0) this.flare = 1.8; } if (this.elapsed > 5 && Math.floor(this.elapsed / 7) !== Math.floor((this.elapsed - dt) / 7)) { this.flareWarning = 1.5; this.flare = 0; this.flareAngle = Math.random() * Math.PI * 2; }
    this.flowers = this.flowers.filter(flower => { const hit = distance(this.moon, flower) < 30; if (hit) { this.score++; this.combo++; this.best = Math.max(this.best, this.combo); this.bloom(flower, time); return false; } if (distance(this.moon, flower) > 370) this.combo = 0; return true; });
    const moonAngle = Math.atan2(this.moon.y - this.sun.y, this.moon.x - this.sun.x); const angleDelta = Math.atan2(Math.sin(moonAngle - this.flareAngle), Math.cos(moonAngle - this.flareAngle)); if (this.flare > 0 && Math.abs(angleDelta) < .25 && distance(this.moon, this.sun) < 330) { this.energy = Math.max(0, this.energy - dt * 35); this.combo = 0; }
    if (this.energy <= 0) this.lost = true; this.particles = this.particles.filter(particle => { particle.life -= dt * 1.6; particle.x += particle.vx * dt; particle.y += particle.vy * dt; return particle.life > 0; });
  }
  bloom(flower, time) { for (let index = 0; index < 12; index++) { const angle = index / 12 * Math.PI * 2; this.particles.push({ x: flower.x, y: flower.y, vx: Math.cos(angle) * (30 + Math.random() * 70), vy: Math.sin(angle) * (30 + Math.random() * 70), life: 1, color: `hsl(${(time * 50 + index * 25) % 360} 75% 67%)` }); } }
  draw(c, time) {
    c.fillStyle = '#0d1b2a'; c.fillRect(0, 0, W, H); c.fillStyle = 'rgba(88,159,170,.12)'; for (let index = 0; index < 40; index++) { const x = (index * 173) % W; const y = (index * 97) % H; c.beginPath(); c.arc(x, y, 1 + index % 3, 0, Math.PI * 2); c.fill(); }
    c.strokeStyle = 'rgba(161,230,214,.25)'; c.lineWidth = 2; for (const radius of [130, 225, 315]) { c.beginPath(); c.arc(this.sun.x, this.sun.y, radius, 0, Math.PI * 2); c.stroke(); }
    c.fillStyle = '#f6d36f'; c.shadowColor = '#f6d36f'; c.shadowBlur = 40 + Math.sin(time * 3) * 8; c.beginPath(); c.arc(this.sun.x, this.sun.y, 52 + Math.sin(time * 2) * 3, 0, Math.PI * 2); c.fill(); c.shadowBlur = 0;
    this.flowers.forEach(flower => { c.save(); c.translate(flower.x, flower.y); c.rotate(time + flower.phase); c.fillStyle = '#a1e6d6'; c.beginPath(); for (let petal = 0; petal < 6; petal++) { c.rotate(Math.PI / 3); c.ellipse(0, flower.radius * .9, flower.radius * .45, flower.radius, 0, 0, Math.PI * 2); } c.fill(); c.fillStyle = '#fff4bd'; c.beginPath(); c.arc(0, 0, flower.radius * .35, 0, Math.PI * 2); c.fill(); c.restore(); });
    if (this.flareWarning > 0 || this.flare > 0) { c.save(); c.translate(this.sun.x, this.sun.y); c.rotate(this.flareAngle); c.strokeStyle = this.flareWarning > 0 ? `rgba(255,218,111,${.55 + Math.sin(time * 16) * .25})` : `rgba(255,136,102,${this.flare / 2})`; c.lineWidth = this.flareWarning > 0 ? 5 : 16; if (this.flareWarning > 0) c.setLineDash([14, 12]); c.beginPath(); c.moveTo(68, 0); c.lineTo(330, 0); c.stroke(); c.setLineDash([]); c.restore(); }
    this.particles.forEach(particle => { c.globalAlpha = particle.life; c.fillStyle = particle.color; c.beginPath(); c.arc(particle.x, particle.y, 4, 0, Math.PI * 2); c.fill(); }); c.globalAlpha = 1;
    if (this.pulse > 0) { c.strokeStyle = `rgba(246,211,111,${this.pulse})`; c.lineWidth = 4; c.beginPath(); c.arc(this.moon.x, this.moon.y, 28 + (1 - this.pulse) * 70, 0, Math.PI * 2); c.stroke(); }
    c.save(); c.translate(this.moon.x, this.moon.y); c.rotate(time * 2); c.fillStyle = '#b9f3e3'; c.shadowColor = '#a1e6d6'; c.shadowBlur = 18; c.beginPath(); c.moveTo(0, -17); c.lineTo(14, 0); c.lineTo(0, 17); c.lineTo(-14, 0); c.closePath(); c.fill(); c.restore();
    c.textAlign = 'left'; c.fillStyle = '#f4f0e7'; c.font = '700 29px Space Grotesk'; c.fillText('ORBIT GARDEN', 25, 40); c.fillStyle = '#a1e6d6'; c.font = '14px DM Mono'; c.fillText(`BLOOMS  ${String(this.score).padStart(2, '0')}   COMBO  x${this.combo}`, 28, 68); c.textAlign = 'right'; c.fillStyle = '#f4f0e7'; c.fillText(`SUN ENERGY  ${Math.ceil(this.energy)}%`, W - 24, 39); c.fillStyle = 'rgba(255,255,255,.15)'; c.fillRect(W - 220, 53, 195, 9); c.fillStyle = '#f6d36f'; c.fillRect(W - 220, 53, 195 * this.energy / 100, 9); c.fillStyle = '#d7e9df'; c.font = '14px DM Mono'; c.fillText('[MOVE] GUIDE MOON  •  [TAP] PULSE  •  [R] RESET', W - 22, H - 20); c.textAlign = 'center'; c.fillStyle = this.flareWarning > 0 ? '#ffda6e' : '#fff4bd'; c.font = '16px Space Grotesk'; c.fillText(this.flareWarning > 0 ? 'WARNING: SOLAR FLARE INCOMING' : this.flare > 0 ? 'SOLAR FLARE! DODGE THE ORANGE RAY' : 'COLLECT THE BLOOMS • KEEP THE SUN ALIVE', W / 2, 102);
    if (this.lost) { c.fillStyle = 'rgba(7,19,31,.86)'; c.fillRect(0, 0, W, H); roundedRect(c, 235, 245, 530, 220, 18, '#402438', '#ff9c7a'); c.fillStyle = '#fff4bd'; c.font = '700 52px Space Grotesk'; c.fillText('SUNLIGHT LOST', W / 2, 332); c.fillStyle = '#f5d8d0'; c.font = '18px DM Mono'; c.fillText(`The flare reached the sun after ${this.score} blooms.`, W / 2, 375); c.font = '14px DM Mono'; c.fillText('PRESS R OR USE RESET TO TRY AGAIN', W / 2, 422); }
  }
}

class DrawingGame {
  constructor() { this.reset(); }
  reset() { this.strokes = []; this.activeStroke = null; this.color = '#17211d'; this.size = 10; this.rainbow = false; this.mirror = false; this.totalPoints = 0; }
  pointerDown() {
    const tool = this.toolAt(pointer.x, pointer.y);
    if (tool) { this.useTool(tool); return; }
    if (pointer.y < 92) return;
    this.activeStroke = { color: this.color, size: this.size, points: [] };
    this.addPoint(pointer.x, pointer.y);
  }
  pointerUp() { if (this.activeStroke?.points.length > 1) this.strokes.push(this.activeStroke); this.activeStroke = null; }
  update() { if (this.activeStroke && pointer.down) this.addPoint(pointer.x, pointer.y); }
  addPoint(x, y) {
    if (y < 92) return;
    const point = { x: clamp(x, 18, W - 18), y: clamp(y, 102, H - 18) };
    const points = this.activeStroke.points;
    if (!points.length || distance(point, points[points.length - 1]) > 2) { points.push(point); this.totalPoints++; }
  }
  toolAt(x, y) {
    if (y < 72 && x >= 24 && x <= 238) return 'color';
    if (y < 72 && x >= 258 && x <= 365) return 'sizeDown';
    if (y < 72 && x >= 370 && x <= 477) return 'sizeUp';
    if (y < 72 && x >= 490 && x <= 610) return 'rainbow';
    if (y < 72 && x >= 625 && x <= 735) return 'mirror';
    if (y < 72 && x >= 748 && x <= 839) return 'undo';
    if (y < 72 && x >= 852 && x <= 978) return 'clear';
    return null;
  }
  useTool(tool) {
    if (tool === 'color') this.color = ['#17211d', '#ef6351', '#4c6fff', '#f2b134', '#38a169'][this.strokes.length % 5];
    if (tool === 'sizeDown') this.size = clamp(this.size - 3, 3, 36);
    if (tool === 'sizeUp') this.size = clamp(this.size + 3, 3, 36);
    if (tool === 'rainbow') this.rainbow = !this.rainbow;
    if (tool === 'mirror') this.mirror = !this.mirror;
    if (tool === 'undo') { this.strokes.pop(); this.totalPoints = this.strokes.reduce((sum, stroke) => sum + stroke.points.length, 0); }
    if (tool === 'clear') this.reset();
  }
  draw(c, time) {
    c.fillStyle = '#f7f4ec'; c.fillRect(0, 0, W, H); c.fillStyle = '#fff'; c.fillRect(0, 88, W, H - 88);
    c.strokeStyle = '#e8e2d7'; c.lineWidth = 1; c.beginPath(); c.moveTo(0, 88); c.lineTo(W, 88); c.stroke();
    c.fillStyle = '#17211d'; c.font = '700 22px Space Grotesk'; c.textAlign = 'left'; c.fillText('DRAWING GAME', 24, 31); c.fillStyle = '#758078'; c.font = '12px DM Mono'; c.fillText(`${this.totalPoints} INK POINTS`, 25, 55);
    this.button(c, 258, 16, 101, 42, 'SIZE −', this.size <= 3); this.button(c, 370, 16, 101, 42, 'SIZE +', this.size >= 36); this.button(c, 490, 16, 113, 42, this.rainbow ? 'RAINBOW ON' : 'RAINBOW', this.rainbow); this.button(c, 625, 16, 105, 42, this.mirror ? 'MIRROR ON' : 'MIRROR', this.mirror); this.button(c, 748, 16, 91, 42, 'UNDO', false); this.button(c, 852, 16, 126, 42, 'CLEAR PAGE', false);
    c.fillStyle = this.color; c.beginPath(); c.arc(226, 37, this.size / 2 + 6, 0, Math.PI * 2); c.fill(); [...this.strokes, ...(this.activeStroke ? [this.activeStroke] : [])].forEach(stroke => this.drawStroke(c, stroke, time));
    c.fillStyle = 'rgba(23,33,29,.5)'; c.font = '12px DM Mono'; c.textAlign = 'center'; c.fillText(this.mirror ? 'MIRROR MODE ACTIVE' : 'MAKE A MARK • THEN MAKE ANOTHER', W / 2, H - 14); c.textAlign = 'left';
  }
  button(c, x, y, width, height, label, active) { roundedRect(c, x, y, width, height, 4, active ? '#d8ef63' : '#fff', '#d9d3c7'); c.fillStyle = '#17211d'; c.font = '11px DM Mono'; c.textAlign = 'center'; c.fillText(label, x + width / 2, y + 26); }
  drawStroke(c, stroke, time) {
    const points = stroke.points; if (points.length < 1) return;
    c.save(); c.lineCap = 'round'; c.lineJoin = 'round'; c.lineWidth = stroke.size; c.strokeStyle = this.rainbow ? `hsl(${(time * 80 + points[0].x) % 360} 75% 52%)` : stroke.color; c.beginPath(); c.moveTo(points[0].x, points[0].y); points.slice(1).forEach(point => c.lineTo(point.x, point.y)); c.stroke();
    if (this.mirror && points[0].x !== W / 2) { c.beginPath(); c.moveTo(W - points[0].x, points[0].y); points.slice(1).forEach(point => c.lineTo(W - point.x, point.y)); c.stroke(); } c.restore();
  }
}

function drawMouse(c, point, dragging, time) {
  c.save(); c.translate(point.x, point.y); c.rotate(Math.sin(time * 5) * .04); c.fillStyle = 'rgba(0,0,0,.25)'; c.beginPath(); c.ellipse(0, 33, 43, 11, 0, 0, 7); c.fill();
  c.fillStyle = '#e8edf0'; c.beginPath(); c.ellipse(0, 0, 34, 27, 0, 0, 7); c.fill(); c.fillStyle = '#f39c9c'; c.beginPath(); c.arc(-20, -21, 14, 0, 7); c.arc(20, -21, 14, 0, 7); c.fill(); c.fillStyle = '#26353d'; c.beginPath(); c.arc(13, -5, 4, 0, 7); c.fill(); c.fillStyle = '#ef8a8a'; c.beginPath(); c.arc(32, 3, 6, 0, 7); c.fill(); c.strokeStyle = '#f39c9c'; c.lineWidth = 3; c.beginPath(); c.moveTo(-27, 12); c.bezierCurveTo(-78, 42, -78, -10, -46, 8); c.stroke();
  if (dragging) { c.strokeStyle = '#f8e7a2'; c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 47, 0, 7); c.stroke(); } c.restore();
}

function drawChaseCat(c, point, time) {
  c.save(); c.translate(point.x, point.y); c.rotate(Math.sin(time * 8) * .05); c.fillStyle = 'rgba(0,0,0,.25)'; c.beginPath(); c.ellipse(0, 38, 48, 12, 0, 0, 7); c.fill(); c.fillStyle = '#ef8354'; c.beginPath(); c.ellipse(0, 0, 42, 34, 0, 0, 7); c.fill(); c.beginPath(); c.moveTo(-31, -20); c.lineTo(-36, -59); c.lineTo(-7, -35); c.moveTo(31, -20); c.lineTo(36, -59); c.lineTo(7, -35); c.fill(); c.fillStyle = '#452738'; c.beginPath(); c.arc(-15, -5, 5, 0, 7); c.arc(15, -5, 5, 0, 7); c.fill(); c.fillStyle = '#f7b267'; c.beginPath(); c.arc(0, 8, 6, 0, 7); c.fill(); c.strokeStyle = '#ef8354'; c.lineWidth = 10; c.beginPath(); c.arc(-30, 0, 48, 3.8, 5.6); c.stroke(); c.restore();
}

class BearGame {
  constructor() { this.image = new Image(); this.image.src = 'bear/bear.jpg'; this.reset(); }
  reset() { this.bear = vector(W / 2, 340); this.velocity = vector(0, 0); this.day = 0; this.elapsed = 0; this.nextStrike = 3 + Math.random() * 3; this.strike = 0; this.shock = 0; this.shockTimer = 8; this.targetX = W / 2; this.over = false; this.won = false; }
  update(dt, time) { if (this.over || this.won) return; this.elapsed += dt; this.day = Math.min(6, Math.floor(this.elapsed / 6)); this.nextStrike -= dt; if (this.nextStrike <= 0) { this.strike = 1.5; this.nextStrike = 3 + Math.random() * 3; this.targetX = 120 + Math.random() * 760; } if (this.strike > 0) { this.strike -= dt; if (this.strike < .35 && Math.abs(this.bear.x - this.targetX) < 90) this.over = true; } this.shockTimer -= dt; if (this.shockTimer <= 0 && this.shock <= 0) this.shock = 2.3; if (this.shock > 0) { this.shock -= dt; if (this.shock <= 0) this.shockTimer = 8 + Math.random() * 6; } const wind = vector((keys.a ? -1 : 0) + (keys.d ? 1 : 0), (keys.w ? -1 : 0) + (keys.s ? 1 : 0)); const danger = this.strike > 0 ? (this.targetX - this.bear.x) : 0; this.velocity.x += (pointer.x - this.bear.x) * 10 * dt + wind.x * 2400 * dt + (Math.abs(danger) < 250 ? -Math.sign(danger) * 6000 * dt : 0); this.velocity.y += (pointer.y - this.bear.y) * 10 * dt + wind.y * 2400 * dt + 1600 * dt; this.velocity.x *= .985; this.velocity.y *= .985; this.velocity.x = clamp(this.velocity.x, -1000, 1000); this.velocity.y = clamp(this.velocity.y, -1000, 1000); this.bear.x += this.velocity.x * dt; this.bear.y += this.velocity.y * dt; if (this.bear.y > 625) { this.bear.y = 625; this.velocity.y *= -.18; this.velocity.x *= .86; } this.bear.x = clamp(this.bear.x, 70, 930); if (this.day === 6) this.won = true; }
  draw(c, time) { const shake = this.shock > 0 ? vector(Math.sin(time * 49) * 7, Math.sin(time * 67) * 5) : vector(0, 0); c.save(); c.translate(shake.x, shake.y); c.fillStyle = this.strike > 0 ? '#69798d' : '#a5d8e8'; c.fillRect(0, 0, W, H); c.fillStyle = '#67ae69'; c.fillRect(0, 560, W, 140); c.fillStyle = '#42875e'; c.beginPath(); c.arc(220, 610, 280, Math.PI, 7); c.arc(760, 640, 360, Math.PI, 7); c.fill(); c.fillStyle = '#fff'; c.font = '600 17px Space Grotesk'; c.textAlign = 'center'; c.fillText('KEEP THE BEAR MOVING', W / 2, 116); drawDays(c, this.day); if (this.shock > 0) { c.fillStyle = 'rgba(255,255,255,.18)'; c.fillRect(0, 0, W, H); c.fillStyle = '#fff'; c.font = '700 28px Space Grotesk'; c.fillText('EARTHQUAKE!', W - 140, 116); } if (this.strike > 0) { c.strokeStyle = '#fff06a'; c.lineWidth = 12; c.shadowColor = '#fff'; c.shadowBlur = 22; c.beginPath(); c.moveTo(this.targetX, 75); c.lineTo(this.targetX - 35, 190); c.lineTo(this.targetX + 25, 300); c.lineTo(this.targetX - 20, 430); c.lineTo(this.targetX, 625); c.stroke(); c.shadowBlur = 0; } drawBear(c, this.bear, this.image); if (windDirection()) { drawWind(c, time); } c.restore(); c.fillStyle = '#17211d'; c.textAlign = 'left'; c.font = '500 16px DM Mono'; c.fillText(`DAY ${['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'][this.day]}`, 25, 675); c.textAlign = 'right'; c.fillText('[WASD] WIND  •  [R] RESET', W - 22, 675); if (this.over || this.won) { c.fillStyle = 'rgba(18,22,31,.83)'; c.fillRect(0, 0, W, H); roundedRect(c, 250, 245, 500, 230, 18, this.won ? '#185b43' : '#281f2a', this.won ? '#8ff09a' : '#ff715b'); c.textAlign = 'center'; c.fillStyle = '#fff'; c.font = '700 57px Space Grotesk'; c.fillText(this.won ? 'YOU WIN!' : 'GAME OVER', 500, 325); c.font = '20px Space Grotesk'; c.fillText(this.won ? 'The bear reached Sunday.' : 'The bear was hit by lightning.', 500, 372); c.font = '500 14px DM Mono'; c.fillText('PRESS R OR USE RESET TO PLAY AGAIN', 500, 425); } }
}

function windDirection() { return (keys.w || keys.a || keys.s || keys.d) ? vector((keys.a ? -1 : 0) + (keys.d ? 1 : 0), (keys.w ? -1 : 0) + (keys.s ? 1 : 0)) : null; }
function drawWind(c, time) { const wind = windDirection(); c.save(); c.strokeStyle = 'rgba(235,250,255,.62)'; c.lineWidth = 4; for (let index = 0; index < 18; index++) { const x = (index * 157 + time * 430 * wind.x) % (W + 200) - 100; const y = (index * 83 + time * 430 * wind.y) % (H + 200) - 100; const length = 45 + index % 4 * 12; c.beginPath(); c.moveTo(x, y); c.lineTo(x - wind.x * length, y - wind.y * length); c.stroke(); } c.fillStyle = '#235578'; c.font = '700 22px Space Grotesk'; c.textAlign = 'left'; c.fillText(`WIND ${wind.y < 0 ? 'UP' : wind.y > 0 ? 'DOWN' : ''}${wind.x ? (wind.y ? ' + ' : '') + (wind.x < 0 ? 'LEFT' : 'RIGHT') : ''}`, 24, 116); c.restore(); }

function drawDays(c, active) { const days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']; roundedRect(c, 20, 18, 960, 59, 12, 'rgba(25,35,55,.78)'); days.forEach((day, index) => { const x = 31 + index * 135; roundedRect(c, x, 26, 126, 43, 8, index === active ? '#ffe04e' : '#eff3f5'); c.fillStyle = index === active ? '#17211d' : '#34414b'; c.font = '700 16px Space Grotesk'; c.textAlign = 'center'; c.fillText(day, x + 63, 53); if (index === 4 && index === active) { c.fillStyle = '#8f5c00'; c.font = '10px DM Mono'; c.fillText('THUNDER', x + 63, 65); } }); }
function drawBear(c, point, image) { if (image.complete && image.naturalWidth) { c.drawImage(image, point.x - 82, point.y - 112, 165, 165); return; } c.fillStyle = '#6d4738'; c.beginPath(); c.arc(point.x, point.y, 62, 0, 7); c.fill(); c.fillStyle = '#f8d5a4'; c.beginPath(); c.arc(point.x, point.y + 8, 40, 0, 7); c.fill(); c.fillStyle = '#17211d'; c.beginPath(); c.arc(point.x - 20, point.y - 10, 6, 0, 7); c.arc(point.x + 20, point.y - 10, 6, 0, 7); c.fill(); }