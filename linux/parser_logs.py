"""Accesses log parser."""  # noqa: INP001
import argparse
import json
import pprint
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator
from zoneinfo import ZoneInfo


timezone = ZoneInfo("Europe/Moscow")


METHODS = ("GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD")
DEFAULT_PATTERN = "*.log"
TOP_LIMIT = 3

# Example:
# 109.169.248.247 - - [12/Dec/2015:18:25:11 +0100] "POST /administrator/index.php HTTP/1.1" 200 4494 "http://almhuette-raith.at/administrator/" "Mozilla/5.0 (Windows NT 6.0; rv:34.0) Gecko/20100101 Firefox/34.0" 4374  # noqa: E501


LOG_LINE_REGEX = re.compile(
    r'^(?P<ip>\d+\.\d+\.\d+\.\d+)\s+-\s+'
    r'(?P<user>\S+)\s+'
    r'\[(?P<ts>[^\]]+)\]\s+'
    r'"(?P<request>.+)"\s+'
    r'(?P<status>\d{3})\s+'
    r'(?P<size>\S+)\s+'
    r'"(?P<referer>.*)"\s+'
    r'"(?P<ua>.*)"\s+'
    r'(?P<duration_ms>\d+)\s*$',
)


@dataclass(frozen=True)
class LogRecord:
    """Dataclass for one line of logs."""

    ip: str
    date_brackets: str
    method: str
    url: str
    duration_ms: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze access logs:"
                    " methods, top IPs, top 3 longest requests.",
    )
    parser.add_argument(
        "path",
        help="Path to a log file or a directory with logs",
    )
    parser.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help="Filename pattern used when path is a directory",
    )
    parser.add_argument(
        "--out",
        default="./",
        help="Directory where JSON reports will be saved",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=False,
        help="Search for files recursively when path is a directory",
    )
    return parser.parse_args()


def iter_log_files(
    path: Path,
    pattern: str,
    *,
    recursive: bool = False,
) -> Iterator[Path]:
    if path.is_file():
        yield path
        return
    if path.is_dir():
        iterator = path.rglob(pattern) if recursive else path.glob(pattern)
        for file_path in iterator:
            if file_path.is_file():
                yield file_path
        return
    msg = f"File or directory not found: {path}"
    raise FileNotFoundError(msg)


def _parse_request(request: str) -> tuple[str, str]:
    parts = request.split()
    method = parts[0] if len(parts) > 0 else "-"
    url = parts[1] if len(parts) > 1 else "-"
    return method, url


def parse_line(line: str) -> LogRecord | None:
    match = LOG_LINE_REGEX.match(line)
    if not match:
        return None

    method, url = _parse_request(match.group("request"))
    return LogRecord(
        ip=match.group("ip"),
        date_brackets=f"[{match.group('ts')}]",
        method=method,
        url=url,
        duration_ms=int(match.group("duration_ms")),
    )


def change_top_duration_records(
    record1: LogRecord | None,
    record2: LogRecord | None,
    record3: LogRecord | None,
    record: LogRecord,
) -> tuple[LogRecord | None, LogRecord | None, LogRecord | None]:
    record_duration = record.duration_ms

    if record1 is None or record_duration > record1.duration_ms:
        record3, record2, record1 = record2, record1, record
    elif record2 is None or record_duration > record2.duration_ms:
        record3, record2 = record2, record
    elif record3 is None or record_duration > record3.duration_ms:
        record3 = record
    return record1, record2, record3



def analyze_file(path: Path) -> dict:
    method_counts: Counter = Counter()
    ip_counter: Counter = Counter()
    top_time_record1 = top_time_record2 = top_time_record3 = None

    with (path.open("r", encoding="utf-8", errors="ignore") as file):
        for line in file:
            record = parse_line(line)
            if record is None:
                continue

            method_counts[record.method] += 1
            ip_counter[record.ip] += 1

            top_time_record1, top_time_record2, top_time_record3 = \
                change_top_duration_records(
                    top_time_record1,
                    top_time_record2,
                    top_time_record3,
                    record,
                )

    top_ips = dict(ip_counter.most_common(TOP_LIMIT))
    top_longest = [
        {
            "ip": record.ip,
            "date": record.date_brackets,
            "method": record.method,
            "url": record.url,
            "duration": record.duration_ms,
        }
        for record in (
            top_time_record1,
            top_time_record2,
            top_time_record3,
        ) if record
    ]
    total_stat = {method: method_counts[method] for method in METHODS}
    total_requests = method_counts.total()

    return {
        "top_ips": top_ips,
        "top_longest": top_longest,
        "total_stat": total_stat,
        "total_requests": total_requests,
    }


def save_report(report: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=timezone).strftime("%Y-%m-%d_%H-%M-%S")
    report_file = out_dir / f"{timestamp}-scan.json"
    report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report_file


def main() -> int:
    args = parse_args()
    base_path = Path(args.path)
    files = list(iter_log_files(
        base_path,
        args.pattern,
        recursive=args.recursive,
    ))
    if not files:
        print("No log files found.")  # noqa: T201
        return 0

    out_dir = Path(args.out)
    for log_file in files:
        report = analyze_file(log_file)
        report_file = save_report(report, out_dir)
        pprint.pprint(report)  # noqa: T203
        print(f"Report created for {log_file}: {report_file}")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
