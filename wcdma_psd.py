"""
wcdma_psd.py — 3-carrier WCDMA signal generation and PSD plot.

Generates a baseband complex I/Q signal comprising three adjacent WCDMA
carriers (−5, 0, +5 MHz), each RRC pulse-shaped at 3.84 Mcps with α=0.22.
The PSD is estimated via Welch's method with a Blackman-Harris window to
achieve ≥80 dB passband-to-stopband separation.
"""

import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

def build_params() -> SimpleNamespace:
    chip_rate  = 3.84e6          # WCDMA chip rate (chips/s)
    sps        = 16              # samples per chip  →  fs = 61.44 MHz
    fs         = chip_rate * sps # 61.44 MHz sample rate
    rolloff    = 0.22            # RRC roll-off factor (WCDMA standard)
    rrc_spans  = 32              # RRC filter length in chip-periods (each side)
    n_chips    = 65536           # chips per carrier  →  2^16 = 1 048 576 samples
    carrier_offsets = [-5e6, 0.0, 5e6]  # Hz; standard 5 MHz adjacent spacing

    # Welch PSD parameters
    N_fft    = 16384   # FFT length  →  3.75 kHz/bin
    noverlap = 12288   # 75 % overlap  →  K ≈ 253 segments

    return SimpleNamespace(**locals())


# ---------------------------------------------------------------------------
# RRC filter
# ---------------------------------------------------------------------------

def make_rrc_taps(num_taps: int, sps: int, rolloff: float) -> np.ndarray:
    """Return a (num_taps,) real RRC impulse response, normalised to unit DC gain."""
    alpha = rolloff
    n     = np.arange(num_taps) - (num_taps - 1) / 2   # centred time index
    t     = n / sps                                      # time in chip periods
    h     = np.zeros(num_taps)

    for i, (ti, ni) in enumerate(zip(t, n)):
        if ti == 0.0:
            h[i] = (1.0 / sps) * (1.0 - alpha + 4.0 * alpha / np.pi)
        elif alpha != 0.0 and abs(ti) == 1.0 / (4.0 * alpha):
            h[i] = (alpha / (sps * np.sqrt(2.0))) * (
                (1.0 + 2.0 / np.pi) * np.sin(np.pi / (4.0 * alpha))
                + (1.0 - 2.0 / np.pi) * np.cos(np.pi / (4.0 * alpha))
            )
        else:
            numerator   = (np.sin(np.pi * ti * (1.0 - alpha))
                           + 4.0 * alpha * ti * np.cos(np.pi * ti * (1.0 + alpha)))
            denominator = np.pi * ti * (1.0 - (4.0 * alpha * ti) ** 2)
            h[i] = (1.0 / sps) * numerator / denominator

    # Normalise to unit DC gain
    dc = np.sum(h)
    if dc != 0.0:
        h /= dc
    return h


# ---------------------------------------------------------------------------
# Single carrier
# ---------------------------------------------------------------------------

