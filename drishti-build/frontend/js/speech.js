// Text-to-speech (server gTTS audio with browser fallback), earcons/chimes, and voice assistant.

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
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.18);
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.start(now);
      osc.stop(now + 0.35);
    } else if (type === 'listen') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now);
      osc.stop(now + 0.22);
    } else if (type === 'success') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(783.99, now + 0.08);
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    } else if (type === 'stop') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(750, now);
      osc.frequency.exponentialRampToValueAtTime(350, now + 0.18);
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    } else if (type === 'hazard') {
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
    if (this.audio) {
      try { this.audio.pause(); } catch {}
      this.audio = null;
    }
  }

  async speak(text, { interrupt = true } = {}) {
    if (!text) return;
    const p = this.getPrefs();
    if (interrupt) this.stop();
    const my = ++this.token;
    this.speaking = true;

    // 1. Primary: Server-side gTTS audio (native Kannada, Hindi, Telugu, Tamil, English, etc.)
    try {
      const r = await this.api.tts({
        text,
        language: p.language || 'en',
        voice: p.voice || 'neutral',
      });
      if (my !== this.token) return;
      const d = r?.data;
      if (d && d.audioData) {
        await this.#playAudio(`data:${d.audioMimeType || 'audio/mp3'};base64,${d.audioData}`, p.rate, my);
        if (my === this.token) this.speaking = false;
        return;
      }
    } catch (err) {
      console.warn('Server TTS failed, falling back to browser voice:', err);
    }

    if (my !== this.token) return;

    // 2. Fallback: Browser Web Speech API
    await this.#browserSpeak(text, p.bcp47, p, my);
    if (my === this.token) this.speaking = false;
  }

  #playAudio(src, rate, my) {
    return new Promise((resolve) => {
      try {
        const a = new Audio();
        a.src = src;
        a.playbackRate = Math.min(rate || 1.0, 1.5);
        this.audio = a;

        a.onended = () => {
          if (my === this.token) this.speaking = false;
          resolve();
        };

        a.onerror = (e) => {
          console.warn('Audio element error:', e);
          if (my === this.token) this.speaking = false;
          resolve();
        };

        const playPromise = a.play();
        if (playPromise !== undefined) {
          playPromise.catch((err) => {
            console.warn('Audio autoplay blocked by browser or failed:', err);
            if (my === this.token) this.speaking = false;
            resolve();
          });
        }
      } catch (err) {
        console.warn('Could not play audio:', err);
        if (my === this.token) this.speaking = false;
        resolve();
      }
    });
  }

  #browserSpeak(text, lang, p, my) {
    return new Promise((resolve) => {
      if (!('speechSynthesis' in window)) {
        if (my === this.token) this.speaking = false;
        return resolve();
      }
      try {
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        u.rate = p.rate || 1.0;
        u.pitch = 1;
        u.volume = 1;
        const voices = speechSynthesis.getVoices();
        const base = (lang || 'en').split('-')[0].toLowerCase();
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
      } catch {
        if (my === this.token) this.speaking = false;
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
