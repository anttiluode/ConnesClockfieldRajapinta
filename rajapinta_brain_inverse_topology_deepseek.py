"""
Brain Manifold Viewer — Rajapinta Inverse Projection
=====================================================
Live EEG → Takens Phase Space → Resonator Bank → Moiré Manifold
with FREQUENCY TARGETING (Graphical EQ for brain waves)

PerceptionLab, Helsinki 2026

Usage:
    python brain_manifold_viewer.py

Dependencies:
    pip install mne scipy matplotlib numpy
"""

import sys
import warnings
import traceback
warnings.filterwarnings('ignore')

import numpy as np

import tkinter as tk
from tkinter import filedialog, ttk

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque

try:
    import mne
    mne.set_log_level('WARNING')
    from scipy import signal as scipy_signal
    from scipy.signal import find_peaks
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    print(f"\nMissing: {e}\nRun:  pip install mne scipy matplotlib numpy\n")

# ─────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────
EEG_REGIONS = {
    "All":       [],
    "Frontal":   ['FP1','FP2','FZ','F1','F2','F3','F4','F7','F8','AFZ','AF3','AF4'],
    "Temporal":  ['T7','T8','TP7','TP8','FT7','FT8','T3','T4','T5','T6'],
    "Parietal":  ['P1','P2','P3','P4','PZ','CP1','CP2','P7','P8','CP3','CP4','CPZ'],
    "Occipital": ['O1','O2','OZ','POZ','PO3','PO4','PO7','PO8'],
    "Central":   ['C1','C2','C3','C4','CZ','FC1','FC2','FC3','FC4','FCZ'],
}

BAND_DEFS   = {'d':(1,4), 't':(4,8), 'a':(8,13), 'b':(13,30), 'g':(30,45)}
BAND_LABELS = {'d': 'delta', 't': 'theta', 'a': 'alpha', 'b': 'beta',  'g': 'gamma'}
BAND_COLORS = {'d':'#a040e8', 't':'#00d4e8', 'a':'#00e87a', 'b':'#e8a000', 'g':'#e84040'}
BAND_DISP   = {'d': 'δ',     't': 'θ',     'a': 'α',     'b': 'β',     'g': 'γ'}

BG     = '#040408'
PANEL  = '#06060d'
BORDER = '#0e0e1e'
ACCENT = '#00e87a'
CYAN   = '#00d4e8'
VIOLET = '#a040e8'
GOLD   = '#e8c040'
DIM    = '#5a5a88'


