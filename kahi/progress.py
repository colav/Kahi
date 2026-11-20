"""Reporte de progreso uniforme para los plugins de Kahi.

Formato::

    [plugin] START total=802785 | detalle
    [plugin] 160000/802785 (19.9%) | 1850 reg/s | ETA 5m48s | nuevos=10 actualizados=90
    [plugin] DONE 802785 reg en 7m12s | nuevos=12034 actualizados=790751

Emite una linea cada ``every`` registros (por defecto 5% del total, minimo
1000) o cada ``seconds`` segundos, lo que ocurra primero. El nombre se normaliza a ``[a-z0-9_:]``. ``initial`` permite
reanudar un proceso: cuenta como ya procesados esos registros sin afectar la
velocidad ni el ETA. Es seguro para uso concurrente con hilos.
"""

import re
from threading import Lock
from time import monotonic


def normalize_name(name):
    """Deja el nombre en ``[a-z0-9_:]`` para que el prefijo sea filtrable."""
    return re.sub(r"[^a-z0-9_:]+", "_", str(name).lower()).strip("_")


def format_duration(seconds):
    seconds = int(max(0, seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return "{}h{:02d}m".format(hours, minutes)
    if minutes:
        return "{}m{:02d}s".format(minutes, secs)
    return f"{secs}s"


class ProgressLogger:
    def __init__(self, name, total=None, every=None, seconds=60, initial=0):
        self.name = normalize_name(name)
        self.total = total if total and total > 0 else None
        if every is None:
            every = max(1000, self.total // 20) if self.total else 1000
        self.every = max(1, int(every))
        self.seconds = seconds
        self.initial = max(0, int(initial or 0))
        self.processed = self.initial
        self.counts = {}
        self._lock = Lock()
        self._start = None
        self._last_emit = None
        self._next_mark = (self.processed // self.every + 1) * self.every

    def log(self, message):
        print(f"[{self.name}] {message}", flush=True)

    def _counts_text(self):
        return " ".join(f"{key}={value}" for key, value in self.counts.items())

    def start(self, detail=""):
        self._start = self._last_emit = monotonic()
        total = self.total if self.total is not None else "?"
        parts = [f"START total={total}"]
        if self.initial:
            parts.append(f"reanuda_desde={self.initial}")
        if detail:
            parts.append(detail)
        self.log(" | ".join(parts))
        return self

    def step(self, outcome=None, n=1):
        """Registra ``n`` registros terminados, opcionalmente con su resultado."""
        if n <= 0:
            return
        with self._lock:
            if self._start is None:
                self._start = self._last_emit = monotonic()
            self.processed += n
            if outcome:
                self.counts[outcome] = self.counts.get(outcome, 0) + n
            now = monotonic()
            if self.processed >= self._next_mark or now - self._last_emit >= self.seconds:
                while self._next_mark <= self.processed:
                    self._next_mark += self.every
                self._last_emit = now
                self._emit(now)

    def _emit(self, now):
        elapsed = max(now - self._start, 1e-9)
        rate = (self.processed - self.initial) / elapsed
        if self.total:
            pct = 100.0 * self.processed / self.total
            eta = (self.total - self.processed) / rate if rate else 0
            head = "{}/{} ({:.1f}%) | {:.0f} reg/s | ETA {}".format(
                self.processed, self.total, pct, rate, format_duration(eta))
        else:
            head = "{} reg | {:.0f} reg/s".format(self.processed, rate)
        counts = self._counts_text()
        self.log(head + (f" | {counts}" if counts else ""))

    def done(self, **extra):
        with self._lock:
            start = self._start if self._start is not None else monotonic()
            elapsed = monotonic() - start
            self.counts.update(extra)
            counts = self._counts_text()
            suffix = f" | {counts}" if counts else ""
            self.log(f"DONE {self.processed} reg en {format_duration(elapsed)}{suffix}")
