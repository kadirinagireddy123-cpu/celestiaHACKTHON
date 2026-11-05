// Text-to-speech (server audio with browser fallback) and speech recognition.
export class Speaker {
  constructor(api, getPrefs) {
    this.api = api; this.getPrefs = getPrefs;
    this.audio = null; this.token = 0;
  }
  stop() {
    this.token++;
    try { speechSynthesis.cancel(); } catch {}
    if (this.audio) { this.audio.pause(); this.audio = null; }
  }
  async speak(text, { interrupt = true } = {}) {
    if (!text) return;
    const p = this.getPrefs();
    if (interrupt) this.stop();
    const my = ++this.token;
    if (p.engine === 'server') {
      try {
        const r = await this.api.tts({ text, language: p.language, voice: p.voice });
        if (my !== this.token) return;
        const d = r.data;
        if (!d.useBrowserFallback && d.audioData) {
          await this.#playAudio(`data:${d.audioMimeType || 'audio/mp3'};base64,${d.audioData}`, p.rate, my);
          return;
        }
        if (d.speechConfig) return this.#browserSpeak(d.speechConfig.text, d.speechConfig.lang, p, my);
      } catch { /* fall through to device voice */ }
      if (my !== this.token) return;
    }
    return this.#browserSpeak(text, p.bcp47, p, my);
  }
  #playAudio(src, rate, my) {
    return new Promise((resolve) => {
      const a = new Audio(src);
      a.playbackRate = Math.min(rate, 1.5);
      this.audio = a;
      a.onended = a.onerror = () => resolve();
      a.play().catch(() => resolve());
    });
  }
  #browserSpeak(text, lang, p, my) {
    return new Promise((resolve) => {
      if (!('speechSynthesis' in window)) return resolve();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang; u.rate = p.rate; u.pitch = 1; u.volume = 1;
      const voices = speechSynthesis.getVoices();
      const base = lang.split('-')[0];
      let cand = voices.filter(v => v.lang && v.lang.toLowerCase().startsWith(base));
      if (p.voice === 'female') cand = cand.filter(v => /female|woman|zira|samantha|google.*(uk|us)/i.test(v.name)).concat(cand);
      if (p.voice === 'male') cand = cand.filter(v => /\bmale\b|man|david|daniel|alex/i.test(v.name)).concat(cand);
      if (cand[0]) u.voice = cand[0];
      u.onend = u.onerror = () => resolve();
      if (my === this.token) speechSynthesis.speak(u); else resolve();
    });
  }
}

export const recognitionSupported = () => !!(window.SpeechRecognition || window.webkitSpeechRecognition);

// One-shot dictation. Returns a promise of the transcript ('' if nothing heard).
export function listen(bcp47, { onInterim } = {}) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  return new Promise((resolve, reject) => {
    if (!SR) return reject(new Error('Voice input is not supported in this browser. Try Chrome or Edge, or type instead.'));
    const rec = new SR();
    rec.lang = bcp47; rec.interimResults = true; rec.maxAlternatives = 1; rec.continuous = false;
    let finalText = '';
    rec.onresult = (e) => {
      let interim = '';
      for (const r of e.results) { if (r.isFinal) finalText += r[0].transcript; else interim += r[0].transcript; }
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
