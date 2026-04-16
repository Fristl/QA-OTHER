"""Packege with 'ps aux' report script."""  # noqa: INP001

import argparse
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


timezone = ZoneInfo("Europe/Moscow")

@dataclass
class Process:
    """Process data class."""

    user: str
    cpu: float
    mem: float
    command: str


def run_ps_aux() -> list[str]:
    """Execute ps and return result as list of process."""
    result = subprocess.run(
        ["ps", "-axo", "user=,pcpu=,pmem=,command="],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().splitlines()


def parse_ps_aux(lines: list[str]) -> list[Process]:
    """Parse ps output lines with fields: user cpu mem command."""
    procs: list[Process] = []
    for line in lines:
        params = line.split(maxsplit=3)
        if len(params) < 4:
            continue
        user = params[0]
        try:
            cpu = float(params[1])
            mem = float(params[2])
        except ValueError:
            continue
        command = params[3]
        procs.append(Process(user=user, cpu=cpu, mem=mem, command=command))
    return procs


def make_summary(procs: list[Process]) -> dict[str, Any]:
    total_processes = len(procs)

    users_counter: Counter = Counter()

    top_mem_proc: Process | None = None
    total_mem_sum = 0.0

    top_cpu_proc: Process | None = None
    total_cpu_sum = 0.0

    for p in procs:
        users_counter[p.user] += 1

        if top_mem_proc is None or p.mem > top_mem_proc.mem:
            top_mem_proc = p
        total_mem_sum += p.mem

        if top_cpu_proc is None or p.cpu > top_cpu_proc.cpu:
            top_cpu_proc = p
        total_cpu_sum += p.cpu


    sorted_user_counts = sorted(
        users_counter.items(),
        key=lambda kv: (-kv[1], kv[0]),
    )

    return {
        "total_processes": total_processes,
        "users": sorted(users_counter.keys()),
        "top_mem_proc": top_mem_proc,
        "top_cpu_proc": top_cpu_proc,
        "total_cpu_sum": total_cpu_sum,
        "total_mem_sum": total_mem_sum,
        "sorted_user_counts": sorted_user_counts,
    }


def build_report(summary: dict) -> str:
    """Build the report."""
    lines: list[str] = ["System Status Report:"]
    if summary.get("users"):
        lines.append(f"System users: {', '.join(summary['users'])}")
    else:
        lines.append("(none)")
    lines.append(f"Processes running: {summary['total_processes']}")

    lines.append("\nUser processes:")
    if summary.get("sorted_user_counts"):
        lines.extend(
            [
                f"{user}: {count}"
                for user, count in summary["sorted_user_counts"]
            ],
        )
    else:
        lines.append("(no processes parsed)")

    lines.append(
        f"\nSum of process memory (%MEM): {summary['total_mem_sum']:.1f}%",
    )
    lines.append(
        f"Sum of process CPU (%CPU): {summary['total_cpu_sum']:.1f}%",
    )

    lines.append("\nTop processes:")
    if summary.get("top_mem_proc"):
        lines.append(
            f"Top memory: {summary['top_mem_proc'].mem:.1f}% "
            f"- {summary['top_mem_proc'].command:.20}",
        )
    else:
        lines.append("Top memory: n/a")
    if summary.get("top_cpu_proc"):
        lines.append(
            f"Top CPU: {summary['top_cpu_proc'].cpu:.1f}% "
            f"- {summary['top_cpu_proc'].command:.20}",
        )
    else:
        lines.append("Top CPU: n/a")

    return "\n".join(lines)


def save_report(report_text: str, output_dir: str) -> Path:
    """Save report to txt file."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    filename = datetime.now(tz=timezone).strftime(
        "%d-%m-%Y-%H-%M-%S-%f-scan.txt",
    )
    out_path = directory / filename
    out_path.write_text(report_text, encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a process report from ps output.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="./",
        help="Directory for the report (current directory by default).",
    )
    args = parser.parse_args()

    ps_aux_lines = run_ps_aux()
    procs = parse_ps_aux(ps_aux_lines)
    summary = make_summary(procs)
    report = build_report(summary)
    print(report)  # noqa: T201

    out_path = save_report(report, args.output_dir)
    print(f"\nSaved to file: {out_path}")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
