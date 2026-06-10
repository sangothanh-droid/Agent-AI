const canvas = document.getElementById('bgCanvas');
const ctx = canvas.getContext('2d');

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resize();
window.addEventListener('resize', resize);

const KANJI = '忍死闇暁血刃鬼影炎剣魂怨滅封術呪縛幻煉獄冥邪鎖憎怒恨殺暗裂崩壊滅亡爆炸轟';
const fontSize = 18;

function makeDrops() {
  const cols = Math.floor(canvas.width / fontSize);
  return Array.from({length: cols}, () => ({
    y: Math.random() * -canvas.height,
    speed: Math.random() * 1.5 + 0.4,
    bright: Math.random() > 0.97,
    len: Math.floor(Math.random() * 15 + 5),
    opacity: Math.random() * 0.4 + 0.2,
    chars: Array.from({length: 30}, () => KANJI[Math.floor(Math.random() * KANJI.length)]),
  }));
}

let drops = makeDrops();
window.addEventListener('resize', () => { drops = makeDrops(); });

function animate() {
  ctx.fillStyle = 'rgba(10,0,0,0.07)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const cols = Math.floor(canvas.width / fontSize);
  drops.forEach((drop, i) => {
    if (i >= cols) return;
    const col = i * fontSize;
    const steps = Math.floor(drop.y / fontSize);

    for (let j = 0; j < drop.len; j++) {
      const row = steps - j;
      if (row < 0) continue;
      const py = row * fontSize;
      if (py > canvas.height) continue;
      const ratio = 1 - j / drop.len;
      const char = drop.chars[(row + j) % drop.chars.length];

      if (j === 0 && drop.bright) {
        ctx.fillStyle = `rgba(255,200,200,${ratio})`;
      } else if (j === 0) {
        ctx.fillStyle = `rgba(255,60,60,${ratio * drop.opacity})`;
      } else if (j < 3) {
        ctx.fillStyle = `rgba(200,20,20,${ratio * drop.opacity * 0.9})`;
      } else {
        ctx.fillStyle = `rgba(100,0,0,${ratio * drop.opacity * 0.6})`;
      }

      ctx.font = `${fontSize}px monospace`;
      ctx.fillText(char, col, py);

      if (Math.random() < 0.015) {
        drop.chars[(row + j) % drop.chars.length] = KANJI[Math.floor(Math.random() * KANJI.length)];
      }
    }

    drop.y += drop.speed;
    if (drop.y > canvas.height + drop.len * fontSize) {
      drop.y = Math.random() * -200;
      drop.speed = Math.random() * 1.5 + 0.4;
      drop.bright = Math.random() > 0.97;
      drop.len = Math.floor(Math.random() * 15 + 5);
    }
  });

  requestAnimationFrame(animate);
}

animate();
