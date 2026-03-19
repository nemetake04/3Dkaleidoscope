import numpy as np
import sounddevice as sd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from collections import deque
import threading
import socket
import time

# --- 設定 ---
FS = 44100
BLOCKSIZE = 1024 
HISTORY = 100
SMOOTH_WINDOW = 3 

UDP_IP = "192.168.0.150"   # ArduinoのIPアドレス
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

value = 0

# 履歴データ
pitch_hist = deque([0.0]*HISTORY, maxlen=HISTORY)
vol_hist   = deque([-80.0]*HISTORY, maxlen=HISTORY)
bright_hist = deque([0.0]*HISTORY, maxlen=HISTORY)
temp_pitches = deque([0.0]*SMOOTH_WINDOW, maxlen=SMOOTH_WINDOW)

audio_buffer = np.zeros(BLOCKSIZE)
new_data = False
lock = threading.Lock()

def callback(indata, frames, time, status):
    global audio_buffer, new_data
    with lock:
        audio_buffer = indata[:, 0].copy()
        new_data = True

def analyze_stable(audio):
    rms = np.sqrt(np.mean(audio**2)) + 1e-12
    db = 20 * np.log10(rms)
    if rms < 0.005: return 0, db, 0

    sig = audio - np.mean(audio)
    windowed = sig * np.hanning(len(sig))

    # ピッチ検出（自己相関 + 放物線補間）
    corr = np.correlate(windowed, windowed, mode='full')[len(windowed)-1:]
    d = np.diff(corr)
    valleys = np.where(d > 0)[0]
    
    if len(valleys) > 0:
        peak_idx = np.argmax(corr[valleys[0]:]) + valleys[0]
        if 0 < peak_idx < len(corr) - 1:
            y1, y2, y3 = corr[peak_idx-1], corr[peak_idx], corr[peak_idx+1]
            denom = (2 * y2 - y1 - y3)
            adj = (y3 - y1) / (2 * denom) if abs(denom) > 1e-12 else 0
            precise_peak = peak_idx + adj
        else:
            precise_peak = peak_idx
        pitch = FS / precise_peak if precise_peak > 0 else 0
    else:
        pitch = 0
    
    # スペクトル重心（明るさ）
    spec = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(audio), 1/FS)
    centroid = np.sum(freqs * spec) / (np.sum(spec) + 1e-12)

    return pitch, db, centroid

# ===== RGB モニター用 =====
plt.ion()
rgb_fig = plt.figure(4, figsize=(4, 3))
rgb_ax = rgb_fig.add_subplot(111)
rgb_bars = rgb_ax.bar(["R Hz", "G dB", "B 線形スペクトラム"], [0, 0, 0])
rgb_ax.set_ylim(0, 255)
rgb_ax.set_title("LED Output (0–255)")


# --- ウィンドウ設定 ---
plt.ion()
figs = [plt.figure(i+1, figsize=(6, 4)) for i in range(3)]
axes = [f.add_subplot(111) for f in figs]
lines = []
colors = ['cyan', 'magenta', 'yellow']
titles = ["Pitch (Hz)", "Volume (dB)", "Brightness (Hz)"]

# Y軸の範囲設定
# PitchとBrightnessは 20Hz - 20,000Hz の対数表示にする
ylims = [(20, 20000), (-80, 0), (20, 20000)]

for i, ax in enumerate(axes):
    l, = ax.plot(range(HISTORY), [20 if i != 1 else -80]*HISTORY, color=colors[i], lw=2)
    lines.append(l)
    ax.set_title(titles[i])
    ax.set_ylim(ylims[i])
    ax.grid(True, which='both', alpha=0.3)
    
    # 1番目(Pitch)と3番目(Brightness)を対数スケールに設定
    if i == 0 or i == 2:
        ax.set_yscale('log')
        ax.set_yticks([20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000])
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

try:
    with sd.InputStream(channels=1, samplerate=FS, blocksize=BLOCKSIZE, callback=callback):
        while all(plt.fignum_exists(f.number) for f in figs):
            if new_data:
                with lock:
                    data = audio_buffer.copy()
                    new_data = False

                p, v, b = analyze_stable(data)

                if p > 0:
                    temp_pitches.append(p)
                    stable_p = sum(temp_pitches) / len(temp_pitches)
                else:
                    stable_p = pitch_hist[-1]

                pitch_hist.append(max(20, min(stable_p, 20000)))
                vol_hist.append(v)
                bright_hist.append(max(20, min(b, 20000)))

                # ===== グラフY軸 → RGB 完全一致変換 =====

            # ===== 画面の見た目基準 RGB変換 =====

                # ---- Pitch（対数軸 20–20000 Hz）----
                p_min, p_max = 20, 20000
                p_log = np.log10(np.clip(stable_p, p_min, p_max))
                p_log_min = np.log10(p_min)
                p_log_max = np.log10(p_max)
                r = int(np.clip((p_log - p_log_min) / (p_log_max - p_log_min) * 255, 0, 255))


                # ---- Volume（線形軸 -80–0 dB）----
                v_min, v_max = -80, 0
                g = int(np.clip((v - v_min) / (v_max - v_min) * 255, 0, 255))


                # ---- Brightness（対数軸 20–20000 Hz）----
                b_min, b_max = 20, 20000
                b_log = np.log10(np.clip(b, b_min, b_max))
                b_log_min = np.log10(b_min)
                b_log_max = np.log10(b_max)
                bl = int(np.clip((b_log - b_log_min) / (b_log_max - b_log_min) * 255, 0, 255))


                msg = f"{r},{g},{bl}"
                sock.sendto(msg.encode("utf-8"), (UDP_IP, UDP_PORT))

                print(f"LED -> R:{r:3d} G:{g:3d} B:{bl:3d}")

                # ===== RGB モニター =====
                rgb_bars[0].set_height(r)
                rgb_bars[1].set_height(g)
                rgb_bars[2].set_height(bl)

                rgb_bars[0].set_color((r/255, 0, 0))
                rgb_bars[1].set_color((0, g/255, 0))
                rgb_bars[2].set_color((0, 0, bl/255))

                rgb_fig.canvas.draw_idle()

                # ===== グラフ描画 =====
                lines[0].set_ydata(list(pitch_hist))
                lines[1].set_ydata(list(vol_hist))
                lines[2].set_ydata(list(bright_hist))

                axes[0].set_title(f"Pitch: {stable_p:.1f} Hz")

                for f in figs:
                    f.canvas.draw_idle()
                plt.pause(0.01)

except Exception as e:
    print("全体エラー:", e)