def make_carrier(
    n_chips: int,
    sps: int,
    rolloff: float,
    rrc_spans: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return one RRC-shaped WCDMA carrier at baseband (length = n_chips * sps)."""
    n_chips_gen = n_chips + rrc_spans       # extra chips absorb filter transients

    # QPSK symbols: independent I and Q drawn from {−1, +1}
    I = rng.choice([-1.0, 1.0], size=n_chips_gen)
    Q = rng.choice([-1.0, 1.0], size=n_chips_gen)
    symbols = (I + 1j * Q) / np.sqrt(2.0)  # unit average power

    # Upsample by sps (insert sps−1 zeros between chips)
    upsampled = np.zeros(n_chips_gen * sps, dtype=complex)
    upsampled[::sps] = symbols

    # RRC pulse-shape
    num_taps = rrc_spans * sps + 1
    h = make_rrc_taps(num_taps, sps, rolloff)
    filtered = np.convolve(upsampled, h, mode='full')

    # Trim filter transient: discard rrc_spans*sps//2 samples from each end
    trim = rrc_spans * sps // 2
    carrier = filtered[trim: trim + n_chips * sps]
    assert len(carrier) == n_chips * sps
    return carrier


# ---------------------------------------------------------------------------
# 3-carrier composite signal
# ---------------------------------------------------------------------------

def make_wcdma_signal(params: SimpleNamespace, rng: np.random.Generator) -> np.ndarray:
    """Return a 3-carrier WCDMA composite baseband signal."""
    N = params.n_chips * params.sps
    t = np.arange(N) / params.fs
    composite = np.zeros(N, dtype=complex)

    for f_offset in params.carrier_offsets:
        carrier = make_carrier(
            params.n_chips, params.sps, params.rolloff, params.rrc_spans, rng
        )
        # Frequency-shift to carrier centre
        carrier *= np.exp(2j * np.pi * f_offset * t)
        composite += carrier

    return composite


# ---------------------------------------------------------------------------
# PSD estimation
# ---------------------------------------------------------------------------

def estimate_psd(
    signal: np.ndarray, params: SimpleNamespace
) -> tuple[np.ndarray, np.ndarray]:
    """Return (freqs_Hz, psd_dBr) using Welch + Blackman-Harris window."""
    f, Pxx = scipy.signal.welch(
        signal,
        fs=params.fs,
        window='blackmanharris',
        nperseg=params.N_fft,
        noverlap=params.noverlap,
        nfft=params.N_fft,
        detrend=False,
        return_onesided=False,   # complex input → two-sided spectrum
        scaling='density',
        average='mean',
    )

    # Convert to dB, guard against log(0)
    psd_db = 10.0 * np.log10(Pxx + 1e-20)

    # Normalise so passband peak is 0 dBr
    psd_db -= psd_db.max()

    # Re-order from [0 … fs/2, −fs/2 … 0) to [−fs/2 … +fs/2)
    f      = np.fft.fftshift(f)
    psd_db = np.fft.fftshift(psd_db)

    return f, psd_db


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot_psd(freqs: np.ndarray, psd_db: np.ndarray, params: SimpleNamespace) -> None:
    """Publication-quality PSD plot; saves wcdma_psd.png."""
    fig, ax = plt.subplots(figsize=(12, 5), dpi=150)

    ax.plot(freqs / 1e6, psd_db, linewidth=0.8, color='steelblue')

    # Carrier centre markers
    for fc_mhz in [-5, 0, 5]:
        ax.axvline(fc_mhz, color='grey', linestyle='--', linewidth=0.7, alpha=0.7)

    # 80 dB reference line
    ax.axhline(-80, color='red', linestyle=':', linewidth=0.9, alpha=0.85,
               label='−80 dB reference')

    ax.set_xlim(-20, 20)
    ax.set_ylim(-120, 5)
    ax.set_xlabel('Frequency (MHz)', fontsize=11)
    ax.set_ylabel('PSD (dBr/Hz)', fontsize=11)
    ax.set_title(
        '3-Carrier WCDMA — Power Spectral Density\n'
        'fs = 61.44 MHz · chip rate = 3.84 Mcps · α = 0.22 · 5 MHz carrier spacing',
        fontsize=11,
    )

    ax.grid(True, which='major', linestyle='-',  alpha=0.4, linewidth=0.6)
    ax.grid(True, which='minor', linestyle='--', alpha=0.2, linewidth=0.4)
    ax.minorticks_on()
    ax.legend(loc='lower center', fontsize=9)

    plt.tight_layout()
    plt.savefig('wcdma_psd.png', dpi=150, bbox_inches='tight')
    print("Plot saved to wcdma_psd.png")
    plt.show()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    params = build_params()
    rng    = np.random.default_rng(42)   # fixed seed → reproducible

    print(f"Generating 3-carrier WCDMA signal "
          f"({params.n_chips * params.sps:,} samples @ {params.fs/1e6:.2f} MHz) ...")
    signal = make_wcdma_signal(params, rng)

    print("Estimating PSD (Welch / Blackman-Harris) ...")
    freqs, psd_db = estimate_psd(signal, params)

    # Programmatic 80 dB verification
    passband_mask  = np.abs(freqs) < 1.92e6           # centre carrier passband
    stopband_mask  = np.abs(freqs) > 8e6              # clear of all 3 carriers
    pb_peak = psd_db[passband_mask].max()
    sb_max  = psd_db[stopband_mask].max()
    ratio   = pb_peak - sb_max
    print(f"Passband peak : {pb_peak:.1f} dBr")
    print(f"Stopband max  : {sb_max:.1f} dBr  (|f| > 8 MHz)")
    print(f"Passband-to-stopband ratio : {ratio:.1f} dB  "
          f"({'PASS' if ratio >= 80 else 'FAIL'} — target ≥ 80 dB)")

    plot_psd(freqs, psd_db, params)


if __name__ == '__main__':
    main()
