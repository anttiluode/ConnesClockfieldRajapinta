import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import defaultdict
import time

class Arm:
    def __init__(self, idx, n_arms):
        self.idx = idx
        # Improved frequency distribution: log + harmonic series + prime bias
        log_f = 0.8 * np.exp(0.085 * idx)
        harmonic = 1.0 + (idx % 11) * 0.4
        prime_bias = 1.0 if idx % 7 == 0 or idx % 13 == 0 else 1.0
        self.f = log_f * harmonic * prime_bias
        self.phi = np.random.uniform(0, 2*np.pi)
        self.A = 0.5 + 0.5 * np.random.rand()

    def update(self, dt, drive=1.0, gamma=1.0):
        self.phi = (self.phi + 2 * np.pi * self.f * gamma * dt) % (2 * np.pi)
        self.A = np.clip(self.A * 0.96 + 0.04 * (0.8 + 0.6 * np.sin(self.phi)), 0.2, 1.8)

class Kernel:
    def __init__(self, n_arms=512):
        self.n_arms = n_arms
        self.arms = [Arm(i, n_arms) for i in range(n_arms)]
        self.leakage_history = []
        
    def step(self, dt=0.01, beta=1.0):
        gamma = 1.0 / (1.0 + 0.22 * beta)
        leakage = 0.0
        
        for i in range(self.n_arms):
            arm = self.arms[i]
            # Ephaptic coupling (local + a bit global)
            neigh = 0.0
            for offset in [-1, 1]:
                j = (i + offset) % self.n_arms
                neigh += np.cos(self.arms[j].phi - arm.phi)
            drive = 1.0 + 0.15 * neigh
            
            arm.update(dt, drive=drive, gamma=gamma)
            leakage += arm.A * np.cos(arm.phi)
        
        leakage /= self.n_arms
        self.leakage_history.append(leakage)
        if len(self.leakage_history) > 1500:
            self.leakage_history.pop(0)
        return leakage

class Rajapinta:
    def __init__(self, kernel, window=300):
        self.kernel = kernel
        self.window = window
        self.discovered = []                    # (ratio, stability, label)
        self.memory = defaultdict(float)
        
    def update(self):
        if len(self.kernel.leakage_history) < self.window:
            return
        
        # Collect candidate frequencies from strong arms
        candidates = [arm.f for arm in self.kernel.arms if arm.A > 0.7]
        if len(candidates) < 4:
            return
            
        new_disc = []
        for i in range(len(candidates)):
            for j in range(i+1, len(candidates)):
                f1 = candidates[i]
                f2 = candidates[j]
                if min(f1, f2) < 1e-6: continue
                
                ratio1 = f1 / f2
                ratio2 = f2 / f1
                
                for ratio in [ratio1, ratio2]:
                    if ratio < 0.2 or ratio > 12: continue
                    # Find simple rational approximations
                    for q in range(1, 18):
                        p = round(ratio * q)
                        if p < 1: continue
                        r_approx = p / q
                        err = abs(ratio - r_approx)
                        if err < 0.045:   # tighter
                            stability = np.exp(-10 * err) * 0.8
                            label = f"{p}/{q}" if p/q <= 1 else f"{q}/{p}" if ratio > 1 else f"{p}/{q}"
                            new_disc.append((r_approx, stability, label))
        
        # Freeze good ones
        for r, stab, label in new_disc:
            if stab > 0.5:
                self.memory[label] += stab * 0.2
                if self.memory[label] > 1.8 and not any(abs(r - ex_r) < 0.04 for ex_r,_,_ in self.discovered):
                    self.discovered.append((r, stab, label))
        
        # Limit to strongest
        if len(self.discovered) > 30:
            self.discovered = sorted(self.discovered, key=lambda x: x[1], reverse=True)[:30]

# ====================== MAIN ======================

kernel = Kernel(n_arms=512)
rajapinta = Rajapinta(kernel)

fig, axs = plt.subplots(3, 1, figsize=(15, 12))
plt.suptitle("Rajapinta Number Forge v0.3 — Better Frequency Diversity", fontsize=16)

line_leak, = axs[0].plot([], [], 'r-', lw=2, label='Additive Leakage')
line_phase, = axs[0].plot([], [], 'b-', lw=1.2, alpha=0.75, label='Phase proxy')
axs[0].set_ylim(-1.5, 1.5)
axs[0].legend()
axs[0].set_title("Leakage Field")

scatter = axs[1].scatter([], [], c=[], s=60, cmap='viridis', vmin=0, vmax=1)
axs[1].set_xlim(0.2, 12)
axs[1].set_ylim(0, 1.05)
axs[1].set_xlabel("Ratio")
axs[1].set_ylabel("Stability")
axs[1].set_title("Discovered Numbers")

text_ax = axs[2]
text_ax.axis('off')
status_text = text_ax.text(0.02, 0.98, "", ha='left', va='top', fontsize=10, family='monospace', transform=text_ax.transAxes)

step = [0]

def update(frame):
    beta = 0.6 + 0.7 * np.sin(step[0] / 120)
    kernel.step(dt=0.009, beta=beta)
    rajapinta.update()
    step[0] += 1
    
    # Update plots
    n = min(300, len(kernel.leakage_history))
    t = np.arange(n) * 0.009
    leak_data = kernel.leakage_history[-n:]
    
    phase_proxy = np.mean([np.sin(a.phi) for a in kernel.arms])
    
    line_leak.set_data(t, leak_data)
    line_phase.set_data(t, [phase_proxy] * n)
    
    if rajapinta.discovered:
        xs = [r for r, _, _ in rajapinta.discovered]
        ys = [s for _, s, _ in rajapinta.discovered]
        scatter.set_offsets(np.c_[xs, ys])
        scatter.set_array(np.array(ys))
    
    # Update memory text
    if rajapinta.memory:
        top = sorted(rajapinta.memory.items(), key=lambda item: item[1], reverse=True)[:18]
        lines = ["Number Memory (frozen ratios):"] + [f"{k:>8}   strength: {v:.1f}" for k, v in top]
        status_text.set_text("\n".join(lines))
    
    if step[0] % 100 == 0:
        count = len(rajapinta.discovered)
        top_r = [round(r, 3) for r, _, _ in rajapinta.discovered[:8]]
        print(f"Step {step[0]:4d} | Discovered: {count:2d} | Top ratios: {top_r}")
    
    return line_leak, line_phase, scatter, status_text

ani = FuncAnimation(fig, update, interval=20, blit=False)

print("Rajapinta Number Forge v0.3 running...")
print("Improved frequency seeding + better ratio detection (both directions)")
print("Should now discover more musically/numerically interesting ratios.\n")

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()