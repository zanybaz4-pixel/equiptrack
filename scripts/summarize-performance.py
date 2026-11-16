"""Validate the six performance cells and collect delivery-safe measurements."""

import argparse
import json
import re
from pathlib import Path
from statistics import mean


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def summarize_cell(directory, mode, users):
    metrics = load(directory / "summary.json")
    values = {name: value["values"] for name, value in metrics["metrics"].items()}
    attempts = values["transaction_requests"]["count"]
    errors = values["transaction_http_errors"]["passes"]
    body_errors = values["transaction_validation_errors"]["passes"]
    assert attempts == values["transaction_latency"]["count"]
    database = load(directory / "database.json")
    expected_writes = attempts - errors if mode == "write" else 0
    assert expected_writes == database["requests"] == database["audit_creations"], directory

    cpu = {service: [] for service in ("api", "db", "edge", "web")}
    locks = []
    io = []
    for line in (directory / "resources.txt").read_text().splitlines():
        if not line.startswith("{"):
            continue
        observation = json.loads(line)
        if observation.get("sample_type") == "postgresql_connections":
            locks.append(observation["lock_waits"])
            io.append(observation["io_waits"])
        else:
            service = observation["Name"].split("-")[-2]
            cpu[service].append(float(observation["CPUPerc"].rstrip("%")))
    assert all(cpu.values()) and locks, directory
    return {
        "mode": mode,
        "users": users,
        "start_utc": (directory / "start-utc.txt").read_text().strip(),
        "end_utc": (directory / "end-utc.txt").read_text().strip(),
        "scenario_seconds": metrics["state"]["testRunDurationMs"] / 1000,
        "requests": attempts,
        "requests_per_second": values["transaction_requests"]["rate"],
        "average_ms": values["transaction_latency"]["avg"],
        "p95_ms": values["transaction_latency"]["p(95)"],
        "error_percent": 100 * errors / attempts,
        "validation_error_percent": 100 * body_errors / attempts,
        "confirmed_writes": expected_writes,
        "cpu": {service: {"mean": mean(samples), "max": max(samples), "samples": len(samples)}
                for service, samples in cpu.items()},
        "pg_samples": len(locks),
        "pg_max_lock_waits": max(locks),
        "pg_max_io_waits": max(io),
        "database_bytes": database["database_bytes"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("windows", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    environment = (args.run / "wsl-environment.txt").read_text()
    wsl = re.search(r"Docker=(\S+) OS=(.+?) CPUs=(\d+) MemoryBytes=(\d+)", environment)
    assert wsl
    container_limits = re.findall(r"NanoCpus=(\d+) MemoryBytes=(\d+)", environment)
    assert len(container_limits) == 4
    report = {
        "run_id": args.run.name,
        "windows": load(args.windows),
        "wsl": {"engine": wsl[1], "os": wsl[2], "logical_cpus": int(wsl[3]), "memory_bytes": int(wsl[4]),
                "explicit_container_limits": any(cpu != "0" or mem != "0" for cpu, mem in container_limits)},
        "database": load(args.run / "database.json"),
        "runs": [summarize_cell(args.run / f"{mode}-{users}", mode, users)
                 for mode in ("read", "write") for users in (1, 10, 50)],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
