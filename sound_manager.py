import os
import math
import struct
import array
import random
import logging
import platform
import tempfile
import shutil
import atexit

# E-04: Imports condicionales para Windows
if platform.system() == 'Windows':
    import winsound
    import ctypes
else:
    winsound = None
    ctypes = None


class SoundManager:
    """
    Administra efectos de audio del juego, incluyendo generación dinámica de WAV
    estéreo con paneo y barridos de frecuencia.
    """
    def __init__(self):
        """Inicializa el SoundManager, configura directorio temporal y pre-genera sonidos."""
        system_temp = tempfile.gettempdir()
        self.temp_dir = os.path.join(system_temp, "2048_Accesible_Sfx")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        self.sounds = {}
        # H-09: Flag anti-duplicación para cleanup
        self._cleaned_up = False
        logging.info(f"SoundManager initialized. Temp dir: {self.temp_dir}")

        self._cleanup_old_folder()

        # Test de audio del sistema
        if winsound is not None:
            try:
                winsound.MessageBeep(winsound.MB_OK)
            except Exception as e:
                logging.error(f"System Audio Test Failed: {e}")

        try:
            self._pregenerate_defaults()
        except Exception as e:
            logging.error(f"Pregeneration failed: {e}")

        atexit.register(self.cleanup)

    def cleanup(self):
        """Elimina todos los archivos temporales de sonido."""
        if self._cleaned_up:
            return
        self._cleaned_up = True
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logging.info(f"Temporales de audio eliminados: {self.temp_dir}")
            except Exception as e:
                logging.warning(f"Error limpiando temporales de audio: {e}")

    def __del__(self):
        """Intento secundario de cleanup durante garbage collection."""
        self.cleanup()

    def _cleanup_old_folder(self):
        """Limpia carpeta legacy de sonidos si existe."""
        old_path = os.path.join(os.path.expanduser("~"), ".2048_sounds")
        if os.path.exists(old_path):
            try:
                shutil.rmtree(old_path, ignore_errors=True)
                logging.info(f"Cleaned up legacy sound folder: {old_path}")
            except Exception as e:
                logging.warning(f"Could not remove legacy folder {old_path}: {e}")

    # E-08: Generación optimizada con buffer pre-alocado
    def _generate_wave(self, freq_start, freq_end, duration, vol=0.5,
                       pan_start=0.0, pan_end=None):
        """Genera datos WAV estéreo con barrido de frecuencia y paneo."""
        if pan_end is None:
            pan_end = pan_start

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

            val = self._compute_tile_sample(phase, f_current, sample_rate,
                                            float(i) / sample_rate)

            # Envolvente: ataque rápido + decay exponencial
            if i < attack_samples:
                env = i / max(1, attack_samples)
            else:
                decay_div = max(1, n_samples - attack_samples)
                decay_progress = (i - attack_samples) / decay_div
                env = math.exp(-8.0 * decay_progress)

            # Paneo estéreo
            current_pan = pan_start + (pan_end - pan_start) * progress
            left_factor = max(0.0, min(1.0, 0.5 * (1.0 - current_pan) * 2.0))
            right_factor = max(0.0, min(1.0, 0.5 * (1.0 + current_pan) * 2.0))

            base_sample = int(val * 32700.0 * vol * env)
            left_sample = max(-32767, min(32767, int(base_sample * left_factor)))
            right_sample = max(-32767, min(32767, int(base_sample * right_factor)))

            buf[i * 2] = left_sample
            buf[i * 2 + 1] = right_sample

        return self._wrap_wav_header(buf.tobytes())

    def _wrap_wav_header(self, pcm_data):
        """Envuelve datos PCM en un header WAV válido."""
        header = struct.pack('<4sI4s', b'RIFF', 36 + len(pcm_data), b'WAVE')
        fmt = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 2, 44100, 44100 * 4, 4, 16)
        data_hdr = struct.pack('<4sI', b'data', len(pcm_data))
        return header + fmt + data_hdr + pcm_data

    def _save_temp_sound(self, name, data):
        """Guarda datos WAV en un archivo temporal."""
        path = os.path.join(self.temp_dir, f"{name}.wav")
        try:
            with open(path, "wb") as f:
                f.write(data)
            logging.info(f"Saved sound {name} to {path} ({len(data)} bytes)")
        except Exception as e:
            logging.error(f"Failed to save {name}: {e}")
        return path

    def _pregenerate_defaults(self):
        """Pre-genera todos los sonidos por defecto al iniciar."""
        data = self._generate_wave(200, 400, 0.2, 0.8, pan_start=0.0)
        self.sounds['MOVE'] = self._save_temp_sound('MOVE', data)

        data = self._generate_wave(100, 50, 0.3, 0.8, pan_start=0.0)
        self.sounds['INVALID'] = self._save_temp_sound('INVALID', data)

        data = self._generate_wave(400, 100, 0.5, 0.8, pan_start=0.0)
        self.sounds['GAMEOVER'] = self._save_temp_sound('GAMEOVER', data)

        data = self._generate_wave(150, 50, 0.2, 0.4, pan_start=0.0)
        self.sounds['UNDO'] = self._save_temp_sound('UNDO', data)

        data = self._generate_wave(880, 880, 0.05, 0.3)
        self.sounds['TOGGLE_ON'] = self._save_temp_sound('TOGGLE_ON', data)

        data = self._generate_wave(440, 440, 0.05, 0.3)
        self.sounds['TOGGLE_OFF'] = self._save_temp_sound('TOGGLE_OFF', data)

        # A-04: Sonido sutil para primer wall hit
        data = self._generate_wave(300, 200, 0.06, 0.2, pan_start=0.0)
        self.sounds['WALL_SOFT'] = self._save_temp_sound('WALL_SOFT', data)

        # Fanfare de high score (arpegio mayor)
        fanfare_notes = [523.25, 659.25, 783.99, 1046.50]
        data = self._generate_sequence(fanfare_notes, 0.1, 0.4)
        self.sounds['HIGHSCORE'] = self._save_temp_sound('HIGHSCORE', data)

        # Reinicio
        restart_freqs = [261.63, 329.63, 392.00, 523.25]
        data = self._generate_sequence(restart_freqs, 0.05, 0.4)
        self.sounds['RESTART'] = self._save_temp_sound('RESTART', data)

    def play(self, name_or_data):
        """Reproduce un sonido por nombre predefinido o datos WAV crudos."""
        filepath = None

        if isinstance(name_or_data, str):
            filepath = self.sounds.get(name_or_data)
        elif isinstance(name_or_data, (bytes, bytearray)):
            self._play_from_memory(name_or_data)
            return

        if filepath and os.path.exists(filepath):
            self._play_from_file(filepath)
        elif isinstance(name_or_data, str):
            logging.warning(f"Sound not found: {name_or_data}")

    # H6-02: Anclar buffer para que no sea GC'd durante playback async
    _last_memory_buffer = None

    def _play_from_memory(self, data):
        """Reproduce WAV desde memoria usando WinAPI."""
        if platform.system() != 'Windows':
            return
        try:
            # H6-02: Anclar datos para evitar GC durante playback async
            self._last_memory_buffer = bytes(data)
            winmm = ctypes.windll.winmm
            flags = 0x0001 | 0x0004 | 0x0002  # SND_ASYNC | SND_MEMORY | SND_NODEFAULT
            winmm.PlaySoundW(self._last_memory_buffer, 0, flags)
        except Exception as e:
            logging.error(f"Memory playback failed: {e}")
            if winsound is not None:
                try:
                    winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
                except Exception:
                    pass

    def _play_from_file(self, filepath):
        """Reproduce WAV desde archivo usando WinAPI."""
        if platform.system() != 'Windows':
            return
        try:
            winmm = ctypes.windll.winmm
            flags = 0x0001 | 0x00020000 | 0x0002  # SND_ASYNC | SND_FILENAME | SND_NODEFAULT
            winmm.PlaySoundW(filepath, 0, flags)
        except AttributeError:
            if winsound is not None:
                try:
                    winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
                except Exception as e2:
                    logging.warning(f"Fallback audio también falló: {e2}")
        except Exception as e:
            logging.error(f"Error playing sound {filepath}: {e}")

    def _compute_tile_sample(self, phase, freq, sample_rate, time_t):
        """Calcula un sample individual con timbre de pieza/ficha."""
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

    def _generate_sequence(self, freqs, note_duration, vol=0.5):
        """Genera una secuencia de notas (arpegio)."""
        sample_rate = 44100
        n_samples_note = int(sample_rate * note_duration)
        attack_samples = int(sample_rate * 0.005)

        # E-08: Pre-alocar buffer para toda la secuencia
        total_samples = n_samples_note * len(freqs) * 2  # stereo
        buf = array.array('h', [0]) * total_samples
        buf_idx = 0

        for f_note in freqs:
            phase = 0.0
            f_val = float(f_note)

            for i_samp in range(n_samples_note):
                phase += 2.0 * math.pi * f_val / float(sample_rate)

                val = self._compute_tile_sample(phase, f_val, sample_rate,
                                                float(i_samp) / sample_rate)

                if i_samp < attack_samples:
                    env = i_samp / max(1, attack_samples)
                else:
                    decay_div = max(1, n_samples_note - attack_samples)
                    decay_prog = (i_samp - attack_samples) / decay_div
                    env = math.exp(-2.0 * decay_prog)
                    env = env * 0.8 + 0.2 * (1.0 - decay_prog)

                sample_val = max(-32767, min(32767, int(val * 32767.0 * vol * env)))

                buf[buf_idx] = sample_val  # type: ignore
                buf[buf_idx + 1] = sample_val  # type: ignore
                buf_idx += 2  # type: ignore

        return self._wrap_wav_header(buf.tobytes())


