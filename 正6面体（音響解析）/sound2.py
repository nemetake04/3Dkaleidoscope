import sys
import numpy as np
import sounddevice as sd
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets
import librosa
import socket

# --- UDP設定 ---
UDP_IP = "192.168.0.148" # ArduinoのIPアドレスに書き換え
UDP_PORT = 5005

# --- 解析設定 ---
CHUNK = 2048
RATE = 44100

class UdpAudioAnalyzer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UDP Smooth Audio to LED")
        self.resize(1000, 600)

        # UDPソケットの作成
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 滑らかさの設定
        self.alpha = 0.15
        self.smooth_db = -60.0
        self.smooth_pitch = 0.0

        self.db_history = np.zeros(100)
        self.pitch_history = np.zeros(100)
        self.current_frame = np.zeros(CHUNK)

        self.init_ui()

        # 音声ストリーム
        self.stream = sd.InputStream(samplerate=RATE, channels=1, blocksize=CHUNK, callback=self.audio_callback)
        self.stream.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_all)
        self.timer.start(30)

    def init_ui(self):
        self.central_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.central_widget)
        
        self.db_plot = pg.PlotWidget(title="Volume (dB)")
        self.db_plot.setYRange(-60, 0)
        self.db_curve = self.db_plot.plot(pen='y')
        self.central_widget.addTab(self.db_plot, "Volume")

        self.pitch_plot = pg.PlotWidget(title="Pitch (Hz)")
        self.pitch_plot.setYRange(0, 2000)
        self.pitch_curve = self.pitch_plot.plot(pen='g')
        self.central_widget.addTab(self.pitch_plot, "Pitch")

        self.spec_plot = pg.PlotWidget(title="Spectrum")
        self.spec_curve = self.spec_plot.plot(pen='c')
        self.central_widget.addTab(self.spec_plot, "Spectrum")

    def audio_callback(self, indata, frames, time, status):
        self.current_frame = indata[:, 0]

    def update_all(self):
        y = self.current_frame
        if np.max(np.abs(y)) < 1e-4: return

        # 音量解析
        rms = np.sqrt(np.mean(y**2)) + 1e-9
        db = 20 * np.log10(rms)
        self.smooth_db = (self.alpha * db) + ((1 - self.alpha) * self.smooth_db)
        self.db_curve.setData(np.roll(self.db_history, -1)) # 簡易表示更新
        self.db_history = np.roll(self.db_history, -1); self.db_history[-1] = self.smooth_db

        # ピッチ解析
        pitches, magnitudes = librosa.piptrack(y=y, sr=RATE, n_fft=CHUNK)
        raw_pitch = pitches[magnitudes[:, 0].argmax(), 0]
        if 50 < raw_pitch < 2000:
            self.smooth_pitch = (self.alpha * raw_pitch) + ((1 - self.alpha) * self.smooth_pitch)
        self.pitch_history = np.roll(self.pitch_history, -1); self.pitch_history[-1] = self.smooth_pitch
        self.pitch_curve.setData(self.pitch_history)

        # スペクトラム
        self.spec_curve.setData(np.abs(np.fft.rfft(y)))

        # --- UDP送信 ---
        s_db = int(np.clip(self.smooth_db, -60, 0))
        s_pitch = int(np.clip(self.smooth_pitch, 0, 2000))
        message = f"{s_db},{s_pitch}"
        try:
            self.sock.sendto(message.encode(), (UDP_IP, UDP_PORT))
        except:
            pass

    def closeEvent(self, event):
        self.stream.stop()
        self.sock.close()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = UdpAudioAnalyzer()
    window.show()
    sys.exit(app.exec())