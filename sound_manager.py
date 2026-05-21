"""Administrador de sonido interactivo para 2048 Accesible."""
import array
import logging
import math
import platform
import random
import struct
from typing import Dict, List, Optional

try:
    import winsound  # type: ignore[import]
    import ctypes
except ImportError:
    winsound = None
    ctypes = None


class SoundManager:
    """
    Administra efectos de audio del juego generados dinámicamente en memoria,
    eliminando por completo el uso de archivos temporales en disco.
    """

    def __init__(self) -> None:
        """Inicializa el administrador de sonido y pre-genera los efectos."""
        self.sounds: Dict[str, bytes] = {}
        self._last_memory_buffer: Optional[bytes] = None

        # Test de audio del sistema al inicio
        if winsound is not None:
            try:
                winsound.MessageBeep(winsound.MB_OK)  # type: ignore[attr-defined]
            except Exception as e:
                logging.error(f"System Audio Test Failed: {e}")

        try:
            self._pregenerate_defaults()
            logging.info("SoundManager initialized. All sounds pre-generated in memory.")
        except Exception as e:
            logging.error(f"Pregeneration failed: {e}")

    def _compute_tile_sample(self, phase: float, freq: float, sample_rate: int, time_t: float) -> float:
        """Calcula un sample individual con el timbre distintivo del juego."""
        val = 0.0
        val += 1.0 * math.sin(phase)
        val += 0.5 * math.sin(phase * 3.0)
        val += 0.25 * math.sin(phase * 5.0)
        val += 0.1 * math.sin(phase * 2.4)

        if time_t < 0.01:
            noise = (random.random() - 0.5) * 2.0
            noise_env = 1.0 - (time_t / 0.01)
            val += noise * 0.8 * noise_env

        return val / 2.0

    def _wrap_wav_header(self, pcm_data: bytes) -> bytes:
        """Envuelve datos PCM en un encabezado WAV válido."""
        header = struct.pack('<4sI4s', b'RIFF', 36 + len(pcm_data), b'WAVE')
        fmt = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 2, 44100, 44100 * 4, 4, 16)
        data_hdr = struct.pack('<4sI', b'data', len(pcm_data))
        return header + fmt + data_hdr + pcm_data

    def _generate_wave(self, freq_start: float, freq_end: float, duration: float, vol: float = 0.5) -> bytes:
        """Genera un barrido de frecuencias WAV estéreo en memoria."""
        sample_rate = 44100
        n_samples = int(sample_rate * duration)

        # Pre-alocar buffer (2 canales × n_samples)
        buf = array.array('h', [0]) * (n_samples * 2)

        phase = 0.0
        attack_samples = int(sample_rate * 0.005)

        for i in range(n_samples):
            progress = float(i) / n_samples
            f_current = freq_start + (freq_end - freq_start) * progress
            phase += 2 * math.pi * f_current / sample_rate

            val = self._compute_tile_sample(phase, f_current, sample_rate, float(i) / sample_rate)

            # Envolvente: ataque rápido + decaimiento exponencial
            if i < attack_samples:
                env = i / max(1, attack_samples)
            else:
                decay_div = max(1, n_samples - attack_samples)
                decay_progress = (i - attack_samples) / decay_div
                env = math.exp(-8.0 * decay_progress)

            base_sample = int(val * 32700.0 * vol * env)
            sample_val = max(-32767, min(32767, base_sample))

            buf[i * 2] = sample_val
            buf[i * 2 + 1] = sample_val

        return self._wrap_wav_header(buf.tobytes())

    def _generate_sequence(self, freqs: List[float], note_duration: float, vol: float = 0.5) -> bytes:
        """Genera una secuencia melódica de notas en memoria."""
        sample_rate = 44100
        n_samples_note = int(sample_rate * note_duration)
        attack_samples = int(sample_rate * 0.005)

        # Pre-alocar buffer para toda la secuencia
        total_samples = n_samples_note * len(freqs) * 2
        buf = array.array('h', [0]) * total_samples
        buf_idx = 0

        for f_note in freqs:
            phase = 0.0
            f_val = float(f_note)

            for i_samp in range(n_samples_note):
                phase += 2.0 * math.pi * f_val / float(sample_rate)
                val = self._compute_tile_sample(phase, f_val, sample_rate, float(i_samp) / sample_rate)

                if i_samp < attack_samples:
                    env = i_samp / max(1, attack_samples)
                else:
                    decay_div = max(1, n_samples_note - attack_samples)
                    decay_prog = (i_samp - attack_samples) / decay_div
                    env = math.exp(-2.0 * decay_prog)
                    env = env * 0.8 + 0.2 * (1.0 - decay_prog)

                sample_val = max(-32767, min(32767, int(val * 32767.0 * vol * env)))

                buf[buf_idx] = sample_val
                buf[buf_idx + 1] = sample_val
                buf_idx += 2

        return self._wrap_wav_header(buf.tobytes())

    def _pregenerate_defaults(self) -> None:
        """Pre-genera todos los sonidos por defecto al iniciar."""
        self.sounds['MOVE'] = self._generate_wave(200, 400, 0.2, 0.8)
        self.sounds['INVALID'] = self._generate_wave(100, 50, 0.3, 0.8)
        self.sounds['GAMEOVER'] = self._generate_wave(400, 100, 0.5, 0.8)
        self.sounds['UNDO'] = self._generate_wave(150, 50, 0.2, 0.4)
        self.sounds['TOGGLE_ON'] = self._generate_wave(880, 880, 0.05, 0.3)
        self.sounds['TOGGLE_OFF'] = self._generate_wave(440, 440, 0.05, 0.3)
        self.sounds['WALL_SOFT'] = self._generate_wave(300, 200, 0.06, 0.2)
        self.sounds['VERBOSITY'] = self._generate_wave(660, 660, 0.04, 0.3)

        # Fanfarria de puntuación máxima/hitos (arpegio mayor)
        fanfare_notes = [523.25, 659.25, 783.99, 1046.50]
        self.sounds['HIGHSCORE'] = self._generate_sequence(fanfare_notes, 0.1, 0.4)

        # Reinicio (escala ascendente rápida)
        restart_freqs = [261.63, 329.63, 392.00, 523.25]
        self.sounds['RESTART'] = self._generate_sequence(restart_freqs, 0.05, 0.4)

        # Sonido de guardado (chime de 2 notas)
        save_notes = [523.25, 783.99]
        self.sounds['SAVE'] = self._generate_sequence(save_notes, 0.08, 0.4)

    def play(self, name: str) -> None:
        """Reproduce un sonido pregenerado directamente desde memoria."""
        if platform.system() != 'Windows':
            return

        data = self.sounds.get(name)
        if not data:
            logging.warning(f"Sonido no encontrado en la memoria: {name}")
            return

        try:
            # Anclar buffer para evitar recolección de basura durante la reproducción asíncrona
            self._last_memory_buffer = data
            if ctypes is not None:
                winmm = ctypes.windll.winmm  # type: ignore[union-attr]
                flags = 0x0001 | 0x0004 | 0x0002  # SND_ASYNC | SND_MEMORY | SND_NODEFAULT
                winmm.PlaySoundW(self._last_memory_buffer, 0, flags)
            elif winsound is not None:
                winsound.PlaySound(self._last_memory_buffer, winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_NODEFAULT)  # type: ignore[attr-defined]
        except Exception as e:
            logging.error(f"Error al reproducir audio '{name}' desde memoria: {e}")
