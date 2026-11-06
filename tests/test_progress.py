from concurrent.futures import ThreadPoolExecutor

from kahi.progress import ProgressLogger, format_duration, normalize_name


def _lines(capsys):
    return [line for line in capsys.readouterr().out.splitlines() if line]


def test_format_duration():
    assert format_duration(5) == "5s"
    assert format_duration(125) == "2m05s"
    assert format_duration(3725) == "1h02m"


def test_start_progress_and_done(capsys):
    progress = ProgressLogger("demo", total=3000, every=1000).start("x=1")
    for i in range(3000):
        progress.step("nuevos" if i % 2 else "actualizados")
    progress.done(extra=7)
    lines = _lines(capsys)
    assert lines[0] == "[demo] START total=3000 | x=1"
    assert lines[1].startswith("[demo] 1000/3000 (33.3%)")
    assert lines[3].startswith("[demo] 3000/3000 (100.0%)")
    assert lines[-1].startswith("[demo] DONE 3000 reg en ")
    assert lines[-1].endswith("actualizados=1500 nuevos=1500 extra=7")


def test_default_interval_is_five_percent_with_minimum():
    assert ProgressLogger("a", total=800000).every == 40000
    assert ProgressLogger("b", total=5000).every == 1000
    assert ProgressLogger("c").every == 1000


def test_initial_resumes_count(capsys):
    progress = ProgressLogger("r", total=5000, every=1000, initial=2500).start()
    progress.step(n=500)
    progress.done()
    lines = _lines(capsys)
    assert lines[0] == "[r] START total=5000 | reanuda_desde=2500"
    assert lines[1].startswith("[r] 3000/5000 (60.0%)")
    assert lines[-1].startswith("[r] DONE 3000 reg")


def test_thread_safe_counts(capsys):
    progress = ProgressLogger("t", total=4000).start()
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda _: progress.step("ok"), range(4000)))
    progress.done()
    assert progress.processed == 4000
    assert progress.counts == {"ok": 4000}
    assert _lines(capsys)[-1].endswith("ok=4000")


def test_normalize_name():
    assert normalize_name("scienti_affiliations:catalog scienti_udea_2024.institution") == \
        "scienti_affiliations:catalog_scienti_udea_2024_institution"
    assert ProgressLogger("Staff:03BP5HC83").name == "staff:03bp5hc83"