# ─────────────────────────────────────────────────────────────
#  GRAPHICAL EQUALIZER WIDGET (for frequency targeting)
# ─────────────────────────────────────────────────────────────
class FrequencyEQ(tk.Frame):
    """A graphical equalizer for EEG frequency bands (Delta, Theta, Alpha, Beta, Gamma)."""
    def __init__(self, parent, bands, band_disp, band_colors, width=500, height=70, callback=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.bands = bands                    # list of band keys ['d','t','a','b','g']
        self.band_disp = band_disp            # display names {'d':'δ', ...}
        self.band_colors = band_colors        # colors for each band
        self.callback = callback
        
        # Default flat response (all bands at 1.0)
        self.gains = {band: 1.0 for band in self.bands}
        
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg='#1a1a2a', highlightthickness=0)
        self.canvas.pack(pady=5)
        
        self.band_width = self.width / len(self.bands)
        self.selected_band = None
        
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonPress-1>", self._on_click)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        
        self.draw()

    def _on_click(self, event):
        band_index = int(event.x // self.band_width)
        if 0 <= band_index < len(self.bands):
            self.selected_band = self.bands[band_index]
            self._update_gain(event.y)

    def _on_release(self, event):
        self.selected_band = None

    def _on_drag(self, event):
        if self.selected_band is not None:
            self._update_gain(event.y)

    def _update_gain(self, y_pos):
        y_clamped = max(0, min(self.height, y_pos))
        gain = 1.0 - (y_clamped / self.height)   # top = 1.0, bottom = 0.0
        self.gains[self.selected_band] = gain
        self.draw()
        if self.callback:
            self.callback()

    def draw(self):
        self.canvas.delete("all")
        
        # Draw filled curve
        points = []
        for i, band in enumerate(self.bands):
            x = i * self.band_width
            y = (1.0 - self.gains[band]) * self.height
            points.extend([x, y])
        for i, band in enumerate(reversed(self.bands)):
            x = (len(self.bands) - 1 - i + 1) * self.band_width
            y = self.height
            points.extend([x, y])
        self.canvas.create_polygon(points, fill='#2a2a4a', outline='#4a4a7a')
        
        # Draw band bars and labels
        for i, band in enumerate(self.bands):
            x = i * self.band_width
            x_center = x + self.band_width / 2
            y = (1.0 - self.gains[band]) * self.height
            
            # Bar
            self.canvas.create_rectangle(x, y, x + self.band_width - 2, self.height,
                                         fill=self.band_colors.get(band, '#888888'), 
                                         outline='', width=0)
            # Control knob
            self.canvas.create_oval(x_center - 6, y - 6, x_center + 6, y + 6,
                                    fill='white', outline='#333333', width=1)
            # Label beneath
            self.canvas.create_text(x_center, self.height + 12,
                                    text=self.band_disp.get(band, band),
                                    fill=self.band_colors.get(band, '#cccccc'),
                                    font=('Courier New', 9, 'bold'))
        
        # Draw zero line
        self.canvas.create_line(0, self.height, self.width, self.height,
                                fill=DIM, width=1, dash=(2,2))

    def get_gain_for_frequency(self, freq_hz):
        """Return gain multiplier for a given frequency (Hz) based on band gains."""
        # Find which band this frequency falls into
        for band, (lo, hi) in BAND_DEFS.items():
            if lo <= freq_hz < hi:
                return self.gains.get(band, 1.0)
        return 1.0  # fallback

    def get_filter_array(self, frequencies):
        """Return array of gains for each frequency in the given array."""
        return np.array([self.get_gain_for_frequency(f) for f in frequencies])

    def reset_flat(self):
        for band in self.bands:
            self.gains[band] = 1.0
        self.draw()
        if self.callback:
            self.callback()


# ─────────────────────────────────────────────────────────────
#  INVERSE RAJAPINTA — Log-spaced resonator bank with FREQUENCY TARGETING
# ─────────────────────────────────────────────────────────────
class InverseRajapinta:
    """
    Continuous EEG signal fed into 128 log-spaced resonators.
    Each accumulates energy via sin-coherence with its natural frequency.
    The energy distribution is the rajapinta frequency manifold.
    Supports frequency targeting via external gain multipliers (graphic EQ).
    """
    def __init__(self, n=128, f_lo=0.5, f_hi=45.0, decay=0.965):
        self.freqs  = np.exp(np.linspace(np.log(f_lo), np.log(f_hi), n))
        self.n      = n
        self.decay  = decay
        self.energy = np.zeros(n, dtype=np.float64)
        self.phases = np.zeros(n, dtype=np.float64)
        self.TWO_PI = 2.0 * np.pi
        self.freq_eq_gains = np.ones(n, dtype=np.float64)   # frequency targeting multipliers

    def set_eq_gains(self, eq_widget):
        """Update frequency targeting gains from the EQ widget."""
        self.freq_eq_gains = eq_widget.get_filter_array(self.freqs)

    def feed(self, chunk, dt):
        adv = self.TWO_PI * self.freqs * dt
        for s in chunk:
            self.phases  = (self.phases + adv) % self.TWO_PI
            resonance    = np.abs(s) * np.abs(np.sin(self.phases))
            # Apply frequency targeting gain before accumulation
            targeted_resonance = resonance * self.freq_eq_gains
            self.energy  = self.energy * self.decay + targeted_resonance * (1.0 - self.decay)

    def energy_norm(self):
        mx = self.energy.max()
        return self.energy / mx if mx > 1e-12 else self.energy.copy()

    def dominant_freqs(self, top=5):
        en = self.energy_norm()
        peaks, _ = find_peaks(en, height=0.15, distance=3)
        if not len(peaks):
            return []
        order = np.argsort(en[peaks])[::-1]
        return [(float(self.freqs[peaks[i]]), float(en[peaks[i]])) for i in order[:top]]

    def get_manifold(self, size=128):
        """Reconstruct Moire field from top resonators, respecting EQ gains."""
        field = np.zeros((size, size), dtype=np.float32)
        x = np.linspace(-1.0, 1.0, size, dtype=np.float32)
        X, Y = np.meshgrid(x, x)
        R = (np.sqrt(X**2 + Y**2) + 1e-6).astype(np.float32)
        en  = self.energy_norm()
        gains = self.freq_eq_gains   # frequency targeting applied during manifold generation
        
        # Use all resonators with significant energy, weighted by EQ gains
        top = np.argsort(en * gains)[-36:]
        for i in top:
            w = float(en[i] * gains[i])
            if w < 0.03:
                continue
            field += w * np.sin(2.0 * np.pi * float(self.freqs[i]) * R
                                 + float(self.phases[i]))
        lo, hi = float(field.min()), float(field.max())
        if hi - lo > 1e-8:
            field = (field - lo) / (hi - lo)
        return field

    def get_spectrum_with_gains(self):
        """Return frequencies, raw energy, and gain-weighted energy for display."""
        en = self.energy_norm()
        weighted = en * self.freq_eq_gains
        # Normalize weighted for display
        if weighted.max() > 1e-8:
            weighted = weighted / weighted.max()
        return self.freqs.copy(), en, weighted

    def reset(self):
        self.energy[:] = 0.0
        self.phases[:] = 0.0


# ─────────────────────────────────────────────────────────────
#  TAKENS BUFFER
# ─────────────────────────────────────────────────────────────
class TakensBuffer:
    def __init__(self, capacity=2000, delay=20):
        self._buf  = deque(maxlen=int(capacity))
        self.delay = max(3, int(delay))

    def push(self, v):
        self._buf.append(float(v))

    def get_xy(self, n_pts=700):
        data = list(self._buf)
        if len(data) <= self.delay + 4:
            return np.array([]), np.array([])
        x = np.array(data[self.delay:],           dtype=np.float32)
        y = np.array(data[:len(data)-self.delay],  dtype=np.float32)
        if len(x) > n_pts:
            step = max(1, len(x) // n_pts)
            x, y = x[::step], y[::step]
        return x, y

    def clear(self):
        self._buf.clear()


# ─────────────────────────────────────────────────────────────
#  EEG LOADER  (single-threaded, explicit .loaded flag)
# ─────────────────────────────────────────────────────────────
class EEGLoader:
    def __init__(self, target_fs=256):
        self.raw      = None
        self.fs       = target_fs
        self.target_fs = target_fs
        self.cursor   = 0
        self.n_times  = 0
        self.channels = []
        self.channel  = None
        self.loaded   = False   # THE flag — set True only after successful load

    def load(self, path, region="All", fs=256):
        """Synchronous load. Returns (True, info) or (False, error)."""
        # Reset first
        self.loaded   = False
        self.raw      = None
        self.channels = []
        self.channel  = None

        try:
            print(f"[load] opening: {path}")
            raw = mne.io.read_raw_edf(path, preload=True, verbose=False)

            # Clean up channel names
            raw.rename_channels(lambda n: n.strip()
                                           .replace('.', '')
                                           .replace(' ', '')
                                           .upper())
            print(f"[load] found channels: {raw.ch_names[:10]}")

            # Region subset
            if region != "All" and region in EEG_REGIONS:
                want = [c for c in EEG_REGIONS[region] if c in raw.ch_names]
                if want:
                    raw.pick_channels(want)
                    print(f"[load] picked {len(want)} channels for region '{region}'")
                else:
                    print(f"[load] no matching channels for region '{region}', using all")

            print(f"[load] resampling to {fs} Hz …")
            raw.resample(fs, verbose=False)

            # Commit
            self.raw      = raw
            self.fs       = fs
            self.cursor   = 0
            self.n_times  = int(raw.n_times)
            self.channels = list(raw.ch_names)
            self.channel  = self.channels[0] if self.channels else None
            self.loaded   = True

            info = (f"{len(self.channels)} ch  @  {fs} Hz  "
                    f"({self.n_times / fs:.1f} s)")
            print(f"[load] SUCCESS — {info}")
            return True, info

        except Exception:
            err_lines = traceback.format_exc(limit=3).strip().split('\n')
            err_short = err_lines[-1]
            print(f"[load] FAILED:\n{traceback.format_exc()}")
            return False, err_short

    def get_chunk(self, n=16):
        """Returns (np.array, dt) or (None, None)."""
        if not self.loaded or self.raw is None:
            return None, None

        end = self.cursor + n
        if end >= self.n_times:
            self.cursor = 0
            end = n
        if end > self.n_times:
            return None, None

        data, _ = self.raw[:, self.cursor:end]
        self.cursor = end

        if self.channel and self.channel in self.raw.ch_names:
            idx   = self.raw.ch_names.index(self.channel)
            chunk = data[idx, :].astype(np.float64)
        else:
            chunk = np.mean(data, axis=0).astype(np.float64)

        std = float(chunk.std())
        if std > 1e-12:
            chunk /= std
        return chunk, 1.0 / self.fs

    def set_channel(self, ch):
        if ch in self.channels:
            self.channel = ch

    def channel_index(self):
        try:
            return self.channels.index(self.channel)
        except ValueError:
            return 0


# ─────────────────────────────────────────────────────────────
#  BAND POWER HELPER
# ─────────────────────────────────────────────────────────────
def compute_bands(chunk, fs):
    nyq = fs / 2.0
    out = {}
    for key, (lo, hi) in BAND_DEFS.items():
        hi2 = min(hi, nyq - 0.5)
        if lo >= hi2 or len(chunk) < 32:
            out[key] = 0.0
            continue
        try:
            b, a = scipy_signal.butter(4, [lo / nyq, hi2 / nyq], btype='band')
            f    = scipy_signal.filtfilt(b, a, chunk)
            out[key] = float(np.log1p(np.mean(f ** 2)))
        except Exception:
            out[key] = 0.0
    return out


# ─────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────────────────────
class BrainManifoldViewer:
    TICK_MS    = 40     # ~25 fps
    CHUNK_SIZE = 16     # EEG samples per tick

    def __init__(self, root):
        self.root    = root
        self.loader  = EEGLoader(target_fs=256)
        self.inverse = InverseRajapinta(n=128, f_lo=0.5, f_hi=45.0)
        self.takens  = TakensBuffer(capacity=2000, delay=20)

        self.running      = False
        self.tick_count   = 0
        self.signal_buf   = deque(maxlen=3000)
        self.band_hist    = {k: deque(maxlen=300) for k in BAND_DEFS}
        self.manifold_img = np.zeros((128, 128), dtype=np.float32)
        self._peak_vlines = []

        self._build_controls()
        self._build_figure()
        self._schedule()

    # ── Controls ──────────────────────────────────────────────
    def _build_controls(self):
        # Top control bar
        bar = tk.Frame(self.root, bg=BG, pady=5)
        bar.pack(side=tk.TOP, fill=tk.X, padx=6)

        def btn(text, cmd, fg=ACCENT):
            b = tk.Button(bar, text=text, command=cmd,
                          bg='#0a0a18', fg=fg,
                          activebackground='#181830', activeforeground=fg,
                          font=('Courier New', 9, 'bold'),
                          relief=tk.FLAT, padx=9, pady=3,
                          highlightbackground=BORDER, highlightthickness=1)
            b.pack(side=tk.LEFT, padx=3)
            return b

        btn("LOAD EDF", self._on_load)
        btn("START",    self._on_start,  ACCENT)
        btn("STOP",     self._on_stop,   '#e84040')
        btn("RESET",    self._on_reset,  GOLD)
        btn("◄ CH",     self._ch_prev,   CYAN)
        btn("CH ►",     self._ch_next,   CYAN)

        tk.Label(bar, text=" Region:", bg=BG, fg=DIM,
                 font=('Courier New', 8)).pack(side=tk.LEFT)
        self.region_var = tk.StringVar(value="All")
        ttk.Combobox(bar, textvariable=self.region_var,
                     values=list(EEG_REGIONS.keys()),
                     width=9, font=('Courier New', 8),
                     state='readonly').pack(side=tk.LEFT, padx=2)

        tk.Label(bar, text="  tau:", bg=BG, fg=DIM,
                 font=('Courier New', 8)).pack(side=tk.LEFT)
        self.tau_var = tk.IntVar(value=20)
        sb = tk.Spinbox(bar, from_=3, to=120, textvariable=self.tau_var,
                        width=4, font=('Courier New', 8),
                        bg='#0a0a18', fg=CYAN, buttonbackground='#0a0a18',
                        command=self._on_tau)
        sb.pack(side=tk.LEFT, padx=2)
        sb.bind('<Return>', lambda _: self._on_tau())

        self.ch_var     = tk.StringVar(value="CH: --")
        self.status_var = tk.StringVar(value="Load an EDF file to begin")
        tk.Label(bar, textvariable=self.ch_var,
                 bg=BG, fg=GOLD, font=('Courier New', 8)).pack(side=tk.RIGHT, padx=6)
        tk.Label(bar, textvariable=self.status_var,
                 bg=BG, fg=DIM,  font=('Courier New', 8)).pack(side=tk.RIGHT, padx=6)

        # --- FREQUENCY TARGETING EQ (Graphical Equalizer) ---
        eq_frame = tk.Frame(self.root, bg=BG, pady=8)
        eq_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        eq_label = tk.Label(eq_frame, text="FREQUENCY TARGETING  |  Drag bars to amplify/suppress brainwave bands",
                            bg=BG, fg=ACCENT, font=('Courier New', 9, 'bold'))
        eq_label.pack()

        # Create the graphical EQ with band names and colors
        band_keys = ['d', 't', 'a', 'b', 'g']
        self.freq_eq = FrequencyEQ(eq_frame, band_keys, BAND_DISP, BAND_COLORS,
                                   width=550, height=70, callback=self._on_eq_changed)
        self.freq_eq.pack(pady=5)

        # Preset buttons for EQ
        preset_frame = tk.Frame(eq_frame, bg=BG)
        preset_frame.pack(pady=4)
        
        def preset_btn(text, callback):
            tk.Button(preset_frame, text=text, command=callback,
                      bg='#0a0a18', fg=CYAN, font=('Courier New', 8),
                      relief=tk.FLAT, padx=8, pady=1).pack(side=tk.LEFT, padx=3)
        
        preset_btn("FLAT", self._eq_flat)
        preset_btn("EMPHASIZE ALPHA", lambda: self._eq_preset({'a':1.4, 'b':0.8, 'g':0.6, 't':0.9, 'd':0.7}))
        preset_btn("EMPHASIZE BETA",  lambda: self._eq_preset({'b':1.5, 'g':1.2, 'a':0.7, 't':0.6, 'd':0.5}))
        preset_btn("EMPHASIZE THETA", lambda: self._eq_preset({'t':1.6, 'd':1.2, 'a':0.8, 'b':0.6, 'g':0.4}))
        preset_btn("SUPPRESS HIGH",   lambda: self._eq_preset({'b':0.3, 'g':0.2, 'a':0.8, 't':1.0, 'd':1.0}))

    def _on_eq_changed(self):
        """Called when EQ sliders move — update resonator gains."""
        if hasattr(self, 'inverse') and self.inverse is not None:
            self.inverse.set_eq_gains(self.freq_eq)
            # Force a quick manifold update on next tick

    def _eq_flat(self):
        self.freq_eq.reset_flat()
        self._on_eq_changed()

    def _eq_preset(self, gains_dict):
        for band, gain in gains_dict.items():
            if band in self.freq_eq.gains:
                self.freq_eq.gains[band] = gain
        self.freq_eq.draw()
        self._on_eq_changed()

    # ── Figure ────────────────────────────────────────────────
    def _build_figure(self):
        self.fig = plt.Figure(figsize=(17, 10), facecolor=BG)
        gs = gridspec.GridSpec(3, 4, figure=self.fig,
                               hspace=0.44, wspace=0.30,
                               left=0.05, right=0.97,
                               top=0.92, bottom=0.04)

        self.fig.text(0.5, 0.975,
                      'BRAIN MANIFOLD VIEWER  |  RAJAPINTA INVERSE PROJECTION  |  FREQUENCY TARGETING ACTIVE',
                      ha='center', va='top', fontsize=11,
                      color=ACCENT, family='monospace', fontweight='bold')

        def ax(pos):
            a = self.fig.add_subplot(pos)
            a.set_facecolor(PANEL)
            for sp in a.spines.values():
                sp.set_color(BORDER)
            a.tick_params(colors=DIM, labelsize=7)
            return a

        self.ax_sig  = ax(gs[0, 0])
        self.ax_tak  = ax(gs[0, 1])
        self.ax_mfld = ax(gs[0, 2])
        self.ax_res  = ax(gs[0, 3])
        self.ax_band = ax(gs[1, :])
        self.ax_info = ax(gs[2, :])

        # Raw signal
        self.ax_sig.set_title('RAW EEG (z-scored)', color=CYAN,
                               fontsize=8, family='monospace', pad=3)
        self.line_sig, = self.ax_sig.plot([], [], color=CYAN, lw=0.7)
        self.ax_sig.axhline( 2.0, color='#e8404044', lw=0.6, ls='--')
        self.ax_sig.axhline(-2.0, color='#e8404044', lw=0.6, ls='--')
        self.ax_sig.set_xlim(0, 300)
        self.ax_sig.set_ylim(-5, 5)
        self.ax_sig.set_xlabel('samples', color=DIM, fontsize=6)

        # Takens — redrawn each frame via cla()
        self.ax_tak.set_title('TAKENS MANIFOLD  S(t) vs S(t-tau)',
                               color=CYAN, fontsize=8, family='monospace', pad=3)
        self.ax_tak.set_xlim(-4, 4)
        self.ax_tak.set_ylim(-4, 4)

        # Manifold image
        self.ax_mfld.set_title('RAJAPINTA MOIRE MANIFOLD (EQ Weighted)',
                                color=VIOLET, fontsize=8, family='monospace', pad=3)
        self.im_mfld = self.ax_mfld.imshow(
            np.zeros((128, 128)), cmap='inferno',
            origin='lower', aspect='equal', vmin=0, vmax=1)
        self.ax_mfld.set_xticks([])
        self.ax_mfld.set_yticks([])

        # Resonator spectrum (dual: raw + weighted)
        self.ax_res.set_title('RESONATOR SPECTRUM  (solid = EQ weighted | dashed = raw)',
                               color=GOLD, fontsize=8, family='monospace', pad=3)
        self.ax_res.set_xlabel('Hz', color=DIM, fontsize=6)
        self.ax_res.set_xlim(0.4, 46)
        self.ax_res.set_ylim(0, 1.15)
        for key, (lo, hi) in BAND_DEFS.items():
            self.ax_res.axvspan(lo, hi, alpha=0.07, color=BAND_COLORS[key])
            self.ax_res.text((lo+hi)/2, 1.07, BAND_DISP[key],
                              ha='center', va='bottom',
                              fontsize=6, color=BAND_COLORS[key], family='monospace')
        self.line_res_weighted, = self.ax_res.plot([], [], color=GOLD, lw=1.5, label='weighted')
        self.line_res_raw,      = self.ax_res.plot([], [], color='#e8c04066', lw=0.8, ls='--', label='raw')
        self._fill_res = None
        self.ax_res.legend(loc='upper right', fontsize=6, facecolor=PANEL, edgecolor=BORDER)

        # Band history
        self.ax_band.set_title('BAND POWER HISTORY',
                                color='#e8a000', fontsize=8, family='monospace', pad=3)
        self.band_lines = {}
        for key, color in BAND_COLORS.items():
            ln, = self.ax_band.plot([], [], color=color, lw=1.1,
                                    label=BAND_DISP[key])
            self.band_lines[key] = ln
        self.ax_band.legend(loc='upper right', fontsize=7,
                             facecolor=PANEL, edgecolor=BORDER)
        self.ax_band.set_ylim(0, 3)
        self.ax_band.set_xlim(0, 300)
        self.ax_band.set_xlabel('frames', color=DIM, fontsize=6)

        # Info bar
        self.ax_info.set_facecolor(BG)
        self.ax_info.axis('off')
        self.txt_dom  = self.ax_info.text(
            0.01, 0.65, 'DOMINANT FREQUENCIES: --',
            transform=self.ax_info.transAxes,
            ha='left', va='center', fontsize=9, color=ACCENT, family='monospace')
        self.txt_meta = self.ax_info.text(
            0.01, 0.15, '',
            transform=self.ax_info.transAxes,
            ha='left', va='center', fontsize=7, color=DIM, family='monospace')

        canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas = canvas
        self.fig.canvas.draw()

    # ── Update loop (root.after — no FuncAnimation, no races) ─
    def _schedule(self):
        self.root.after(self.TICK_MS, self._tick)

    def _tick(self):
        """Called by tkinter event loop every TICK_MS ms."""
        try:
            if self.running and self.loader.loaded:
                chunk, dt = self.loader.get_chunk(self.CHUNK_SIZE)
                if chunk is not None:
                    self.tick_count += 1
                    self._process(chunk, dt)
                    self._draw()
                    self.canvas.draw_idle()
        except Exception:
            traceback.print_exc()
        finally:
            self._schedule()

    def _process(self, chunk, dt):
        for v in chunk:
            self.signal_buf.append(float(v))
            self.takens.push(float(v))

        self.inverse.feed(chunk, dt)

        if self.tick_count % 4 == 0:
            buf = np.array(list(self.signal_buf)[-512:])
            if len(buf) >= 64:
                bp = compute_bands(buf, self.loader.fs)
                for k, p in bp.items():
                    self.band_hist[k].append(p)

        if self.tick_count % 6 == 0:
            self.manifold_img = self.inverse.get_manifold(size=128)

    # ── Per-panel drawing ─────────────────────────────────────
    def _draw(self):
        self._draw_signal()
        self._draw_takens()
        self._draw_manifold()
        self._draw_resonator()
        self._draw_bands()
        self._draw_info()

    def _draw_signal(self):
        sig = list(self.signal_buf)[-300:]
        if not sig:
            return
        self.line_sig.set_data(np.arange(len(sig)), sig)
        self.ax_sig.set_xlim(0, max(len(sig), 10))
        arr = np.array(sig)
        p2, p98 = np.percentile(arr, [2, 98])
        mg = max(0.4, (p98 - p2) * 0.25)
        self.ax_sig.set_ylim(p2 - mg, p98 + mg)

    def _draw_takens(self):
        x, y = self.takens.get_xy(n_pts=600)
        if len(x) < 10:
            return
        ax = self.ax_tak
        ax.cla()
        ax.set_facecolor(PANEL)
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        ax.tick_params(colors=DIM, labelsize=7)
        ax.set_title('TAKENS MANIFOLD  S(t) vs S(t-tau)',
                      color=CYAN, fontsize=8, family='monospace', pad=3)
        ax.axhline(0, color=BORDER, lw=0.5)
        ax.axvline(0, color=BORDER, lw=0.5)

        n = len(x)
        step = max(1, n // 500)
        for i in range(0, n - step, step):
            age = i / n
            ax.plot(x[i:i+step+1], y[i:i+step+1],
                    color=(age * 0.05, 0.05 + age * 0.85, 0.9 - age * 0.75),
                    lw=0.65, alpha=0.25 + 0.75 * age)

        ax.plot(x[-1], y[-1], 'o', color='white', markersize=4, zorder=10)

        xy_all = np.concatenate([x, y])
        p3, p97 = np.percentile(xy_all, [3, 97])
        rng = max(0.5, (p97 - p3) * 0.65)
        mid = (p3 + p97) / 2.0
        ax.set_xlim(mid - rng, mid + rng)
        ax.set_ylim(mid - rng, mid + rng)

    def _draw_manifold(self):
        self.im_mfld.set_data(self.manifold_img)

    def _draw_resonator(self):
        freqs, raw_en, weighted_en = self.inverse.get_spectrum_with_gains()
        self.line_res_weighted.set_data(freqs, weighted_en)
        self.line_res_raw.set_data(freqs, raw_en)

        # Update fill for weighted spectrum
        if self._fill_res is not None:
            try:
                self._fill_res.remove()
            except Exception:
                pass
        self._fill_res = self.ax_res.fill_between(freqs, weighted_en, alpha=0.28, color=GOLD)

        # Peak markers on weighted spectrum
        for vl in self._peak_vlines:
            try:
                vl.remove()
            except Exception:
                pass
        self._peak_vlines = []
        peaks, _ = find_peaks(weighted_en, height=0.15, distance=3)
        for pk in peaks[:6]:
            vl = self.ax_res.axvline(freqs[pk], color='#ffffff55', lw=0.8, ls=':')
            self._peak_vlines.append(vl)

    def _draw_bands(self):
        for key, ln in self.band_lines.items():
            h = list(self.band_hist[key])
            if h:
                ln.set_data(np.arange(len(h)), h)
        non_empty = [v for v in self.band_hist.values() if v]
        if non_empty:
            mx = max(max(v, default=0.1) for v in non_empty)
            self.ax_band.set_ylim(0, max(0.3, mx * 1.1))
            self.ax_band.set_xlim(0, max(max(len(v) for v in non_empty), 10))

    def _draw_info(self):
        dom = self.inverse.dominant_freqs(top=5)
        if dom:
            # Show which band each dominant frequency belongs to
            parts = []
            for f, e in dom:
                band_char = self._band(f)
                band_name = BAND_DISP.get(band_char, '?')
                parts.append(f"{band_name}{f:.1f}Hz")
            self.txt_dom.set_text("DOMINANT:  " + "   ".join(parts))
        else:
            self.txt_dom.set_text("DOMINANT FREQUENCIES: (accumulating...)")

        ch   = self.loader.channel or '--'
        cidx = self.loader.channel_index() + 1
        ntot = len(self.loader.channels)
        t_s  = self.loader.cursor / max(1, self.loader.fs)
        dur  = self.loader.n_times / max(1, self.loader.fs)
        tau_ms = self.takens.delay / max(1, self.loader.fs) * 1000
        
        # Show EQ status
        eq_status = " | ".join([f"{BAND_DISP[b]}:{self.freq_eq.gains[b]:.1f}" for b in self.freq_eq.bands])
        self.txt_meta.set_text(
            f"CH: {ch}  [{cidx}/{ntot}]    "
            f"t = {t_s:.1f}s / {dur:.1f}s    "
            f"fs = {self.loader.fs} Hz    "
            f"tau = {self.takens.delay} smp  ({tau_ms:.0f} ms)\n"
            f"EQ TARGETS: {eq_status}")

    @staticmethod
    def _band(f):
        for key, (lo, hi) in BAND_DEFS.items():
            if lo <= f < hi:
                return key
        return '?'

    # ── Button handlers ───────────────────────────────────────
    def _on_load(self):
        path = filedialog.askopenfilename(
            title="Select EDF file",
            filetypes=[("EDF files", "*.edf *.EDF"), ("All files", "*.*")])
        if not path:
            return

        was_running = self.running
        self.running = False

        name   = path.replace('\\', '/').split('/')[-1]
        region = self.region_var.get()
        self._set_status(f"Loading {name} ...")
        self.root.update()

        ok, msg = self.loader.load(path, region=region, fs=256)

        if ok:
            self._set_status(f"OK  {msg}")
            self._update_ch()
            # Reset EQ gains to flat when loading new file
            self._eq_flat()
            print(f"[app] loaded OK  loaded={self.loader.loaded}")
        else:
            self._set_status(f"FAILED: {msg}")
            print(f"[app] load failed: {msg}")

    def _on_start(self):
        print(f"[app] START pressed  loaded={self.loader.loaded}")
        if not self.loader.loaded:
            self._set_status("Load an EDF file first")
            return
        self.running = True
        self._set_status(f"Streaming  ch={self.loader.channel}  |  EQ active")

    def _on_stop(self):
        self.running = False
        self._set_status("Stopped")

    def _on_reset(self):
        self.running = False
        self.inverse.reset()
        self.takens  = TakensBuffer(capacity=2000, delay=int(self.tau_var.get()))
        self.signal_buf.clear()
        for v in self.band_hist.values():
            v.clear()
        self.tick_count   = 0
        self.manifold_img = np.zeros((128, 128), dtype=np.float32)
        self._set_status("Reset  --  press START")

    def _on_tau(self):
        self.takens.delay = max(3, int(self.tau_var.get()))

    def _ch_prev(self):
        chs = self.loader.channels
        if not chs:
            return
        i = (self.loader.channel_index() - 1) % len(chs)
        self.loader.set_channel(chs[i])
        self._update_ch()

    def _ch_next(self):
        chs = self.loader.channels
        if not chs:
            return
        i = (self.loader.channel_index() + 1) % len(chs)
        self.loader.set_channel(chs[i])
        self._update_ch()

    def _update_ch(self):
        ch   = self.loader.channel or '--'
        cidx = self.loader.channel_index() + 1
        ntot = len(self.loader.channels)
        self.ch_var.set(f"CH: {ch}  [{cidx}/{ntot}]")

    def _set_status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
def main():
    if not DEPS_OK:
        print("Install:  pip install mne scipy matplotlib numpy")
        sys.exit(1)

    root = tk.Tk()
    root.title("Brain Manifold Viewer - Frequency Targeting")
    root.geometry("1600x980")
    root.configure(bg=BG)

    print("Brain Manifold Viewer with Frequency Targeting")
    print("PerceptionLab, Helsinki 2026")
    print()

    BrainManifoldViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()