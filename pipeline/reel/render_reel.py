"""Render a vertical 1080x1920 reel (mp4, H.264 + AAC) from a JSON spec.
Usage: python3 render_reel.py reel.json OUT.mp4 [--tts DIR]
--tts DIR: folder with kokoro.onnx + voices-v1.0.bin (kokoro-onnx, Apache-2.0,
github.com/thewh1teagle/kokoro-onnx releases). Without it the reel is silent.
Spec: {"tag","hook","pre","bad","good","post","ru","ex","exhl","exru",
       "say":[line under the card, example], "voice":"af_heart",
       "bg":"#FF8A4C","lattice":"#F0533A","end_title","end_note","end_cta"}
"""
import json, sys, os, subprocess, tempfile, pathlib, math, struct, wave
HERE = pathlib.Path(__file__).parent
FPS, SR = 30, 24000

def lattice(c):
    c = c.replace('#', '%23')
    return ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='280'%3E"
            f"%3Cpath d='M0 0 L180 280 M180 0 L0 280' stroke='{c}' stroke-width='9'/%3E%3C/svg%3E\")")

def tts(lines, voice, d):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(d, 'kokoro.onnx'), os.path.join(d, 'voices-v1.0.bin'))
    out = []
    for t in lines:
        a, sr = k.create(t, voice=voice, speed=0.92, lang='en-us' if voice[0] == 'a' else 'en-gb')
        assert sr == SR
        out.append(list(a))
    return out

def pop(freq=660, dur=0.12, vol=0.25):
    n = int(SR * dur)
    return [vol * math.sin(2 * math.pi * freq * i / SR * (1 + 0.6 * i / n)) * math.exp(-8 * i / n) for i in range(n)]

def whoosh(dur=0.3, vol=0.12):
    import random; random.seed(1); n = int(SR * dur); prev = 0; s = []
    for i in range(n):
        prev = 0.85 * prev + 0.15 * random.uniform(-1, 1)
        s.append(vol * prev * math.sin(math.pi * i / n) * 3)
    return s

def main(spec_path, out_mp4, tts_dir=None):
    S = json.load(open(spec_path))
    voice = tts(S['say'], S.get('voice', 'af_heart'), tts_dir) if tts_dir else [[0.0] * int(SR * 1.3), [0.0] * int(SR * 2.8)]
    v1, v2 = len(voice[0]) / SR, len(voice[1]) / SR
    T = {'hook': 0.35, 'card': 1.5, 'strike': 2.5, 'good': 3.2}
    T['say1'] = T['good'] + 0.35
    T['ru'] = T['say1'] + 0.3
    T['example'] = T['say1'] + v1 + 1.0
    T['say2'] = T['example'] + 0.7
    T['hl'], T['hlDur'] = T['say2'] + 0.2, max(0.6, v2 * 0.6)
    T['end'] = T['say2'] + v2 + 1.0
    dur = round(T['end'] + 3.2, 2)
    # audio mix
    mix = [0.0] * int(SR * dur)
    def put(a, at):
        o = int(at * SR)
        for i, x in enumerate(a):
            if o + i < len(mix): mix[o + i] += x
    put(whoosh(), T['card'] - 0.05); put(pop(300, 0.18, 0.35), T['strike'])
    put(pop(880, 0.12, 0.18), T['good']); put(whoosh(), T['example']); put(pop(660), T['end'] + 0.3)
    put(voice[0], T['say1']); put(voice[1], T['say2'])
    peak = max(1e-6, max(abs(x) for x in mix)); g = min(1.0, 0.95 / peak)
    work = tempfile.mkdtemp(prefix='reel-')
    with wave.open(os.path.join(work, 'a.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, x * g)) * 32767)) for x in mix))
    # page
    h = (HERE / 'reel.html').read_text()
    ex_html = S['ex'].replace(S['exhl'], f'<span class="hl">{S["exhl"]}</span>', 1)
    for k in ('tag', 'hook', 'pre', 'bad', 'good', 'post', 'ru', 'exru', 'end_title', 'end_note', 'end_cta'):
        h = h.replace('{{%s}}' % k, S[k].replace('\n', '<br>'))
    h = h.replace('{{ex_html}}', ex_html).replace('{{timeline}}', json.dumps(T))
    h = h.replace('</style>', ':root{--bg:%s;--lattice:%s}</style>' % (S.get('bg', '#FF8A4C'), lattice(S.get('lattice', '#F0533A'))), 1)
    page = HERE / '_page.html'; page.write_text(h)
    frames = os.path.join(work, 'f'); os.makedirs(frames)
    subprocess.run(['node', str(HERE / 'frames.js'), str(page), frames, str(dur), str(FPS)], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, '%05d.jpg'),
                    '-i', os.path.join(work, 'a.wav'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                    '-crf', '18', '-r', str(FPS), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-shortest',
                    '-movflags', '+faststart', out_mp4], check=True)
    page.unlink()
    print(out_mp4, dur, 's', json.dumps(T))

if __name__ == '__main__':
    a = sys.argv[1:]; d = None
    if '--tts' in a: i = a.index('--tts'); d = a[i + 1]; del a[i:i + 2]
    main(a[0], a[1], d)
