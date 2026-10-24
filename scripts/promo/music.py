"""Originalna čiptjun muzika za promo klip (~29.7 s), snima music.wav."""
import numpy as np, wave, os

SR = 44100
DUR = 891 / 30
BPM = 128
B = 60 / BPM          # trajanje jedne dobe
N = int(SR * DUR)
mix = np.zeros(N)

def hz(n):            # MIDI broj -> Hz
    return 440 * 2 ** ((n - 69) / 12)

def env(n, a=0.005, r=0.08):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a)
    tail = int(r * SR)
    if n > tail:
        e[-tail:] *= np.linspace(1, 0, tail)
    return e

def tone(start, beats, note, vol, kind='sq', duty=0.25):
    if note is None: return
    s = int(start * SR); n = int(beats * B * SR * 0.92)
    if s >= N: return
    n = min(n, N - s)
    t = np.arange(n) / SR; f = hz(note)
    ph = (t * f) % 1
    if kind == 'sq':  w = np.where(ph < duty, 1.0, -1.0)
    elif kind == 'tri': w = 4 * np.abs(ph - 0.5) - 1
    else: w = np.sin(2 * np.pi * f * t)
    mix[s:s + n] += w * env(n) * vol

def hat(start, vol=0.05, length=0.04):
    s = int(start * SR); n = int(length * SR)
    if s + n >= N: return
    mix[s:s + n] += np.random.uniform(-1, 1, n) * np.linspace(1, 0, n) ** 2 * vol

def kick(start, vol=0.35):
    s = int(start * SR); n = int(0.12 * SR)
    if s + n >= N: return
    t = np.arange(n) / SR; f = 120 * np.exp(-t * 30) + 45
    mix[s:s + n] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18) * vol

C, D, E, F, G, A, Bb, H = 60, 62, 64, 65, 67, 69, 70, 71
# originalna melodija (u C-duru): (nota ili None, trajanje u dobama)
theme = [(G,0.5),(C+12,0.5),(H,0.5),(C+12,0.5),(E+12,1),(D+12,0.5),(C+12,0.5),
         (A,0.5),(C+12,0.5),(D+12,0.5),(E+12,0.5),(D+12,1.5),(None,0.5),
         (F,0.5),(A,0.5),(C+12,0.5),(A,0.5),(G,1),(E,0.5),(G,0.5),
         (A,0.5),(G,0.5),(F,0.5),(D,0.5),(C,1.5),(None,0.5)]
bass_prog = [C-24, A-36, F-36, G-36]   # C, Am, F, G (po jedan takt)
chords = {C-24:[C,E,G], A-36:[A-12,C,E], F-36:[F-12,A-12,C], G-36:[G-12,H-12,D]}

t0 = 3.0                 # muzika "kreće" kad počne igra (posle naslova)
# uvod: arpeđo C-dur
for i,n in enumerate([C,E,G,C+12,E+12,G+12,C+12,G,E,C,E,G]):
    tone(i * B / 2 * 1.0, 0.5, n, 0.10, 'sq', 0.5)
tone(2.4, 1.2, C+12, 0.10, 'sq', 0.5)

bars = int((DUR - 2.8 - t0) / (4 * B))
t = t0
for bar in range(bars):
    root = bass_prog[bar % 4]
    for beat in range(4):
        tone(t + beat * B, 0.9, root + (12 if beat % 2 else 0), 0.22, 'tri')
        kick(t + beat * B, 0.25 if beat % 2 == 0 else 0.15)
        hat(t + beat * B + B / 2)
        for k, cn in enumerate(chords[root]):
            tone(t + beat * B + B / 2, 0.4, cn, 0.035, 'sq', 0.5)
    t += 4 * B
# melodija preko pratnje (ponavlja se)
mt = t0; i = 0
while mt < t - 0.01:
    n, d = theme[i % len(theme)]
    tone(mt, d, n, 0.11, 'sq', 0.25)
    tone(mt, d, None if n is None else n - 12, 0.0, 'sq')
    mt += d * B; i += 1
# završna fanfara + akord
end = t
for k, n in enumerate([G, C+12, E+12, G+12]):
    tone(end + k * 0.14, 0.4, n, 0.12, 'sq', 0.25)
for n in [C, E, G, C+12]:
    tone(end + 0.6, 4.5, n, 0.07, 'sq', 0.5)
tone(end + 0.6, 4.5, C-24, 0.25, 'tri')
kick(end + 0.6, 0.35)

# blago zatamnjenje na kraju i normalizacija
fade = int(1.2 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
mix = np.tanh(mix * 1.2) * 0.85
pcm = (mix * 32767).astype(np.int16)
with wave.open(os.path.join(os.path.dirname(__file__), 'music.wav'), 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', round(DUR, 2), 's, bars', bars, 'end at', round(end, 2))
