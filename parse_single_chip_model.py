import os
import re
import glob
import yaml
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None
    cm = None
    print("matplotlib not available, skipping chart generation")


TEST_SUITES = ["test_01", "test_05"]

RUN_ID = "01"

MODEL_NAME = "MiniMax-M2.5-W8A8"


def load_models_scenarios(config_path="config/models_scenarios.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


CHIP_BASE_PATHS = {}


def load_chip_base_paths():
    paths = {}
    scenarios = load_models_scenarios()
    models = scenarios.get("models", {})
    for chip_name, chip_models in models.items():
        if chip_models:
            model_info = chip_models[0]
            model_path = model_info.get("model_path", "")
            if model_path:
                model_name = Path(model_path).name
                paths[chip_name] = f"reports/{chip_name}/benchmark/{model_name}"
    return paths


CHIP_BASE_PATHS = load_chip_base_paths()


def get_chip_configs(chip_name, test_suite, run_id):
    base_path = CHIP_BASE_PATHS.get(chip_name, "")
    full_path = f"{base_path}/{test_suite}/{run_id}"

    if not os.path.exists(full_path):
        print(f"Error: No data found at {full_path}")
        return []

    return [
        {
            "name": chip_name,
            "base_path": full_path,
        }
    ]


def load_chip_config(config_path="config/chip_conf.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def load_sglang_config(config_path="config/model_deployment.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def parse_benchmark_log(log_file):
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lines = content.split("\n")
    metrics = {}

    section = None
    section_patterns = {
        "Serving Benchmark Result": "=========== Serving Benchmark Result",
        "End-to-End Latency": "----------------End-to-End Latency",
        "Time to First Token": "---------------Time to First Token",
        "Time per Output Token": "-----Time per Output Token",
        "Inter-Token Latency": "---------------Inter-Token Latency",
    }

    for line in lines:
        found_section = None
        for sec_name, sec_pattern in section_patterns.items():
            if sec_pattern in line:
                found_section = sec_name
                break

        if found_section:
            section = found_section
            continue

        if section and line.strip().startswith("==========="):
            section = None
            continue

        if section:
            match = re.match(r"(.+?):\s+(.+)$", line.strip())
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                full_key = f"[{section}] {key}"
                metrics[full_key] = value
                metrics[key] = value

    return metrics


def extract_concurrency_from_dir(dir_name):
    match = re.match(r"^(\d+)-", dir_name)
    if match:
        return match.group(1)
    return None


def extract_input_output_from_dir(dir_name):
    match = re.search(r"-i(\d+)-o(\d+)", dir_name)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def get_all_concurrencies(chip_config):
    concurrency_set = set()
    base_path = chip_config["base_path"]

    if not os.path.exists(base_path):
        return []

    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            conc = extract_concurrency_from_dir(item)
            if conc:
                concurrency_set.add(conc)

    return sorted(concurrency_set, key=lambda x: int(x))


def get_all_input_output_pairs(chip_config):
    io_pairs = set()
    base_path = chip_config["base_path"]

    if not os.path.exists(base_path):
        return []

    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            input_len, output_len = extract_input_output_from_dir(item)
            if input_len and output_len:
                io_pairs.add((input_len, output_len))

    return sorted(io_pairs, key=lambda x: (x[0], x[1]))


def get_chip_metrics(chip_config, concurrency, input_len=None, output_len=None):
    base_path = chip_config["base_path"]
    chip_name = chip_config["name"]

    if input_len is not None and output_len is not None:
        dir_pattern = os.path.join(
            base_path, f"{concurrency}-*-i{input_len}-o{output_len}"
        )
    else:
        dir_pattern = os.path.join(base_path, f"{concurrency}-*")

    matching_dirs = glob.glob(dir_pattern)

    if not matching_dirs:
        return None

    log_pattern = os.path.join(matching_dirs[0], "*.log")
    log_files = glob.glob(log_pattern)

    if not log_files:
        return None

    metrics = parse_benchmark_log(log_files[0])
    return metrics


def generate_comparison_csv(chip_data, concurrencies, output_dir, chip_name):
    metric_names = [
        ("[Serving Benchmark Result]", ""),
        ("Successful requests", "Successful requests"),
        ("Failed requests", "Failed requests"),
        ("Benchmark duration (s)", "Benchmark duration (s)"),
        ("Total input tokens", "Total input tokens"),
        ("Total generated tokens", "Total generated tokens"),
        ("Request throughput (req/s)", "Request throughput (req/s)"),
        ("Output token throughput (tok/s)", "Output token throughput (tok/s)"),
        (
            "Peak output token throughput (tok/s)",
            "Peak output token throughput (tok/s)",
        ),
        ("Peak concurrent requests", "Peak concurrent requests"),
        ("Total token throughput (tok/s)", "Total token throughput (tok/s)"),
        ("[End-to-End Latency]", ""),
        ("Mean E2E Latency (ms)", "Mean E2E Latency (ms)"),
        ("Median E2E Latency (ms)", "Median E2E Latency (ms)"),
        ("P90 E2E Latency (ms)", "P90 E2E Latency (ms)"),
        ("P99 E2E Latency (ms)", "P99 E2E Latency (ms)"),
        ("[Time to First Token]", ""),
        ("Mean TTFT (ms)", "Mean TTFT (ms)"),
        ("Median TTFT (ms)", "Median TTFT (ms)"),
        ("P99 TTFT (ms)", "P99 TTFT (ms)"),
        ("[Time per Output Token]", ""),
        ("Mean TPOT (ms)", "Mean TPOT (ms)"),
        ("Median TPOT (ms)", "Median TPOT (ms)"),
        ("P99 TPOT (ms)", "P99 TPOT (ms)"),
        ("[Inter-Token Latency]", ""),
        ("Mean ITL (ms)", "Mean ITL (ms)"),
        ("Median ITL (ms)", "Median ITL (ms)"),
        ("P95 ITL (ms)", "P95 ITL (ms)"),
        ("P99 ITL (ms)", "P99 ITL (ms)"),
    ]

    csv_lines = []
    header = ["Metric"] + [f"{conc} concurrency" for conc in concurrencies]
    csv_lines.append(",".join(header))

    for display_name, key_name in metric_names:
        if not key_name:
            csv_lines.append(f"[{display_name}]" + ",," * (len(concurrencies) - 1))
            continue

        row = [display_name]
        for conc in concurrencies:
            value = chip_data.get(chip_name, {}).get(conc, {}).get(key_name, "")
            row.append(value)
        csv_lines.append(",".join(row))

    csv_file = os.path.join(output_dir, "concurrency_comparison.csv")
    with open(csv_file, "w", encoding="utf-8") as f:
        f.write("\n".join(csv_lines))

    print(f"Generated: {csv_file}")
    return [csv_file]


def generate_comparison_charts(
    chip_data, concurrencies, output_dir, chip_name, model_name=None
):
    if not HAS_MATPLOTLIB:
        return None

    actual_model_name = model_name if model_name else MODEL_NAME
    x = range(len(concurrencies))

    def get_values(key):
        values = []
        for conc in concurrencies:
            val = chip_data.get(chip_name, {}).get(conc, {}).get(key, "0")
            try:
                values.append(float(val))
            except:
                values.append(0)
        return values

    colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c"]

    req_throughput = get_values("Request throughput (req/s)")
    total_tput = get_values("Total token throughput (tok/s)")
    output_tput = get_values("Output token throughput (tok/s)")
    e2e_latency = get_values("Mean E2E Latency (ms)")
    ttft_p99 = get_values("P99 TTFT (ms)")
    tpot_p99 = get_values("P99 TPOT (ms)")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(
        f"{actual_model_name} on {chip_name} - Concurrency Comparison",
        fontsize=14,
        fontweight="bold",
    )

    axes[0, 0].bar(x, req_throughput, color=colors[: len(concurrencies)], alpha=0.8)
    axes[0, 0].set_title("Request Throughput (req/s)", fontsize=11)
    axes[0, 0].set_xlabel("Concurrency")
    axes[0, 0].set_ylabel("req/s")
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(concurrencies, rotation=45)
    for i, v in enumerate(req_throughput):
        axes[0, 0].text(
            i,
            v + 0.02 * max(req_throughput) if max(req_throughput) > 0 else 0.1,
            f"{v:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    axes[0, 0].grid(axis="y", alpha=0.3)

    axes[0, 1].bar(x, output_tput, color=colors[: len(concurrencies)], alpha=0.8)
    axes[0, 1].set_title("Output Token Throughput (tok/s)", fontsize=11)
    axes[0, 1].set_xlabel("Concurrency")
    axes[0, 1].set_ylabel("tok/s")
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(concurrencies, rotation=45)
    for i, v in enumerate(output_tput):
        axes[0, 1].text(
            i,
            v + 0.02 * max(output_tput) if max(output_tput) > 0 else 1,
            f"{v:.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    axes[0, 1].grid(axis="y", alpha=0.3)

    axes[0, 2].bar(x, total_tput, color=colors[: len(concurrencies)], alpha=0.8)
    axes[0, 2].set_title("Total Token Throughput (tok/s)", fontsize=11)
    axes[0, 2].set_xlabel("Concurrency")
    axes[0, 2].set_ylabel("tok/s")
    axes[0, 2].set_xticks(x)
    axes[0, 2].set_xticklabels(concurrencies, rotation=45)
    for i, v in enumerate(total_tput):
        axes[0, 2].text(
            i,
            v + 0.02 * max(total_tput) if max(total_tput) > 0 else 100,
            f"{v:.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    axes[0, 2].grid(axis="y", alpha=0.3)

    axes[1, 0].bar(x, e2e_latency, color=colors[: len(concurrencies)], alpha=0.8)
    axes[1, 0].set_title("Mean E2E Latency (ms)", fontsize=11)
    axes[1, 0].set_xlabel("Concurrency")
    axes[1, 0].set_ylabel("ms")
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(concurrencies, rotation=45)
    for i, v in enumerate(e2e_latency):
        axes[1, 0].text(
            i,
            v + 0.02 * max(e2e_latency) if max(e2e_latency) > 0 else 10,
            f"{v:.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    axes[1, 0].grid(axis="y", alpha=0.3)

    axes[1, 1].bar(x, ttft_p99, color=colors[: len(concurrencies)], alpha=0.8)
    axes[1, 1].set_title("TTFT P99 (ms)", fontsize=11)
    axes[1, 1].set_xlabel("Concurrency")
    axes[1, 1].set_ylabel("ms")
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(concurrencies, rotation=45)
    for i, v in enumerate(ttft_p99):
        axes[1, 1].text(
            i,
            v + 0.02 * max(ttft_p99) if max(ttft_p99) > 0 else 10,
            f"{v:.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    axes[1, 1].grid(axis="y", alpha=0.3)

    axes[1, 2].bar(x, tpot_p99, color=colors[: len(concurrencies)], alpha=0.8)
    axes[1, 2].set_title("TPOT P99 (ms)", fontsize=11)
    axes[1, 2].set_xlabel("Concurrency")
    axes[1, 2].set_ylabel("ms")
    axes[1, 2].set_xticks(x)
    axes[1, 2].set_xticklabels(concurrencies, rotation=45)
    for i, v in enumerate(tpot_p99):
        axes[1, 2].text(
            i,
            v + 0.02 * max(tpot_p99) if max(tpot_p99) > 0 else 1,
            f"{v:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    axes[1, 2].grid(axis="y", alpha=0.3)

    for ax in axes.flat:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.set_facecolor("#f0f0f0")
    for ax in axes.flat:
        ax.set_facecolor("white")

    plt.tight_layout()

    chart_file = os.path.join(output_dir, "concurrency_comparison.png")
    plt.savefig(chart_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Generated chart: {chart_file}")
    return [chart_file]


def generate_performance_trends(
    chip_data, concurrencies, output_dir, chip_name, model_name=None
):
    if not HAS_MATPLOTLIB:
        return None

    actual_model_name = model_name if model_name else MODEL_NAME
    concurrencies_int = [int(c) for c in concurrencies]

    colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(
        f"{actual_model_name} on {chip_name} - Performance Trends by Concurrency",
        fontsize=14,
        fontweight="bold",
    )

    def get_values(key):
        return [
            float(chip_data.get(chip_name, {}).get(c, {}).get(key, 0) or 0)
            for c in concurrencies
        ]

    values = get_values("Request throughput (req/s)")
    axes[0, 0].plot(
        concurrencies_int,
        values,
        "-o",
        color=colors[0],
        linewidth=2,
        markersize=6,
        label="QPS",
    )
    axes[0, 0].set_title("Request Throughput (req/s)")
    axes[0, 0].set_xlabel("Concurrency")
    axes[0, 0].set_ylabel("req/s")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    values = get_values("Output token throughput (tok/s)")
    axes[0, 1].plot(
        concurrencies_int,
        values,
        "-o",
        color=colors[1],
        linewidth=2,
        markersize=6,
        label="Output",
    )
    axes[0, 1].set_title("Output Token Throughput (tok/s)")
    axes[0, 1].set_xlabel("Concurrency")
    axes[0, 1].set_ylabel("tok/s")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    values = get_values("Total token throughput (tok/s)")
    axes[0, 2].plot(
        concurrencies_int,
        values,
        "-o",
        color=colors[2],
        linewidth=2,
        markersize=6,
        label="Total",
    )
    axes[0, 2].set_title("Total Token Throughput (tok/s)")
    axes[0, 2].set_xlabel("Concurrency")
    axes[0, 2].set_ylabel("tok/s")
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)

    values_mean = get_values("Mean E2E Latency (ms)")
    values_p99 = get_values("P99 E2E Latency (ms)")
    axes[1, 0].plot(
        concurrencies_int,
        values_mean,
        "-o",
        color=colors[0],
        linewidth=2,
        markersize=6,
        label="Mean",
    )
    axes[1, 0].plot(
        concurrencies_int,
        values_p99,
        "--s",
        color=colors[1],
        linewidth=1,
        markersize=4,
        alpha=0.6,
        label="P99",
    )
    axes[1, 0].set_title("E2E Latency (ms)")
    axes[1, 0].set_xlabel("Concurrency")
    axes[1, 0].set_ylabel("ms")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    values_mean = get_values("Mean TTFT (ms)")
    values_p99 = get_values("P99 TTFT (ms)")
    axes[1, 1].plot(
        concurrencies_int,
        values_mean,
        "-o",
        color=colors[0],
        linewidth=2,
        markersize=6,
        label="Mean",
    )
    axes[1, 1].plot(
        concurrencies_int,
        values_p99,
        "--s",
        color=colors[1],
        linewidth=1,
        markersize=4,
        alpha=0.6,
        label="P99",
    )
    axes[1, 1].set_title("TTFT Latency (ms)")
    axes[1, 1].set_xlabel("Concurrency")
    axes[1, 1].set_ylabel("ms")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    values_mean = get_values("Mean TPOT (ms)")
    values_p99 = get_values("P99 TPOT (ms)")
    axes[1, 2].plot(
        concurrencies_int,
        values_mean,
        "-o",
        color=colors[0],
        linewidth=2,
        markersize=6,
        label="Mean",
    )
    axes[1, 2].plot(
        concurrencies_int,
        values_p99,
        "--s",
        color=colors[1],
        linewidth=1,
        markersize=4,
        alpha=0.6,
        label="P99",
    )
    axes[1, 2].set_title("TPOT Latency (ms)")
    axes[1, 2].set_xlabel("Concurrency")
    axes[1, 2].set_ylabel("ms")
    axes[1, 2].legend()
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()

    chart_file = os.path.join(output_dir, "performance_trends.png")
    plt.savefig(chart_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Generated performance trends chart: {chart_file}")
    return chart_file


def generate_io_comparison_csv(chip_data, io_labels, output_dir, chip_name):
    metric_names = [
        ("[Serving Benchmark Result]", ""),
        ("Request throughput (req/s)", "Request throughput (req/s)"),
        ("Output token throughput (tok/s)", "Output token throughput (tok/s)"),
        ("Total token throughput (tok/s)", "Total token throughput (tok/s)"),
        ("[End-to-End Latency]", ""),
        ("Mean E2E Latency (ms)", "Mean E2E Latency (ms)"),
        ("P99 E2E Latency (ms)", "P99 E2E Latency (ms)"),
        ("[Time to First Token]", ""),
        ("Mean TTFT (ms)", "Mean TTFT (ms)"),
        ("P99 TTFT (ms)", "P99 TTFT (ms)"),
        ("[Time per Output Token]", ""),
        ("Mean TPOT (ms)", "Mean TPOT (ms)"),
        ("P99 TPOT (ms)", "P99 TPOT (ms)"),
    ]

    csv_lines = []
    header = ["Metric"] + io_labels
    csv_lines.append(",".join(header))

    for display_name, key_name in metric_names:
        if not key_name:
            csv_lines.append(f"[{display_name}]" + ",," * (len(io_labels) - 1))
            continue

        row = [display_name]
        for io_key in io_labels:
            value = chip_data.get(chip_name, {}).get(io_key, {}).get(key_name, "")
            row.append(value)
        csv_lines.append(",".join(row))

    csv_file = os.path.join(output_dir, "io_comparison.csv")
    with open(csv_file, "w", encoding="utf-8") as f:
        f.write("\n".join(csv_lines))

    print(f"Generated: {csv_file}")
    return [csv_file]


def generate_io_comparison_charts(
    chip_data, io_labels, output_dir, chip_name, model_name=None, fixed_conc="32"
):
    if not HAS_MATPLOTLIB:
        return None

    actual_model_name = model_name if model_name else MODEL_NAME
    x = range(len(io_labels))

    def get_values(key):
        values = []
        for io_key in io_labels:
            val = chip_data.get(chip_name, {}).get(io_key, {}).get(key, "0")
            try:
                values.append(float(val))
            except:
                values.append(0)
        return values

    colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6", "#1abc9c"]

    req_throughput = get_values("Request throughput (req/s)")
    output_tput = get_values("Output token throughput (tok/s)")
    total_tput = get_values("Total token throughput (tok/s)")
    e2e_latency = get_values("Mean E2E Latency (ms)")
    ttft_p99 = get_values("P99 TTFT (ms)")
    tpot_p99 = get_values("P99 TPOT (ms)")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(
        f"{actual_model_name} on {chip_name} - I/O Comparison (Concurrency={fixed_conc})",
        fontsize=14,
        fontweight="bold",
    )

    axes[0, 0].bar(x, req_throughput, color=colors[: len(io_labels)], alpha=0.8)
    axes[0, 0].set_title("Request Throughput (req/s)", fontsize=11)
    axes[0, 0].set_xlabel("Input/Output Length")
    axes[0, 0].set_ylabel("req/s")
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(io_labels, rotation=45, ha="right")
    axes[0, 0].grid(axis="y", alpha=0.3)

    axes[0, 1].bar(x, output_tput, color=colors[: len(io_labels)], alpha=0.8)
    axes[0, 1].set_title("Output Token Throughput (tok/s)", fontsize=11)
    axes[0, 1].set_xlabel("Input/Output Length")
    axes[0, 1].set_ylabel("tok/s")
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(io_labels, rotation=45, ha="right")
    axes[0, 1].grid(axis="y", alpha=0.3)

    axes[0, 2].bar(x, total_tput, color=colors[: len(io_labels)], alpha=0.8)
    axes[0, 2].set_title("Total Token Throughput (tok/s)", fontsize=11)
    axes[0, 2].set_xlabel("Input/Output Length")
    axes[0, 2].set_ylabel("tok/s")
    axes[0, 2].set_xticks(x)
    axes[0, 2].set_xticklabels(io_labels, rotation=45, ha="right")
    axes[0, 2].grid(axis="y", alpha=0.3)

    axes[1, 0].bar(x, e2e_latency, color=colors[: len(io_labels)], alpha=0.8)
    axes[1, 0].set_title("Mean E2E Latency (ms)", fontsize=11)
    axes[1, 0].set_xlabel("Input/Output Length")
    axes[1, 0].set_ylabel("ms")
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(io_labels, rotation=45, ha="right")
    axes[1, 0].grid(axis="y", alpha=0.3)

    axes[1, 1].bar(x, ttft_p99, color=colors[: len(io_labels)], alpha=0.8)
    axes[1, 1].set_title("TTFT P99 (ms)", fontsize=11)
    axes[1, 1].set_xlabel("Input/Output Length")
    axes[1, 1].set_ylabel("ms")
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(io_labels, rotation=45, ha="right")
    axes[1, 1].grid(axis="y", alpha=0.3)

    axes[1, 2].bar(x, tpot_p99, color=colors[: len(io_labels)], alpha=0.8)
    axes[1, 2].set_title("TPOT P99 (ms)", fontsize=11)
    axes[1, 2].set_xlabel("Input/Output Length")
    axes[1, 2].set_ylabel("ms")
    axes[1, 2].set_xticks(x)
    axes[1, 2].set_xticklabels(io_labels, rotation=45, ha="right")
    axes[1, 2].grid(axis="y", alpha=0.3)

    for ax in axes.flat:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.set_facecolor("#f0f0f0")
    for ax in axes.flat:
        ax.set_facecolor("white")

    plt.tight_layout()

    chart_file = os.path.join(output_dir, "io_comparison.png")
    plt.savefig(chart_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Generated chart: {chart_file}")
    return [chart_file]


def generate_markdown_report_for_io_comparison(
    chip_data,
    io_pairs_sorted,
    output_dir,
    test_suite,
    chip_name,
    model_name=None,
    scenarios_config=None,
    fixed_conc="32",
):
    current_date = datetime.now().strftime("%Y-%m-%d")
    actual_model_name = model_name if model_name else MODEL_NAME

    def make_table_for_metric(key_name):
        values = []
        for io_pair in io_pairs_sorted:
            io_key = f"i{io_pair[0]}_o{io_pair[1]}"
            value = chip_data.get(chip_name, {}).get(io_key, {}).get(key_name, "")
            values.append(value)
        return " | ".join(values)

    io_header = " | ".join([f"input:{p[0]}, output:{p[1]}" for p in io_pairs_sorted])
    io_separator = " | ".join(["-----------"] * len(io_pairs_sorted))

    serving_metrics = [
        ("请求吞吐量 (req/s)", "Request throughput (req/s)"),
        ("输出token吞吐量 (tok/s)", "Output token throughput (tok/s)"),
        ("总token吞吐量 (tok/s)", "Total token throughput (tok/s)"),
    ]

    e2e_metrics = [
        ("平均E2E延迟 (ms)", "Mean E2E Latency (ms)"),
        ("P99 E2E延迟 (ms)", "P99 E2E Latency (ms)"),
    ]

    ttft_metrics = [
        ("平均TTFT (ms)", "Mean TTFT (ms)"),
        ("P99 TTFT (ms)", "P99 TTFT (ms)"),
    ]

    tpot_metrics = [
        ("平均TPOT (ms)", "Mean TPOT (ms)"),
        ("P99 TPOT (ms)", "P99 TPOT (ms)"),
    ]

    serving_table = "\n".join(
        [f"| {name} | {make_table_for_metric(key)} |" for name, key in serving_metrics]
    )
    e2e_table = "\n".join(
        [f"| {name} | {make_table_for_metric(key)} |" for name, key in e2e_metrics]
    )
    ttft_table = "\n".join(
        [f"| {name} | {make_table_for_metric(key)} |" for name, key in ttft_metrics]
    )
    tpot_table = "\n".join(
        [f"| {name} | {make_table_for_metric(key)} |" for name, key in tpot_metrics]
    )

    io_comparison_img = '<img src="./io_comparison.png" width="1000" />'

    md_content = f"""# {actual_model_name}模型在{chip_name}上的I/O对比测试报告

<div align="center">
**测试日期：** {current_date}
</div>

---

## 测试场景
固定并发数为 {fixed_conc}，比较不同输入输出长度下的性能表现。

---

## 📊 I/O对比测试汇总

| 指标 | {io_header} |
|------|{io_separator}|
{serving_table}

---

## ⏱️ 端到端延迟 (E2E Latency)

| 指标 | {io_header} |
|------|{io_separator}|
{e2e_table}

---

## ⏱️ 首Token延迟 (TTFT)

| 指标 | {io_header} |
|------|{io_separator}|
{ttft_table}

---

## ⚡ 每Token生成时间 (TPOT)

| 指标 | {io_header} |
|------|{io_separator}|
{tpot_table}

---

## 📊 I/O对比柱状图

{io_comparison_img}

---

<div align="center">
*报告生成时间: {current_date}*
</div>
"""

    md_file = os.path.join(
        output_dir, f"{actual_model_name}_{chip_name}_io_comparison.md"
    )
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Generated: {md_file}")
    return md_file


def generate_multi_io_markdown_report(
    all_chip_data,
    io_pairs,
    concurrencies,
    output_dir,
    test_suite,
    chip_name,
    model_name=None,
    scenarios_config=None,
):
    current_date = datetime.now().strftime("%Y-%m-%d")
    actual_model_name = model_name if model_name else MODEL_NAME

    chip_config = load_chip_config()
    sglang_config = load_sglang_config()
    chips_raw = chip_config.get("chips", {})
    sglang_configs_raw = sglang_config.get("sglang_configs", {})
    chip_configs_list = chips_raw.get(chip_name, [])
    if isinstance(chip_configs_list, list):
        chips_info = chip_configs_list[0] if chip_configs_list else {}
    else:
        chips_info = chip_configs_list if chip_configs_list else {}
    sglang_cfg_list = sglang_configs_raw.get(chip_name, [])
    if isinstance(sglang_cfg_list, list):
        sglang_cfg = sglang_cfg_list[0] if sglang_cfg_list else {}
    else:
        sglang_cfg = sglang_cfg_list if sglang_cfg_list else {}

    test_cfg = (
        scenarios_config.get("base_config", {}).get("params", {}).get(test_suite, {})
    )
    num_prompts = test_cfg.get("num-prompts", [])
    input_output_lens = test_cfg.get("random-input-output-len", [])

    def format_tokens(val):
        try:
            v = int(val)
            if v >= 1024:
                return f"{v // 1024}k"
            else:
                return f"{v / 1024:.2f}k"
        except:
            return str(val)

    if input_output_lens and isinstance(input_output_lens[0], list):
        input_len = [input_output_lens[0][0]]
        output_len = [input_output_lens[0][1]]
    else:
        input_len = test_cfg.get("random-input-len", [])
        output_len = test_cfg.get("random-output-len", [])

    input_ctx = format_tokens(input_len[0]) if input_len else "N/A"
    output_ctx = format_tokens(output_len[0]) if output_len else "N/A"

    chip_param_names = [
        "model_name",
        "quantization_config",
        "model_size",
        "max_position_embeddings",
        "temperature",
        "top_k",
        "top_p",
    ]
    chip_table_rows = []
    for param in chip_param_names:
        val = chips_info.get(param, "N/A")
        chip_table_rows.append(f"| **{param}** | {val} |")
    chip_table = "\n".join(chip_table_rows)

    sglang_param_mapping = {
        "model_name": "Model Name",
        "attention-backend": "Attention Backend",
        "quantization": "Quantization",
        "tp_size": "TP Size",
        "pp_size": "PP Size",
        "nnodes": "Num Nodes",
        "dtype": "Data Type",
        "context-length": "Context Length",
        "max-running-requests": "Max Running Requests",
    }
    sglang_table_rows = []
    for param, display_name in sglang_param_mapping.items():
        val = sglang_cfg.get(param, "N/A")
        if val is None:
            val = "N/A"
        sglang_table_rows.append(f"| **{display_name}** | {val} |")
    sglang_table = "\n".join(sglang_table_rows)

    sglang_version = scenarios_config.get("sglang_version", "N/A")
    fixed_conc_list = concurrencies

    def get_value(chip_data, conc, key):
        return chip_data.get(chip_name, {}).get(conc, {}).get(key, "N/A")

    if HAS_MATPLOTLIB:
        for io_key, io_info in all_chip_data.items():
            input_len = io_info["input_len"]
            output_len = io_info["output_len"]
            chip_data = io_info["data"]
            io_dir = os.path.join(output_dir, f"i{input_len}_o{output_len}")
            Path(io_dir).mkdir(parents=True, exist_ok=True)
            generate_comparison_charts(
                chip_data,
                concurrencies,
                io_dir,
                chip_name,
                f"{actual_model_name} (input:{input_len}, output:{output_len})",
            )

        chip_data_by_io_fixed_conc = defaultdict(lambda: defaultdict(dict))
        for fixed_conc in fixed_conc_list:
            for io_key, io_info in all_chip_data.items():
                input_len = io_info["input_len"]
                output_len = io_info["output_len"]
                chip_data = io_info["data"]
                io_key_label = f"i{input_len}_o{output_len}"
                chip_data_by_io_fixed_conc[fixed_conc][chip_name][io_key_label] = (
                    chip_data.get(chip_name, {}).get(fixed_conc, {})
                )

            if chip_data_by_io_fixed_conc[fixed_conc].get(chip_name):
                io_labels = [
                    f"i{io_info['input_len']}_o{io_info['output_len']}"
                    for io_info in all_chip_data.values()
                ]
                io_comparison_dir = os.path.join(
                    output_dir, f"compare_by_io_conc{fixed_conc}"
                )
                Path(io_comparison_dir).mkdir(parents=True, exist_ok=True)
                generate_io_comparison_charts(
                    chip_data_by_io_fixed_conc[fixed_conc],
                    io_labels,
                    io_comparison_dir,
                    chip_name,
                    actual_model_name,
                    fixed_conc,
                )

    io_sections = []
    for io_key, io_info in all_chip_data.items():
        input_len = io_info["input_len"]
        output_len = io_info["output_len"]
        io_label = io_info["io_label"]
        chip_data = io_info["data"]

        summary_rows = [
            "| 并发数 | 请求吞吐量 (req/s) | 输出Token吞吐量 (tok/s) | 总Token吞吐量 (tok/s) | TTFT P99 (ms) | TPOT P99 (ms) | E2E延迟均值 (ms) |"
        ]
        summary_rows.append("| " + " | ".join(["---------------"] * 7) + " |")

        for conc in concurrencies:
            req_tp = get_value(chip_data, conc, "Request throughput (req/s)")
            out_tp = get_value(chip_data, conc, "Output token throughput (tok/s)")
            total_tp = get_value(chip_data, conc, "Total token throughput (tok/s)")
            ttft_p99 = get_value(chip_data, conc, "P99 TTFT (ms)")
            tpot_p99 = get_value(chip_data, conc, "P99 TPOT (ms)")
            e2e_mean = get_value(chip_data, conc, "Mean E2E Latency (ms)")
            summary_rows.append(
                f"| {conc} | {req_tp} | {out_tp} | {total_tp} | {ttft_p99} | {tpot_p99} | {e2e_mean} |"
            )

        header = " | ".join([f"{conc} 并发" for conc in concurrencies])
        separator = "----------- | " + " | ".join(["-----------"] * len(concurrencies))

        serving_table_rows = [f"| 指标 | {header} |"]
        serving_table_rows.append(f"| {separator} |")

        serving_metrics = [
            ("成功请求数", "Successful requests"),
            ("测试持续时间 (s)", "Benchmark duration (s)"),
            ("总输入 tokens", "Total input tokens"),
            ("总生成 tokens", "Total generated tokens"),
            ("**请求吞吐量 (req/s)**", "Request throughput (req/s)"),
            ("**输出 token 吞吐量 (tok/s)**", "Output token throughput (tok/s)"),
            ("峰值输出 token 吞吐量 (tok/s)", "Peak output token throughput (tok/s)"),
            ("总 token 吞吐量 (tok/s)", "Total token throughput (tok/s)"),
        ]
        for display_name, key_name in serving_metrics:
            row = [f"| {display_name} |"]
            for conc in concurrencies:
                row.append(f" {get_value(chip_data, conc, key_name)} |")
            serving_table_rows.append("".join(row))

        ttft_table_rows = [f"| 指标 | {header} |"]
        ttft_table_rows.append(f"|{separator}|")
        ttft_metrics = [
            ("平均 TTFT (ms)", "Mean TTFT (ms)"),
            ("P99 TTFT (ms)", "P99 TTFT (ms)"),
        ]
        for display_name, key_name in ttft_metrics:
            row = [f"| {display_name} |"]
            for conc in concurrencies:
                row.append(f" {get_value(chip_data, conc, key_name)} |")
            ttft_table_rows.append("".join(row))

        tpot_table_rows = [f"| 指标 | {header} |"]
        tpot_table_rows.append(f"|{separator}|")
        tpot_metrics = [
            ("平均 TPOT (ms)", "Mean TPOT (ms)"),
            ("P99 TPOT (ms)", "P99 TPOT (ms)"),
        ]
        for display_name, key_name in tpot_metrics:
            row = [f"| {display_name} |"]
            for conc in concurrencies:
                row.append(f" {get_value(chip_data, conc, key_name)} |")
            tpot_table_rows.append("".join(row))

        itl_table_rows = [f"| 指标 | {header} |"]
        itl_table_rows.append(f"|{separator}|")
        itl_metrics = [
            ("平均 ITL (ms)", "Mean ITL (ms)"),
            ("P99 ITL (ms)", "P99 ITL (ms)"),
        ]
        for display_name, key_name in itl_metrics:
            row = [f"| {display_name} |"]
            for conc in concurrencies:
                row.append(f" {get_value(chip_data, conc, key_name)} |")
            itl_table_rows.append("".join(row))

        io_sections.append(
            {
                "io_label": io_label,
                "input_len": input_len,
                "output_len": output_len,
                "summary_table": "\n".join(summary_rows),
                "serving_table": "\n".join(serving_table_rows),
                "ttft_table": "\n".join(ttft_table_rows),
                "tpot_table": "\n".join(tpot_table_rows),
                "itl_table": "\n".join(itl_table_rows),
                "chip_data": chip_data,
            }
        )

    md_content = f"""# {actual_model_name}模型在{chip_name}上的多I/O测试报告

<div align="center">
**测试日期：** {current_date}
</div>

---

## 测试场景
测试不同输入输出长度和并发级别下的性能表现，分析同一芯片同一模型在不同输入输出长度和并发级别下的性能指标变化趋势。

**主要采集指标**：

| 指标                  | 单位         | 含义                                 |
|---------------------|------------|------------------------------------|
| E2E Latency         | ms         | End-to-End Latency，端到端延迟         |
| TTFT                | ms         | Time To First Token，首 token 延迟     |
| TPOT                | ms/token   | Time Per Output Token，每 token 生成时间 |
| ITL                 | ms         | Inter-Token Latency，token间延迟       |
| Throughput          | tokens/s   | 系统总吞吐                              |
| QPS                 | requests/s | 请求吞吐                               |

---

## 📊 测试概览

| 项目            | 配置                                     | 备注  |
|---------------|----------------------------------------|-----|
| **数据集**       | random                                 |     |
| **并发数**       | {", ".join(concurrencies)}    |     |
| **总请求数**      | {num_prompts[0] if num_prompts else "N/A"}                                    |     |
| **输入输出长度** | {", ".join([f"({p[0]}, {p[1]})" for p in io_pairs])} |     |
| **模型**        | {actual_model_name}                           |     |
| **被测芯片**      | {chip_name} |     |
| **SGLang版本**   | {sglang_version}                           |     |

---

## 🤖 芯片和模型配置信息

| 参数名称                    | {chip_name} |
|------------------------|-------------|
{chip_table}

---

## 🤖 SGLang启动配置信息

| 参数名称                   | {chip_name} |
|------------------------|-------------|
{sglang_table}

---

## 📋 各I/O测试汇总（随并发变化）

"""

    for io_sec in io_sections:
        md_content += f"### {io_sec['io_label']}\n\n"
        md_content += io_sec["summary_table"] + "\n\n"
        md_content += f"![性能图表](./i{io_sec['input_len']}_o{io_sec['output_len']}/concurrency_comparison.png)\n\n"
        md_content += "---\n\n"

    md_content += "## 📊 I/O对比（固定并发数）\n\n"

    for fixed_conc in fixed_conc_list:
        io_labels = [
            f"i{io_info['input_len']}_o{io_info['output_len']}"
            for io_info in all_chip_data.values()
        ]

        io_header = " | ".join(io_labels)
        io_sep = "--- | " + " | ".join(["---"] * len(io_labels))

        comp_rows = [f"| 指标 | {io_header} |"]
        comp_rows.append(f"| {io_sep} |")

        comp_metrics = [
            ("请求吞吐量 (req/s)", "Request throughput (req/s)"),
            ("输出Token吞吐量 (tok/s)", "Output token throughput (tok/s)"),
            ("总Token吞吐量 (tok/s)", "Total token throughput (tok/s)"),
            ("TTFT P99 (ms)", "P99 TTFT (ms)"),
            ("TPOT P99 (ms)", "P99 TPOT (ms)"),
            ("E2E延迟均值 (ms)", "Mean E2E Latency (ms)"),
        ]

        for display_name, key_name in comp_metrics:
            row = [f"| {display_name} |"]
            for io_info in io_sections:
                chip_data = io_info["chip_data"]
                value = get_value(chip_data, fixed_conc, key_name)
                row.append(f" {value} |")
            comp_rows.append("".join(row))

        md_content += f"### 并发数 = {fixed_conc}\n\n"
        md_content += "\n".join(comp_rows) + "\n\n"
        md_content += (
            f"![I/O对比](./compare_by_io_conc{fixed_conc}/io_comparison.png)\n\n"
        )
        md_content += "---\n\n"

    md_content += f"""## 📝 详细性能数据

"""

    for io_sec in io_sections:
        md_content += f"### {io_sec['io_label']}\n\n"

        md_content += f"#### 服务基准结果\n\n{io_sec['serving_table']}\n\n"

        md_content += f"#### TTFT\n\n{io_sec['ttft_table']}\n\n"

        md_content += f"#### TPOT\n\n{io_sec['tpot_table']}\n\n"

        md_content += f"#### ITL\n\n{io_sec['itl_table']}\n\n"

        md_content += "---\n\n"

    md_content += f"""
<div align="center">
*报告生成时间: {current_date}*
</div>
"""

    md_file = os.path.join(
        output_dir, f"{actual_model_name}_{chip_name}_multi_io_report.md"
    )
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Generated: {md_file}")
    return md_file

    io_sections = []
    for io_key, io_info in all_chip_data.items():
        input_len = io_info["input_len"]
        output_len = io_info["output_len"]
        io_label = io_info["io_label"]
        chip_data = io_info["data"]

        summary_rows = [
            "| 并发数 | 请求吞吐量 (req/s) | 输出Token吞吐量 (tok/s) | 总Token吞吐量 (tok/s) | TTFT P99 (ms) | TPOT P99 (ms) | E2E延迟均值 (ms) |"
        ]
        summary_rows.append("|" + "---|" * 7)

        for conc in concurrencies:
            req_tp = get_value(chip_data, conc, "Request throughput (req/s)")
            out_tp = get_value(chip_data, conc, "Output token throughput (tok/s)")
            total_tp = get_value(chip_data, conc, "Total token throughput (tok/s)")
            ttft_p99 = get_value(chip_data, conc, "P99 TTFT (ms)")
            tpot_p99 = get_value(chip_data, conc, "P99 TPOT (ms)")
            e2e_mean = get_value(chip_data, conc, "Mean E2E Latency (ms)")
            summary_rows.append(
                f"| {conc} | {req_tp} | {out_tp} | {total_tp} | {ttft_p99} | {tpot_p99} | {e2e_mean} |"
            )

        serving_table_rows = ["| 指标 | " + " | ".join(concurrencies) + " |"]
        serving_table_rows.append("|" + "---|" * (len(concurrencies) + 1))

        serving_metrics = [
            ("成功请求数", "Successful requests"),
            ("测试持续时间 (s)", "Benchmark duration (s)"),
            ("总输入 tokens", "Total input tokens"),
            ("总生成 tokens", "Total generated tokens"),
            ("请求吞吐量 (req/s)", "Request throughput (req/s)"),
            ("输出 token 吞吐量 (tok/s)", "Output token throughput (tok/s)"),
            ("峰值输出 token 吞吐量 (tok/s)", "Peak output token throughput (tok/s)"),
            ("总 token 吞吐量 (tok/s)", "Total token throughput (tok/s)"),
        ]
        for display_name, key_name in serving_metrics:
            row = [f"| {display_name} |"]
            for conc in concurrencies:
                row.append(f" {get_value(chip_data, conc, key_name)} |")
            serving_table_rows.append("".join(row))

        ttft_table_rows = ["| 指标 | " + " | ".join(concurrencies) + " |"]
        ttft_table_rows.append("|" + "---|" * (len(concurrencies) + 1))
        ttft_metrics = [
            ("平均 TTFT (ms)", "Mean TTFT (ms)"),
            ("P99 TTFT (ms)", "P99 TTFT (ms)"),
        ]
        for display_name, key_name in ttft_metrics:
            row = [f"| {display_name} |"]
            for conc in concurrencies:
                row.append(f" {get_value(chip_data, conc, key_name)} |")
            ttft_table_rows.append("".join(row))

        tpot_table_rows = ["| 指标 | " + " | ".join(concurrencies) + " |"]
        tpot_table_rows.append("|" + "---|" * (len(concurrencies) + 1))
        tpot_metrics = [
            ("平均 TPOT (ms)", "Mean TPOT (ms)"),
            ("P99 TPOT (ms)", "P99 TPOT (ms)"),
        ]
        for display_name, key_name in tpot_metrics:
            row = [f"| {display_name} |"]
            for conc in concurrencies:
                row.append(f" {get_value(chip_data, conc, key_name)} |")
            tpot_table_rows.append("".join(row))

        itl_table_rows = ["| 指标 | " + " | ".join(concurrencies) + " |"]
        itl_table_rows.append("|" + "---|" * (len(concurrencies) + 1))
        itl_metrics = [
            ("平均 ITL (ms)", "Mean ITL (ms)"),
            ("P99 ITL (ms)", "P99 ITL (ms)"),
        ]
        for display_name, key_name in itl_metrics:
            row = [f"| {display_name} |"]
            for conc in concurrencies:
                row.append(f" {get_value(chip_data, conc, key_name)} |")
            itl_table_rows.append("".join(row))

        io_sections.append(
            {
                "io_label": io_label,
                "input_len": input_len,
                "output_len": output_len,
                "summary_table": "\n".join(summary_rows),
                "serving_table": "\n".join(serving_table_rows),
                "ttft_table": "\n".join(ttft_table_rows),
                "tpot_table": "\n".join(tpot_table_rows),
                "itl_table": "\n".join(itl_table_rows),
                "chip_data": chip_data,
            }
        )

    md_content = f"""# {actual_model_name}模型在{chip_name}上的多I/O测试报告

<div align="center">
**测试日期：** {current_date}
</div>

---

## 测试场景
测试不同输入输出长度和并发级别下的性能表现。

| 项目 | 配置 |
|------|------|
| **并发数** | {", ".join(concurrencies)} |
| **总请求数** | {num_prompts[0] if num_prompts else "N/A"} |
| **输入输出长度** | {", ".join([f"({p[0]}, {p[1]})" for p in io_pairs])} |
| **模型** | {actual_model_name} |
| **被测芯片** | {chip_name} |

---

## 📋 各I/O测试汇总（随并发变化）

"""

    for io_sec in io_sections:
        md_content += f"### {io_sec['io_label']}\n\n"
        md_content += io_sec["summary_table"] + "\n\n"
        md_content += f"![性能图表](./i{io_sec['input_len']}_o{io_sec['output_len']}/concurrency_comparison.png)\n\n"
        md_content += "---\n\n"

    md_content += "## 📊 I/O对比（固定并发数）\n\n"

    for fixed_conc in fixed_conc_list:
        io_labels = [
            f"i{io_info['input_len']}_o{io_info['output_len']}"
            for io_info in all_chip_data.values()
        ]

        io_header = " | ".join(io_labels)
        io_sep = " | ".join(["---"] * len(io_labels)) + " |"

        comp_rows = ["| 指标 | " + io_header + " |"]
        comp_rows.append("|" + io_sep)

        comp_metrics = [
            ("请求吞吐量 (req/s)", "Request throughput (req/s)"),
            ("输出Token吞吐量 (tok/s)", "Output token throughput (tok/s)"),
            ("总Token吞吐量 (tok/s)", "Total token throughput (tok/s)"),
            ("TTFT P99 (ms)", "P99 TTFT (ms)"),
            ("TPOT P99 (ms)", "P99 TPOT (ms)"),
            ("E2E延迟均值 (ms)", "Mean E2E Latency (ms)"),
        ]

        for display_name, key_name in comp_metrics:
            row = [f"| {display_name} |"]
            for io_info in io_sections:
                chip_data = io_info["chip_data"]
                value = get_value(chip_data, fixed_conc, key_name)
                row.append(f" {value} |")
            comp_rows.append("".join(row))

        md_content += f"### 并发数 = {fixed_conc}\n\n"
        md_content += "\n".join(comp_rows) + "\n\n"
        md_content += (
            f"![I/O对比](./compare_by_io_conc{fixed_conc}/io_comparison.png)\n\n"
        )
        md_content += "---\n\n"

    md_content += f"""## 📝 详细性能数据

"""

    for io_sec in io_sections:
        md_content += f"### {io_sec['io_label']}\n\n"

        md_content += f"#### 服务基准结果\n\n{io_sec['serving_table']}\n\n"

        md_content += f"#### TTFT\n\n{io_sec['ttft_table']}\n\n"

        md_content += f"#### TPOT\n\n{io_sec['tpot_table']}\n\n"

        md_content += f"#### ITL\n\n{io_sec['itl_table']}\n\n"

        md_content += "---\n\n"

    md_content += f"""
<div align="center">
*报告生成时间: {current_date}*
</div>
"""

    md_file = os.path.join(
        output_dir, f"{actual_model_name}_{chip_name}_multi_io_report.md"
    )
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Generated: {md_file}")
    return md_file


def generate_performance_trends_csv(chip_data, concurrencies, output_dir, chip_name):
    metric_names = [
        ("[Serving Benchmark Result]", ""),
        ("Successful requests", "Successful requests"),
        ("Failed requests", "Failed requests"),
        ("Benchmark duration (s)", "Benchmark duration (s)"),
        ("Total input tokens", "Total input tokens"),
        ("Total generated tokens", "Total generated tokens"),
        ("Request throughput (req/s)", "Request throughput (req/s)"),
        ("Output token throughput (tok/s)", "Output token throughput (tok/s)"),
        (
            "Peak output token throughput (tok/s)",
            "Peak output token throughput (tok/s)",
        ),
        ("Peak concurrent requests", "Peak concurrent requests"),
        ("Total token throughput (tok/s)", "Total token throughput (tok/s)"),
        ("[End-to-End Latency]", ""),
        ("Mean E2E Latency (ms)", "Mean E2E Latency (ms)"),
        ("Median E2E Latency (ms)", "Median E2E Latency (ms)"),
        ("P90 E2E Latency (ms)", "P90 E2E Latency (ms)"),
        ("P99 E2E Latency (ms)", "P99 E2E Latency (ms)"),
        ("[Time to First Token]", ""),
        ("Mean TTFT (ms)", "Mean TTFT (ms)"),
        ("Median TTFT (ms)", "Median TTFT (ms)"),
        ("P99 TTFT (ms)", "P99 TTFT (ms)"),
        ("[Time per Output Token]", ""),
        ("Mean TPOT (ms)", "Mean TPOT (ms)"),
        ("Median TPOT (ms)", "Median TPOT (ms)"),
        ("P99 TPOT (ms)", "P99 TPOT (ms)"),
        ("[Inter-Token Latency]", ""),
        ("Mean ITL (ms)", "Mean ITL (ms)"),
        ("Median ITL (ms)", "Median ITL (ms)"),
        ("P95 ITL (ms)", "P95 ITL (ms)"),
        ("P99 ITL (ms)", "P99 ITL (ms)"),
    ]

    csv_lines = []
    header = ["Metric"] + [f"{conc}" for conc in concurrencies]
    csv_lines.append(",".join(header))

    for display_name, key_name in metric_names:
        if not key_name:
            csv_lines.append(f"[{display_name}]" + ",," * (len(concurrencies) - 1))
            continue

        row = [display_name]
        for conc in concurrencies:
            value = chip_data.get(chip_name, {}).get(conc, {}).get(key_name, "")
            row.append(value)
        csv_lines.append(",".join(row))

    csv_file = os.path.join(output_dir, "performance_trends.csv")
    with open(csv_file, "w", encoding="utf-8") as f:
        f.write("\n".join(csv_lines))

    print(f"Generated performance trends CSV: {csv_file}")
    return csv_file


def generate_analysis_content(chip_data, chip_name, concurrencies):
    analysis_lines = []

    low_conc = [c for c in concurrencies if int(c) <= 4]
    mid_conc = [c for c in concurrencies if 4 < int(c) <= 32]
    high_conc = [c for c in concurrencies if int(c) > 32]

    def get_avg_by_conc_range(key, conc_list):
        vals = []
        for c in conc_list:
            val = chip_data.get(chip_name, {}).get(c, {}).get(key, 0)
            try:
                vals.append(float(val))
            except:
                pass
        return sum(vals) / len(vals) if vals else 0

    def get_max_value(key):
        max_val = 0
        max_conc = None
        for c in concurrencies:
            val = chip_data.get(chip_name, {}).get(c, {}).get(key, 0)
            try:
                fval = float(val)
                if fval > max_val:
                    max_val = fval
                    max_conc = c
            except:
                pass
        return max_val, max_conc

    def get_min_value(key):
        min_val = float("inf")
        min_conc = None
        for c in concurrencies:
            val = chip_data.get(chip_name, {}).get(c, {}).get(key, float("inf"))
            try:
                fval = float(val)
                if fval > 0 and fval < min_val:
                    min_val = fval
                    min_conc = c
            except:
                pass
        return min_val if min_val != float("inf") else 0, min_conc

    throughputs = [
        float(
            chip_data.get(chip_name, {}).get(c, {}).get("Request throughput (req/s)", 0)
            or 0
        )
        for c in concurrencies
    ]
    avg_low_tp = get_avg_by_conc_range("Request throughput (req/s)", low_conc)
    avg_mid_tp = get_avg_by_conc_range("Request throughput (req/s)", mid_conc)
    avg_high_tp = (
        get_avg_by_conc_range("Request throughput (req/s)", high_conc)
        if high_conc
        else 0
    )

    max_tp, max_tp_conc = get_max_value("Request throughput (req/s)")

    analysis_lines.append("### 1. 吞吐量性能分析\n")
    analysis_lines.append(f"**请求吞吐量 (QPS)**: 随着并发级别增加，QPS持续上升。")
    if low_conc:
        analysis_lines.append(
            f"低并发({','.join(low_conc)})平均 QPS: {avg_low_tp:.2f} req/s；"
        )
    if mid_conc:
        analysis_lines.append(
            f"中并发({','.join(mid_conc)})平均 QPS: {avg_mid_tp:.2f} req/s；"
        )
    if high_conc:
        analysis_lines.append(
            f"高并发({','.join(high_conc)})平均 QPS: {avg_high_tp:.2f} req/s；"
        )
    analysis_lines.append(
        f"最高 QPS 出现在 {max_tp_conc} 并发，达到 {max_tp:.2f} req/s。\n"
    )

    total_tput, total_tput_conc = get_max_value("Total token throughput (tok/s)")
    analysis_lines.append(
        f"**Token总吞吐量**: 最高达到 {total_tput:.0f} tok/s ({total_tput_conc} 并发)。\n"
    )

    e2e_p99, e2e_p99_conc = get_max_value("P99 E2E Latency (ms)")
    e2e_p99_min, _ = get_min_value("P99 E2E Latency (ms)")
    e2e_avg_low = get_avg_by_conc_range("P99 E2E Latency (ms)", low_conc)
    e2e_avg_high = (
        get_avg_by_conc_range("P99 E2E Latency (ms)", high_conc) if high_conc else 0
    )

    analysis_lines.append("### 2. 端到端延迟 (E2E Latency) 分析\n")
    analysis_lines.append(f"E2E延迟随并发增加显著上升。")
    if low_conc:
        analysis_lines.append(f"低并发平均 P99 E2E: {e2e_avg_low:.0f}ms；")
    if high_conc:
        analysis_lines.append(f"高并发平均 P99 E2E: {e2e_avg_high:.0f}ms；")
    analysis_lines.append(
        f"最高 P99 E2E 出现在 {e2e_p99_conc} 并发，达到 {e2e_p99:.0f}ms。\n"
    )

    ttft_p99, ttft_p99_conc = get_max_value("P99 TTFT (ms)")
    ttft_p99_min, _ = get_min_value("P99 TTFT (ms)")
    ttft_avg_low = get_avg_by_conc_range("P99 TTFT (ms)", low_conc)
    ttft_avg_high = (
        get_avg_by_conc_range("P99 TTFT (ms)", high_conc) if high_conc else 0
    )

    analysis_lines.append("### 3. 首Token延迟 (TTFT) 分析\n")
    analysis_lines.append(f"TTFT随并发增加显著上升。")
    if low_conc:
        analysis_lines.append(f"低并发平均 P99 TTFT: {ttft_avg_low:.0f}ms；")
    if high_conc:
        analysis_lines.append(f"高并发平均 P99 TTFT: {ttft_avg_high:.0f}ms；")
    analysis_lines.append(
        f"最高 P99 TTFT 出现在 {ttft_p99_conc} 并发，达到 {ttft_p99:.0f}ms。\n"
    )

    tpot_p99, tpot_p99_conc = get_max_value("P99 TPOT (ms)")
    tpot_avg_low = get_avg_by_conc_range("P99 TPOT (ms)", low_conc)
    tpot_avg_high = (
        get_avg_by_conc_range("P99 TPOT (ms)", high_conc) if high_conc else 0
    )

    analysis_lines.append("### 4. Token生成时间 (TPOT) 分析\n")
    analysis_lines.append(f"TPOT随并发增加也呈上升趋势。")
    if low_conc:
        analysis_lines.append(f"低并发平均 P99 TPOT: {tpot_avg_low:.2f}ms；")
    if high_conc:
        analysis_lines.append(f"高并发平均 P99 TPOT: {tpot_avg_high:.2f}ms；")
    analysis_lines.append(
        f"最高 P99 TPOT 出现在 {tpot_p99_conc} 并发，达到 {tpot_p99:.2f}ms。\n"
    )

    itl_p99, itl_p99_conc = get_max_value("P99 ITL (ms)")
    itl_avg_low = get_avg_by_conc_range("P99 ITL (ms)", low_conc)
    itl_avg_high = get_avg_by_conc_range("P99 ITL (ms)", high_conc) if high_conc else 0

    analysis_lines.append("### 5. Token间延迟 (ITL) 分析\n")
    analysis_lines.append(f"ITL随并发增加呈上升趋势。")
    if low_conc:
        analysis_lines.append(f"低并发平均 P99 ITL: {itl_avg_low:.2f}ms；")
    if high_conc:
        analysis_lines.append(f"高并发平均 P99 ITL: {itl_avg_high:.2f}ms；")
    analysis_lines.append(
        f"最高 P99 ITL 出现在 {itl_p99_conc} 并发，达到 {itl_p99:.2f}ms。\n"
    )

    analysis_lines.append("### 6. 综合评估\n")
    if throughputs:
        growth_rate = (
            (throughputs[-1] / throughputs[0] - 1) * 100 if throughputs[0] > 0 else 0
        )
        analysis_lines.append(
            f"**吞吐量增长**: 从最低并发到最高并发，QPS增长了 {growth_rate:.1f}%。"
        )

    if e2e_p99 > 0 and e2e_avg_low > 0:
        e2e_growth = (e2e_p99 / e2e_avg_low - 1) * 100 if e2e_avg_low > 0 else 0
        analysis_lines.append(
            f"**E2E延迟恶化**: 高并发相比低并发，E2E P99增加了 {e2e_growth:.1f}%。"
        )

    if ttft_p99 > 0 and ttft_avg_low > 0:
        ttft_growth = (ttft_p99 / ttft_avg_low - 1) * 100 if ttft_avg_low > 0 else 0
        analysis_lines.append(
            f"**TTFT延迟恶化**: 高并发相比低并发，TTFT P99增加了 {ttft_growth:.1f}%。"
        )

    if tpot_p99 > 0 and tpot_avg_low > 0:
        tpot_growth = (tpot_p99 / tpot_avg_low - 1) * 100 if tpot_avg_low > 0 else 0
        analysis_lines.append(
            f"**TPOT延迟恶化**: 高并发相比低并发，TPOT P99增加了 {tpot_growth:.1f}%。"
        )

    conclusion = "\n".join(analysis_lines)
    return conclusion


def generate_markdown_report(
    chip_data,
    concurrencies,
    output_dir,
    test_suite,
    chip_name,
    model_name=None,
    scenarios_config=None,
    io_label=None,
):
    current_date = datetime.now().strftime("%Y-%m-%d")

    actual_model_name = model_name if model_name else MODEL_NAME
    model_key = actual_model_name

    io_section_title = f" ({io_label})" if io_label else ""

    chip_config = load_chip_config()
    sglang_config = load_sglang_config()

    chips_raw = chip_config.get("chips", {})
    sglang_configs_raw = sglang_config.get("sglang_configs", {})

    chip_configs_list = chips_raw.get(chip_name, [])
    if isinstance(chip_configs_list, list):
        for cfg in chip_configs_list:
            if cfg.get("model_name") == model_key:
                chips_info = cfg
                break
        else:
            chips_info = chip_configs_list[0] if chip_configs_list else {}
    else:
        chips_info = chip_configs_list if chip_configs_list else {}

    sglang_cfg_list = sglang_configs_raw.get(chip_name, [])
    if isinstance(sglang_cfg_list, list):
        for cfg in sglang_cfg_list:
            if cfg.get("model_name") == model_key:
                sglang_cfg = cfg
                break
        else:
            sglang_cfg = sglang_cfg_list[0] if sglang_cfg_list else {}
    else:
        sglang_cfg = sglang_cfg_list if sglang_cfg_list else {}

    if scenarios_config is None:
        scenarios_config = load_models_scenarios()

    base_config = scenarios_config.get("base_config", {})
    params = base_config.get("params", {})
    test_cfg = params.get(test_suite, {})

    models_config = scenarios_config.get("models", {})
    chip_models = models_config.get(chip_name, [])
    model_info = chip_models[0] if chip_models else {}
    model_path = model_info.get("model_path", "N/A")

    def make_table_for_metric(key_name):
        values = []
        for conc in concurrencies:
            value = chip_data.get(chip_name, {}).get(conc, {}).get(key_name, "")
            values.append(value)
        return " | ".join(values)

    serving_metrics = [
        ("成功请求数", "Successful requests"),
        ("测试持续时间 (s)", "Benchmark duration (s)"),
        ("总输入 tokens", "Total input tokens"),
        ("总生成 tokens", "Total generated tokens"),
        ("**请求吞吐量 (req/s)**", "Request throughput (req/s)"),
        ("**输出 token 吞吐量 (tok/s)**", "Output token throughput (tok/s)"),
        ("峰值输出 token 吞吐量 (tok/s)", "Peak output token throughput (tok/s)"),
        ("峰值并发请求数", "Peak concurrent requests"),
        ("**总 token 吞吐量 (tok/s)**", "Total token throughput (tok/s)"),
    ]

    e2e_metrics = [
        ("平均 E2E 延迟 (ms)", "Mean E2E Latency (ms)"),
        ("中位 E2E 延迟 (ms)", "Median E2E Latency (ms)"),
        ("P90 E2E 延迟 (ms)", "P90 E2E Latency (ms)"),
        ("P99 E2E 延迟 (ms)", "P99 E2E Latency (ms)"),
    ]

    ttft_metrics = [
        ("平均 TTFT (ms)", "Mean TTFT (ms)"),
        ("中位 TTFT (ms)", "Median TTFT (ms)"),
        ("P99 TTFT (ms)", "P99 TTFT (ms)"),
    ]

    tpot_metrics = [
        ("平均 TPOT (ms)", "Mean TPOT (ms)"),
        ("中位 TPOT (ms)", "Median TPOT (ms)"),
        ("P99 TPOT (ms)", "P99 TPOT (ms)"),
    ]

    itl_metrics = [
        ("平均 ITL (ms)", "Mean ITL (ms)"),
        ("中位 ITL (ms)", "Median ITL (ms)"),
        ("P95 ITL (ms)", "P95 ITL (ms)"),
        ("P99 ITL (ms)", "P99 ITL (ms)"),
    ]

    header = " | ".join([f"{conc} 并发" for conc in concurrencies])
    separator = " | ".join(["-----------"] * len(concurrencies))

    serving_table = "\n".join(
        [f"| {name} | {make_table_for_metric(key)} |" for name, key in serving_metrics]
    )

    e2e_table = "\n".join(
        [f"| {name} | {make_table_for_metric(key)} |" for name, key in e2e_metrics]
    )

    ttft_table = "\n".join(
        [f"| {name} | {make_table_for_metric(key)} |" for name, key in ttft_metrics]
    )

    tpot_table = "\n".join(
        [f"| {name} | {make_table_for_metric(key)} |" for name, key in tpot_metrics]
    )

    itl_table = "\n".join(
        [f"| {name} | {make_table_for_metric(key)} |" for name, key in itl_metrics]
    )

    summary_table_rows = [
        "| 并发数 | 请求吞吐量 (req/s) | 输出Token吞吐量 (tok/s) | 总Token吞吐量 (tok/s) | TTFT P99 (ms) | TPOT P99 (ms) | E2E延迟均值 (ms) |"
    ]
    summary_table_rows.append("| " + " | ".join(["-----------"] * 7) + " |")
    for conc in concurrencies:
        req_tp = (
            chip_data.get(chip_name, {})
            .get(conc, {})
            .get("Request throughput (req/s)", "N/A")
        )
        out_tp = (
            chip_data.get(chip_name, {})
            .get(conc, {})
            .get("Output token throughput (tok/s)", "N/A")
        )
        total_tp = (
            chip_data.get(chip_name, {})
            .get(conc, {})
            .get("Total token throughput (tok/s)", "N/A")
        )
        ttft_p99 = (
            chip_data.get(chip_name, {}).get(conc, {}).get("P99 TTFT (ms)", "N/A")
        )
        tpot_p99 = (
            chip_data.get(chip_name, {}).get(conc, {}).get("P99 TPOT (ms)", "N/A")
        )
        e2e_mean = (
            chip_data.get(chip_name, {})
            .get(conc, {})
            .get("Mean E2E Latency (ms)", "N/A")
        )
        summary_table_rows.append(
            f"| {conc} | {req_tp} | {out_tp} | {total_tp} | {ttft_p99} | {tpot_p99} | {e2e_mean} |"
        )
    summary_table = "\n".join(summary_table_rows)

    analysis_content = generate_analysis_content(chip_data, chip_name, concurrencies)

    concurrency_comparison_img = (
        '<img src="./concurrency_comparison.png" width="1000" />'
    )
    performance_trends_img = '<img src="./performance_trends.png" width="1000" />'

    def format_tokens(val):
        try:
            v = int(val)
            if v >= 1024:
                return f"{v // 1024}k"
            else:
                return f"{v / 1024:.2f}k"
        except:
            return str(val)

    dataset = test_cfg.get("dataset-name", "random")
    num_prompts = test_cfg.get("num-prompts", [])
    input_output_lens = test_cfg.get("random-input-output-len", [])
    if (
        input_output_lens
        and isinstance(input_output_lens[0], list)
        and len(input_output_lens[0]) >= 2
    ):
        input_len = [input_output_lens[0][0]]
        output_len = [input_output_lens[0][1]]
    else:
        input_len = test_cfg.get("random-input-len", [])
        output_len = test_cfg.get("random-output-len", [])

    input_ctx = format_tokens(input_len[0]) if input_len else "N/A"
    output_ctx = format_tokens(output_len[0]) if output_len else "N/A"

    chip_info = chips_info
    chip_param_names = [
        "model_name",
        "quantization_config",
        "model_size",
        "max_position_embeddings",
        "temperature",
        "top_k",
        "top_p",
    ]
    chip_table_rows = []
    for param in chip_param_names:
        val = chip_info.get(param, "N/A")
        chip_table_rows.append(f"| **{param}** | {val} |")
    chip_table = "\n".join(chip_table_rows)

    sglang_param_mapping = {
        "model_name": "Model Name",
        "attention-backend": "Attention Backend",
        "quantization": "Quantization",
        "tp_size": "TP Size",
        "pp_size": "PP Size",
        "nnodes": "Num Nodes",
        "dtype": "Data Type",
        "context-length": "Context Length",
        "max-running-requests": "Max Running Requests",
        "max-queued-requests": "Max Queued Requests",
        "disable-radix-cach": "Disable Radix Cache",
        "tool-call-parser": "Tool Call Parser",
        "reasoning-parser": "Reasoning Parser",
        "mem-fraction-static": "Memory Fraction Static",
    }
    sglang_table_rows = []
    for param, display_name in sglang_param_mapping.items():
        val = sglang_cfg.get(param, "N/A")
        if val is None:
            val = "N/A"
        sglang_table_rows.append(f"| **{display_name}** | {val} |")
    sglang_table = "\n".join(sglang_table_rows)

    remark = sglang_cfg.get("remarks", "")
    remarks_section = f"- **{chip_name}**: {remark}" if remark else ""

    sglang_version = scenarios_config.get("sglang_version", "N/A")

    md_content = f"""# {actual_model_name}模型在{chip_name}上的Benchmark基准测试报告{io_section_title}

<div align="center">
**测试日期：** {current_date}

</div>

---

## 测试场景
在固定请求数，输入上下文和输出上下文长度下，使用sglang bench serve工具对并发数逐级增加场景的性能基准验证。分析同一芯片同一模型在不同并发级别下的性能指标变化趋势。

**主要采集指标**：

| 指标                  | 单位         | 含义                                 |
|---------------------|------------|------------------------------------|
| E2E Latency         | ms         | End-to-End Latency，端到端延迟         |
| TTFT                | ms         | Time To First Token，首 token 延迟     |
| TPOT                | ms/token   | Time Per Output Token，每 token 生成时间 |
| ITL                 | ms         | Inter-Token Latency，token间延迟       |
| Throughput          | tokens/s   | 系统总吞吐                              |
| QPS                 | requests/s | 请求吞吐                               |


## 📊 测试概览

| 项目            | 配置                                     | 备注  |
|---------------|----------------------------------------|-----|
| **数据集**       | {dataset}                                 |     |
| **并发数**       | {", ".join(concurrencies)}    |     |
| **总请求数**      | {num_prompts[0] if num_prompts else "N/A"}                                    |     |
| **请求输入上下文长度** | {input_len[0] if input_len else "N/A"}（{input_ctx}）                             |     |
| **请求输出上下文长度** | {output_len[0] if output_len else "N/A"}（{output_ctx}）                             |     |
| **模型**        | {actual_model_name}                           |     |
| **被测芯片**      | {chip_name} |     |
| **SGLang版本**   | {sglang_version}                           |     |

---

## 🤖 芯片和模型配置信息

| 参数名称                    | {chip_name} |
|------------------------|-------------|
{chip_table}

---

## 🤖 SGLang启动配置信息

| 参数名称                   | {chip_name} |
|------------------------|-------------|
{sglang_table}

{remarks_section}

---

## 📋 测试汇总

{summary_table}

---

## 📊 各并发级别性能柱状图

{concurrency_comparison_img}

---

## 📈 性能趋势分析

{performance_trends_img}

---

## 🎯 服务基准结果

| 指标 | {header} |
|------|{separator}|
{serving_table}

---

## ⏱️ 端到端延迟 (E2E Latency)

| 指标 | {header} |
|------|{separator}|
{e2e_table}

---

## ⏱️ 首Token延迟 (TTFT)

| 指标 | {header} |
|------|{separator}|
{ttft_table}

---

## ⚡ 每Token生成时间 (TPOT)

| 指标 | {header} |
|------|{separator}|
{tpot_table}

---

## 🔄 Token间延迟 (ITL)

| 指标 | {header} |
|------|{separator}|
{itl_table}

---

## 📝 分析总结

{analysis_content}

---

<div align="center">
*报告生成时间: {current_date}*
</div>
"""

    md_file = os.path.join(
        output_dir, f"{actual_model_name}_{chip_name}_concurrency.md"
    )
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Generated: {md_file}")
    return md_file


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate single chip benchmark report"
    )
    parser.add_argument(
        "--chip",
        type=str,
        default=None,
        help="Chip name (e.g., inspur_MetaX_C500)",
    )
    parser.add_argument(
        "--model", type=str, default=None, help="Model name (e.g., MiniMax-M2.5-W8A8)"
    )
    parser.add_argument(
        "--test-suite", type=str, default=None, help="Test suite name (e.g., test_01)"
    )
    parser.add_argument("--run-id", type=str, default=None, help="Run ID (e.g., 01)")
    args = parser.parse_args()

    chip_to_use = args.chip.strip() if args.chip else list(CHIP_BASE_PATHS.keys())[0]

    model_input = args.model.strip() if args.model else MODEL_NAME
    model_to_use = model_input
    model_default = MODEL_NAME

    if not args.model:
        model_to_use = model_default

    test_suite_to_use = args.test_suite.strip() if args.test_suite else TEST_SUITES[0]
    run_id_to_use = args.run_id.strip() if args.run_id else RUN_ID

    scenarios_config = load_models_scenarios()

    base_path = f"reports/{chip_to_use}/benchmark/{model_to_use}"

    if not os.path.exists(base_path):
        print(f"\nError: No data found for chip={chip_to_use}, model={model_to_use}")
        print(f"Expected path: {base_path}")

        available_reports = f"reports/{chip_to_use}/benchmark/"
        if os.path.exists(available_reports):
            print(f"Available model reports:")
            for item in os.listdir(available_reports):
                print(f"  - {item}")
        return

    full_base_path = f"{base_path}/{test_suite_to_use}/{run_id_to_use}"

    if not os.path.exists(full_base_path):
        print(
            f"\nError: No data found for {chip_to_use}/{model_to_use} test_suite={test_suite_to_use} run_id={run_id_to_use}"
        )
        print(f"Expected path: {full_base_path}")
        return

    chip_configs = [
        {
            "name": chip_to_use,
            "base_path": full_base_path,
        }
    ]

    print(f"\n{'#' * 60}")
    print(
        f"Processing: chip={chip_to_use}, model={model_to_use}, test_suite={test_suite_to_use}, run_id={run_id_to_use}"
    )
    print(f"{'#' * 60}\n")

    for chip in chip_configs:
        chip_name = chip["name"]
        output_base = f"analysis/single_chip/{chip_name}/{model_to_use}/{test_suite_to_use}/{run_id_to_use}"

        test_cfg = (
            scenarios_config.get("base_config", {})
            .get("params", {})
            .get(test_suite_to_use, {})
        )
        input_output_lens = test_cfg.get("random-input-output-len", [])
        is_multi_io = len(input_output_lens) > 1

        if is_multi_io:
            io_pairs = get_all_input_output_pairs(chip)
            print(f"Detected multi input/output scenario: {len(io_pairs)} pairs")

            all_concurrencies = set()
            for io_pair in io_pairs:
                for conc in range(1, 129):
                    metrics = get_chip_metrics(chip, str(conc), io_pair[0], io_pair[1])
                    if metrics:
                        all_concurrencies.add(str(conc))

            concurrencies = sorted(all_concurrencies, key=lambda x: int(x))
            print(
                f"Found {len(concurrencies)} concurrency levels: {', '.join(concurrencies)}"
            )

            Path(output_base).mkdir(parents=True, exist_ok=True)

            all_chip_data = {}

            for io_pair in io_pairs:
                input_len, output_len = io_pair
                io_label = f"input: {input_len}, output: {output_len}"
                io_key = f"i{input_len}_o{output_len}"
                print(f"\nProcessing I/O pair: {io_label}")

                chip_data = defaultdict(lambda: defaultdict(dict))

                for conc in concurrencies:
                    metrics = get_chip_metrics(chip, conc, input_len, output_len)
                    if metrics:
                        chip_data[chip_name][conc] = metrics
                        print(f"  - {conc}并发: OK")
                    else:
                        print(f"  - {conc}并发: No data")

                if chip_data[chip_name]:
                    all_chip_data[io_key] = {
                        "input_len": input_len,
                        "output_len": output_len,
                        "io_label": io_label,
                        "data": chip_data,
                    }

            generate_multi_io_markdown_report(
                all_chip_data,
                io_pairs,
                concurrencies,
                output_base,
                test_suite_to_use,
                chip_name,
                model_name=model_to_use,
                scenarios_config=scenarios_config,
            )

            print(f"\n{'=' * 50}")
            print(
                f"Multi-I/O analysis for {chip_name} - {test_suite_to_use} generated successfully!"
            )
            print(f"Output directory: {output_base}")
            print(f"{'=' * 50}")

        else:
            all_concurrencies = set()
            concs = get_all_concurrencies(chip)
            all_concurrencies.update(concs)

            if not all_concurrencies:
                print(
                    f"No concurrency configurations found for {chip_name} / {test_suite_to_use}!"
                )
                continue

            concurrencies = sorted(all_concurrencies, key=lambda x: int(x))
            print(
                f"Found {len(concurrencies)} concurrency levels: {', '.join(concurrencies)}"
            )

            Path(output_base).mkdir(parents=True, exist_ok=True)

            chip_data = defaultdict(lambda: defaultdict(dict))

            print(f"\nProcessing chip: {chip_name}")

            for conc in concurrencies:
                metrics = get_chip_metrics(chip, conc)
                if metrics:
                    chip_data[chip_name][conc] = metrics
                    print(f"  - {conc}并发: OK")
                else:
                    print(f"  - {conc}并发: No data")

            print("\nGenerating comparison reports...")

            generate_comparison_csv(chip_data, concurrencies, output_base, chip_name)

            if HAS_MATPLOTLIB:
                generate_comparison_charts(
                    chip_data, concurrencies, output_base, chip_name, model_to_use
                )
                generate_performance_trends(
                    chip_data, concurrencies, output_base, chip_name, model_to_use
                )

            generate_performance_trends_csv(
                chip_data, concurrencies, output_base, chip_name
            )

            generate_markdown_report(
                chip_data,
                concurrencies,
                output_base,
                test_suite_to_use,
                chip_name,
                model_name=model_to_use,
                scenarios_config=scenarios_config,
            )

            print(f"\n{'=' * 50}")
            print(
                f"Single chip analysis for {chip_name} - {test_suite_to_use} generated successfully!"
            )
            print(f"Output directory: {output_base}")
            print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
