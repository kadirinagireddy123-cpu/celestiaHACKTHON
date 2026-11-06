// Text-to-speech (server audio with browser fallback), earcons/chimes, and voice assistant.

let audioCtx = null;
function getAudioCtx() {
  if (!audioCtx) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (AC) audioCtx = new AC();
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume().catch(() => {});
  }
  return audioCtx;
}

// Earcon auditory chimes for blind accessibility
export function playChime(type = 'listen') {
  try {
    const ctx = getAudioCtx();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    if (type === 'start') {
      // Ascending chord for startup
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.18);
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.start(now);
      osc.stop(now + 0.35);
    } else if (type === 'listen') {
      // Soft prompt beep
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, now); // D5
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.12); // A5
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now);
      osc.stop(now + 0.22);
    } else if (type === 'success') {
      // Pleasant double ping
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(783.99, now + 0.08);
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    } else if (type === 'stop') {
      // Descending tone
      osc.type = 'sine';
      osc.frequency.setValueAtTime(750, now);
      osc.frequency.exponentialRampToValueAtTime(350, now + 0.18);
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    } else if (type === 'hazard') {
      // Warning buzz
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.setValueAtTime(440, now + 0.1);
      osc.frequency.setValueAtTime(880, now + 0.2);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.start(now);
      osc.stop(now + 0.35);
    }
  } catch {}
}

export class Speaker {
  constructor(api, getPrefs) {
    this.api = api;
    this.getPrefs = getPrefs;
    this.audio = null;
    this.token = 0;
    this.speaking = false;
  }

  isSpeaking() {
    return this.speaking || (typeof window !== 'undefined' && !!window.speechSynthesis?.speaking);
  }

  stop() {
    this.token++;
    this.speaking = false;
    try { speechSynthesis.cancel(); } catch {}
    if (this.audio) { this.audio.pause(); this.audio = null; }
  }

  async speak(text, { interrupt = true } = {}) {
    if (!text) return;
    const p = this.getPrefs();
    if (interrupt) this.stop();
    const my = ++this.token;
    this.speaking = true;

    if (p.engine === 'server') {
      try {
        const r = await this.api.tts({ text, language: p.language, voice: p.voice });
        if (my !== this.token) return;
        const d = r.data;
        if (!d.useBrowserFallback && d.audioData) {
          await this.#playAudio(`data:${d.audioMimeType || 'audio/mp3'};base64,${d.audioData}`, p.rate, my);
          if (my === this.token) this.speaking = false;
          return;
        }
        if (d.speechConfig) {
          await this.#browserSpeak(d.speechConfig.text, d.speechConfig.lang, p, my);
          if (my === this.token) this.speaking = false;
          return;
        }
      } catch { /* fall through to device voice */ }
      if (my !== this.token) return;
    }
    await this.#browserSpeak(text, p.bcp47, p, my);
    if (my === this.token) this.speaking = false;
  }

  #playAudio(src, rate, my) {
    return new Promise((resolve) => {
      const a = new Audio(src);
      a.playbackRate = Math.min(rate, 1.5);
      this.audio = a;
      a.onended = a.onerror = () => {
        if (my === this.token) this.speaking = false;
        resolve();
      };
      a.play().catch(() => {
        if (my === this.token) this.speaking = false;
        resolve();
      });
    });
  }

  #browserSpeak(text, lang, p, my) {
    return new Promise((resolve) => {
      if (!('speechSynthesis' in window)) {
        if (my === this.token) this.speaking = false;
        return resolve();
      }
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang;
      u.rate = p.rate;
      u.pitch = 1;
      u.volume = 1;
      const voices = speechSynthesis.getVoices();
      const base = lang.split('-')[0];
      let cand = voices.filter(v => v.lang && v.lang.toLowerCase().startsWith(base));
      if (p.voice === 'female') cand = cand.filter(v => /female|woman|zira|samantha|google.*(uk|us)/i.test(v.name)).concat(cand);
      if (p.voice === 'male') cand = cand.filter(v => /\bmale\b|man|david|daniel|alex/i.test(v.name)).concat(cand);
      if (cand[0]) u.voice = cand[0];
      u.onend = u.onerror = () => {
        if (my === this.token) this.speaking = false;
        resolve();
      };
      if (my === this.token) {
        speechSynthesis.speak(u);
      } else {
        resolve();
      }
    });
  }
}

export const recognitionSupported = () => !!(window.SpeechRecognition || window.webkitSpeechRecognition);

// One-shot dictation. Returns a promise of the transcript ('' if nothing heard).
export function listen(bcp47, { onInterim } = {}) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  return new Promise((resolve, reject) => {
    if (!SR) return reject(new Error('Voice input is not supported in this browser. Try Chrome or Edge.'));
    const rec = new SR();
    rec.lang = bcp47;
    rec.interimResults = true;
    rec.maxAlternatives = 1;
    rec.continuous = false;
    let finalText = '';
    rec.onresult = (e) => {
      let interim = '';
      for (const r of e.results) {
        if (r.isFinal) finalText += r[0].transcript;
        else interim += r[0].transcript;
      }
      onInterim?.(finalText || interim);
    };
    rec.onerror = (e) => {
      if (e.error === 'no-speech' || e.error === 'aborted') return resolve('');
      reject(new Error(e.error === 'not-allowed' ? 'Microphone permission was denied.' : `Voice input error: ${e.error}`));
    };
    rec.onend = () => resolve(finalText.trim());
    try { rec.start(); } catch (e) { reject(e); }
  });
}
