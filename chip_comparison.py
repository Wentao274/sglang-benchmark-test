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


TEST_SUITES = ["test_01"]

RUN_IDS = ["01", "01"]

CHIP_BASE_PATHS = {
    "inspur_MetaX_C550": "reports/benchmark/inspur_MetaX_C550/MiniMax-M2.5-W8A8",
    "nvidia_h100": "reports/benchmark/nvidia_h100/MiniMax-M2.5",
}

MODEL_NAME = "MiniMax-M2.5-W8A8,MiniMax-M2.5"


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


def load_models_scenarios(config_path="config/models_scenarios.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_test_suite_config(test_suite, scenarios_config):
    base_config = scenarios_config.get("base_config", {})
    params = base_config.get("params", {})
    return params.get(test_suite, {})


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


def get_chip_metrics(chip_config, concurrency):
    base_path = chip_config["base_path"]
    chip_name = chip_config["name"]

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


COMPARISON_METRICS = [
    ("Request throughput (req/s)", "Request throughput (req/s)"),
    ("Output token throughput (tok/s)", "Output token throughput (tok/s)"),
    ("Total token throughput (tok/s)", "Total token throughput (tok/s)"),
    ("P99 TTFT (ms)", "P99 TTFT (ms)"),
    ("P99 TPOT (ms)", "P99 TPOT (ms)"),
    ("P99 ITL (ms)", "P99 ITL (ms)"),
]


def generate_comparison_csv(
    chip_data, concurrencies, output_dir, test_suite, chip_names
):
    chip_suffix = "_vs_".join([c.lower() for c in chip_names])

    csv_lines = []
    header = ["Metric"] + [f"{conc} 并发" for conc in concurrencies]
    csv_lines.append(",".join(header))

    for display_name, key_name in COMPARISON_METRICS:
        row = [display_name]
        for conc in concurrencies:
            values = []
            for chip in chip_names:
                value = chip_data.get(chip, {}).get(conc, {}).get(key_name, "")
                values.append(value)
            row.append(
                "/".join(values) if len(values) > 1 else values[0] if values else ""
            )
        csv_lines.append(",".join(row))

    csv_file = os.path.join(output_dir, f"comparison_{test_suite}_{chip_suffix}.csv")
    with open(csv_file, "w", encoding="utf-8") as f:
        f.write("\n".join(csv_lines))

    print(f"Generated: {csv_file}")
    return [csv_file]


def generate_comparison_charts(
    chip_data, concurrencies, output_dir, test_suite, chip_names, model_display=None
):
    if not HAS_MATPLOTLIB:
        return None

    chip_suffix = "_vs_".join([c.lower() for c in chip_names])
    if model_display is None:
        model_display = "_vs_".join([chip_names[0]])
    x = range(len(chip_names))

    def get_values(key):
        values = []
        for chip in chip_names:
            chip_vals = []
            for conc in concurrencies:
                val = chip_data.get(chip, {}).get(conc, {}).get(key, "0")
                try:
                    chip_vals.append(float(val))
                except:
                    chip_vals.append(0)
            values.append(chip_vals)
        return values

    colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]

    req_throughput = get_values("Request throughput (req/s)")
    output_tput = get_values("Output token throughput (tok/s)")
    total_tput = get_values("Total token throughput (tok/s)")
    ttft_p99 = get_values("P99 TTFT (ms)")
    tpot_p99 = get_values("P99 TPOT (ms)")
    itl_p99 = get_values("P99 ITL (ms)")

    chart_files = []

    for conc in concurrencies:
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(
            f"{model_display} Chip Comparison @ {conc} Concurrency",
            fontsize=14,
            fontweight="bold",
        )

        idx = concurrencies.index(conc)

        values = [req_throughput[i][idx] for i in range(len(chip_names))]
        axes[0, 0].bar(chip_names, values, color=colors[: len(chip_names)], alpha=0.8)
        axes[0, 0].set_title("Request Throughput (req/s)", fontsize=11)
        axes[0, 0].set_ylabel("req/s")
        axes[0, 0].tick_params(axis="x", rotation=15)
        for i, v in enumerate(values):
            axes[0, 0].text(
                i,
                v + 0.02 * max(values) if max(values) > 0 else 0.1,
                f"{v:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        axes[0, 0].grid(axis="y", alpha=0.3)

        values = [output_tput[i][idx] for i in range(len(chip_names))]
        axes[0, 1].bar(chip_names, values, color=colors[: len(chip_names)], alpha=0.8)
        axes[0, 1].set_title("Output Token Throughput (tok/s)", fontsize=11)
        axes[0, 1].set_ylabel("tok/s")
        axes[0, 1].tick_params(axis="x", rotation=15)
        for i, v in enumerate(values):
            axes[0, 1].text(
                i,
                v + 0.02 * max(values) if max(values) > 0 else 100,
                f"{v:.0f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        axes[0, 1].grid(axis="y", alpha=0.3)

        values = [total_tput[i][idx] for i in range(len(chip_names))]
        axes[0, 2].bar(chip_names, values, color=colors[: len(chip_names)], alpha=0.8)
        axes[0, 2].set_title("Total Token Throughput (tok/s)", fontsize=11)
        axes[0, 2].set_ylabel("tok/s")
        axes[0, 2].tick_params(axis="x", rotation=15)
        for i, v in enumerate(values):
            axes[0, 2].text(
                i,
                v + 0.02 * max(values) if max(values) > 0 else 100,
                f"{v:.0f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        axes[0, 2].grid(axis="y", alpha=0.3)

        values = [ttft_p99[i][idx] for i in range(len(chip_names))]
        axes[1, 0].bar(chip_names, values, color=colors[: len(chip_names)], alpha=0.8)
        axes[1, 0].set_title("TTFT P99 (ms)", fontsize=11)
        axes[1, 0].set_ylabel("ms")
        axes[1, 0].tick_params(axis="x", rotation=15)
        for i, v in enumerate(values):
            axes[1, 0].text(
                i,
                v + 0.02 * max(values) if max(values) > 0 else 100,
                f"{v:.0f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        axes[1, 0].grid(axis="y", alpha=0.3)

        values = [tpot_p99[i][idx] for i in range(len(chip_names))]
        axes[1, 1].bar(chip_names, values, color=colors[: len(chip_names)], alpha=0.8)
        axes[1, 1].set_title("P99 TPOT (ms)", fontsize=11)
        axes[1, 1].set_ylabel("ms")
        axes[1, 1].tick_params(axis="x", rotation=15)
        for i, v in enumerate(values):
            axes[1, 1].text(
                i,
                v + 0.02 * max(values) if max(values) > 0 else 5,
                f"{v:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        axes[1, 1].grid(axis="y", alpha=0.3)

        values = [itl_p99[i][idx] for i in range(len(chip_names))]
        axes[1, 2].bar(chip_names, values, color=colors[: len(chip_names)], alpha=0.8)
        axes[1, 2].set_title("P99 ITL (ms)", fontsize=11)
        axes[1, 2].set_ylabel("ms")
        axes[1, 2].tick_params(axis="x", rotation=15)
        for i, v in enumerate(values):
            axes[1, 2].text(
                i,
                v + 0.02 * max(values) if max(values) > 0 else 5,
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

        chart_file = os.path.join(
            output_dir, f"chip_comparison_c{conc}_{test_suite}_{chip_suffix}.png"
        )
        plt.savefig(chart_file, dpi=150, bbox_inches="tight")
        plt.close()

        chart_files.append(chart_file)
        print(f"Generated chart: {chart_file}")

    return chart_files


def generate_performance_trends(
    chip_data, concurrencies, output_dir, test_suite, chip_names, model_display=None
):
    if not HAS_MATPLOTLIB:
        return None

    chip_suffix = "_vs_".join([c.lower() for c in chip_names])
    concurrencies_int = [int(c) for c in concurrencies]

    colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    if model_display is None:
        model_display = "_vs_".join([chip_names[0]])
    fig.suptitle(
        f"{model_display} Performance Trends by Concurrency",
        fontsize=14,
        fontweight="bold",
    )

    def get_chip_values(chip_name, key):
        return [
            float(chip_data.get(chip_name, {}).get(c, {}).get(key, 0) or 0)
            for c in concurrencies
        ]

    for idx, chip_name in enumerate(chip_names):
        color = colors[idx % len(colors)]
        values = get_chip_values(chip_name, "Request throughput (req/s)")
        axes[0, 0].plot(
            concurrencies_int,
            values,
            "-o",
            color=color,
            linewidth=2,
            markersize=6,
            label=chip_name,
        )

    axes[0, 0].set_title("Request Throughput (req/s)")
    axes[0, 0].set_ylabel("req/s")
    axes[0, 0].set_xlabel("Concurrency")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    for idx, chip_name in enumerate(chip_names):
        color = colors[idx % len(colors)]
        values = get_chip_values(chip_name, "Output token throughput (tok/s)")
        axes[0, 1].plot(
            concurrencies_int,
            values,
            "-o",
            color=color,
            linewidth=2,
            markersize=6,
            label=chip_name,
        )

    axes[0, 1].set_title("Output Token Throughput (tok/s)")
    axes[0, 1].set_ylabel("tok/s")
    axes[0, 1].set_xlabel("Concurrency")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    for idx, chip_name in enumerate(chip_names):
        color = colors[idx % len(colors)]
        values = get_chip_values(chip_name, "Total token throughput (tok/s)")
        axes[0, 2].plot(
            concurrencies_int,
            values,
            "-o",
            color=color,
            linewidth=2,
            markersize=6,
            label=chip_name,
        )

    axes[0, 2].set_title("Total Token Throughput (tok/s)")
    axes[0, 2].set_ylabel("tok/s")
    axes[0, 2].set_xlabel("Concurrency")
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)

    for idx, chip_name in enumerate(chip_names):
        color = colors[idx % len(colors)]
        values = get_chip_values(chip_name, "P99 TTFT (ms)")
        axes[1, 0].plot(
            concurrencies_int,
            values,
            "-o",
            color=color,
            linewidth=2,
            markersize=6,
            label=chip_name,
        )

    axes[1, 0].set_title("TTFT P99 (ms)")
    axes[1, 0].set_ylabel("ms")
    axes[1, 0].set_xlabel("Concurrency")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    for idx, chip_name in enumerate(chip_names):
        color = colors[idx % len(colors)]
        values = get_chip_values(chip_name, "P99 TPOT (ms)")
        axes[1, 1].plot(
            concurrencies_int,
            values,
            "-o",
            color=color,
            linewidth=2,
            markersize=6,
            label=chip_name,
        )

    axes[1, 1].set_title("P99 TPOT (ms)")
    axes[1, 1].set_ylabel("ms")
    axes[1, 1].set_xlabel("Concurrency")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    for idx, chip_name in enumerate(chip_names):
        color = colors[idx % len(colors)]
        values = get_chip_values(chip_name, "P99 ITL (ms)")
        axes[1, 2].plot(
            concurrencies_int,
            values,
            "-o",
            color=color,
            linewidth=2,
            markersize=6,
            label=chip_name,
        )

    axes[1, 2].set_title("P99 ITL (ms)")
    axes[1, 2].set_ylabel("ms")
    axes[1, 2].set_xlabel("Concurrency")
    axes[1, 2].legend()
    axes[1, 2].grid(True, alpha=0.3)

    plt.tight_layout()

    chart_file = os.path.join(
        output_dir, f"performance_trends_{test_suite}_{chip_suffix}.png"
    )
    plt.savefig(chart_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Generated performance trends chart: {chart_file}")
    return chart_file


def generate_markdown_report(
    chip_data,
    concurrencies,
    output_dir,
    test_suite,
    scenarios_config,
    chip_names=None,
    model_names=None,
):
    current_date = datetime.now().strftime("%Y-%m-%d")
    if chip_names is None:
        chip_names = list(CHIP_BASE_PATHS.keys())
    if model_names is None:
        model_names = []

    chip_suffix = "_vs_".join([c.lower() for c in chip_names])

    model_prefix = get_common_model_prefix(model_names)
    model_display = (
        model_prefix
        if model_prefix
        else (", ".join(model_names) if model_names else MODEL_NAME)
    )

    base_config = scenarios_config.get("base_config", {})
    test_params = get_test_suite_config(test_suite, scenarios_config)
    dataset_name = test_params.get("dataset-name", "random")
    max_concurrency = test_params.get("max-concurrency", [])
    num_prompts = test_params.get("num-prompts", [])

    input_output_lens = test_params.get("random-input-output-len", [])
    if (
        input_output_lens
        and isinstance(input_output_lens, list)
        and len(input_output_lens) > 0
    ):
        first_pair = input_output_lens[0]
        if isinstance(first_pair, list) and len(first_pair) >= 2:
            input_len = first_pair[0]
            output_len = first_pair[1]
        else:
            input_len = first_pair if first_pair else 0
            output_len = 0
    else:
        input_len = test_params.get("random-input-len", [0])
        output_len = test_params.get("random-output-len", [0])
        input_len = input_len[0] if isinstance(input_len, list) else input_len
        output_len = output_len[0] if isinstance(output_len, list) else output_len

    def format_tokens(val):
        try:
            v = int(val)
            if v >= 1024:
                return f"{v // 1024}k"
            else:
                return f"{v / 1024:.2f}k"
        except:
            return str(val)

    def make_table_for_concurrency(
        conc, key_name, highlight_max=False, highlight_min=False
    ):
        values = []
        for chip in chip_names:
            value = chip_data.get(chip, {}).get(conc, {}).get(key_name, "")
            if value == "" or value is None:
                value = "N/A"
            values.append(value)

        if highlight_max or highlight_min:
            try:
                numeric = [
                    (i, float(v)) for i, v in enumerate(values) if v and v != "N/A"
                ]
                if numeric:
                    if highlight_max:
                        best_idx = max(numeric, key=lambda x: x[1])[0]
                    else:
                        best_idx = min(numeric, key=lambda x: x[1])[0]
                    for i in range(len(values)):
                        if i == best_idx and values[i] and values[i] != "N/A":
                            values[i] = f"**{values[i]}** ⭐"
            except:
                pass
        return " | ".join(values)

    concurrency_tables = ""

    for conc in concurrencies:
        header = " | ".join(chip_names)
        separator = " | ".join(["-----------"] * len(chip_names))

        metric_rows = []
        for display_name, key_name in COMPARISON_METRICS:
            hmax = key_name in [
                "Request throughput (req/s)",
                "Output token throughput (tok/s)",
                "Total token throughput (tok/s)",
            ]
            hmin = key_name in ["P99 TTFT (ms)", "P99 TPOT (ms)", "P99 ITL (ms)"]
            metric_rows.append(
                f"| {display_name} | {make_table_for_concurrency(conc, key_name, hmax, hmin)} |"
            )

        concurrency_tables += f"""
### {conc} 并发

| 指标 | {header} |
|------|{separator}|
{chr(10).join(metric_rows)}

---
"""

    chart_images = "\n".join(
        [
            f'<img src="./chip_comparison_c{conc}_{test_suite}_{chip_suffix}.png" width="1000" />'
            for conc in concurrencies
        ]
    )

    performance_trends_img = f'<img src="./performance_trends_{test_suite}_{chip_suffix}.png" width="1000" />'

    concurrency_str = (
        ", ".join(str(c) for c in max_concurrency)
        if max_concurrency
        else ", ".join(concurrencies)
    )
    input_ctx = format_tokens(input_len) if input_len else "N/A"
    output_ctx = format_tokens(output_len) if output_len else "N/A"
    total_requests = num_prompts[0] if num_prompts else "N/A"
    input_len_val = input_len if input_len else "N/A"
    output_len_val = output_len if output_len else "N/A"

    chip_models_str = ", ".join(
        [f"{chip} ({model})" for chip, model in zip(chip_names, model_names)]
    )

    md_content = f"""# {model_display}模型在不同芯片下的基准测试报告

<div align="center">
**测试日期：** {current_date}

</div>

---

## 测试场景
在固定请求数，输入上下文和输出上下文长度下，使用SGLang基准测试工具对并发数逐级增加场景的性能基准验证。并对比同一模型在不同芯片环境上的性能指标。

**主要采集指标**：

| 指标                  | 单位         | 含义                                 |
|---------------------|------------|------------------------------------|
| TTFT                | ms         | Time To First Token，首 token 延迟     |
| TPOT                | ms/token   | Time Per Output Token，每 token 生成时间 |
| Throughput          | tokens/s   | 系统总吞吐                              |
| QPS                 | requests/s | 请求吞吐                               |

## 📊 测试概览

| 项目            | 配置                                     | 备注  |
|---------------|----------------------------------------|-----|
| **数据集**       | {dataset_name}                                 |     |
| **并发数**       | {concurrency_str}    |     |
| **总请求数**      | {total_requests}                                    |     |
| **请求输入上下文长度** | {input_len_val}（{input_ctx}）                             |     |
| **请求输出上下文长度** | {output_len_val}（{output_ctx}）                             |     |
| **被测芯片**      | {", ".join(chip_names)} |     |
| **被测模型**      | {chip_models_str} |     |

---

## 📊 芯片性能对比柱状图

{chart_images}

---

## 📈 性能趋势对比图 (所有芯片)

{performance_trends_img}

---

## 📈 各并发级别性能对比详情

{concurrency_tables}

---

<div align="center">
*报告生成时间: {current_date}*
</div>
"""

    md_file = os.path.join(
        output_dir, f"{model_display}_chip_comparison_{test_suite}_{chip_suffix}.md"
    )
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Generated: {md_file}")
    return md_file


def get_common_model_prefix(model_names):
    if not model_names:
        return ""
    if len(model_names) == 1:
        return model_names[0]

    prefix = model_names[0]
    for name in model_names[1:]:
        while not name.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix


def check_reports_exist(chip_models):
    missing = []
    for chip_name, model_name in chip_models:
        report_path = f"reports/benchmark/{chip_name}/{model_name}"
        if not os.path.exists(report_path):
            missing.append((chip_name, model_name, report_path))
    return missing


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate SGLang chip comparison report"
    )
    parser.add_argument(
        "--chip",
        type=str,
        required=True,
        help="Chip names to compare, comma-separated (e.g., inspur_MetaX_C550,nvidia_h100). At least 2 chips required.",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model names corresponding to each chip, comma-separated (e.g., MiniMax-M2.5-W8A8,MiniMax-M2.5). Must have same count as --chip.",
    )
    parser.add_argument(
        "--test-suite", type=str, default=None, help="Test suite name (e.g., test_01)"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run IDs, can be '01' for all chips or '01,02' for each chip",
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=str,
        default=None,
        help="Specific concurrency levels to compare, comma-separated (e.g., 1,2,4,8,10)",
    )
    args = parser.parse_args()

    chip_list = [s.strip() for s in args.chip.split(",")]
    model_list = [s.strip() for s in args.model.split(",")]

    if len(chip_list) < 2:
        print(
            f"Error: At least 2 chips are required for comparison. Got: {len(chip_list)}"
        )
        return

    if len(chip_list) != len(model_list):
        print(
            f"Error: Number of chips ({len(chip_list)}) must match number of models ({len(model_list)})"
        )
        return

    chip_key_map = {
        "inspur_metax_c550": "inspur_MetaX_C550",
        "nvidia_h100": "nvidia_h100",
    }
    chip_key_map_reverse = {
        "inspur_metax_c550": "inspur_MetaX_C550",
        "nvidia_h100": "nvidia_h100",
    }

    chip_names = [chip_key_map_reverse.get(s.lower(), s.lower()) for s in chip_list]
    model_names = model_list

    chip_models = list(zip(chip_names, model_names))

    missing_reports = check_reports_exist(chip_models)
    if missing_reports:
        print("Error: The following chip/model combinations do not have report files:")
        for chip, model, path in missing_reports:
            print(f"  - {chip} + {model}: {path}")
        return

    chip_base_paths = {}
    for i, (chip_name, model_name) in enumerate(chip_models):
        base_path = f"reports/benchmark/{chip_name}/{model_name}"
        chip_base_paths[chip_name] = {"base_path": base_path, "model": model_name}

    scenarios_config = load_models_scenarios()

    test_suite_input = args.test_suite.strip() if args.test_suite else TEST_SUITES[0]
    test_suite_to_use = (
        test_suite_input.lower() if test_suite_input else test_suite_input
    )

    run_ids_input = args.run_id.strip() if args.run_id else None
    if run_ids_input:
        run_ids_list = [s.strip() for s in run_ids_input.split(",")]
        num_chips = len(chip_names)
        if len(run_ids_list) == 1:
            run_id_to_use = [run_ids_list[0]] * num_chips
        elif len(run_ids_list) == num_chips:
            run_id_to_use = run_ids_list
        else:
            print(
                f"Error: Number of run-ids ({len(run_ids_list)}) must match number of chips ({num_chips}) or be 1"
            )
            return
    else:
        num_chips = len(chip_names)
        run_id_to_use = [RUN_IDS[0]] * num_chips

    def get_chip_configs_for_chips(chip_names, test_suite, chip_run_ids, chip_paths):
        configs = []
        for i, chip_name in enumerate(chip_names):
            chip_info = chip_paths.get(chip_name, {})
            base_path = (
                chip_info.get("base_path", "")
                if isinstance(chip_info, dict)
                else chip_info
            )
            run_id = chip_run_ids[i] if i < len(chip_run_ids) else chip_run_ids[0]
            if base_path:
                configs.append(
                    {
                        "name": chip_name,
                        "base_path": f"{base_path}/{test_suite}/{run_id}",
                    }
                )
        return configs

    for test_suite in [test_suite_to_use]:
        print(f"\n{'#' * 60}")
        print(f"Processing test suite: {test_suite}")
        print(f"Chips: {', '.join(chip_names)}")
        print(f"Run IDs: {', '.join(run_id_to_use)}")
        print(f"{'#' * 60}\n")

        chip_configs = get_chip_configs_for_chips(
            chip_names, test_suite, run_id_to_use, chip_base_paths
        )
        run_id_display = "_".join(run_id_to_use)

        model_names_for_path = [chip_base_paths[c]["model"] for c in chip_names]
        model_prefix = get_common_model_prefix(model_names_for_path)
        if not model_prefix:
            model_prefix = "models"

        output_base = (
            f"analysis/chip_comparison/{model_prefix}/{test_suite}/{run_id_display}"
        )
        Path(output_base).mkdir(parents=True, exist_ok=True)

        all_concurrencies = set()
        for chip in chip_configs:
            concs = get_all_concurrencies(chip)
            all_concurrencies.update(concs)

        if not all_concurrencies:
            print(f"No concurrency configurations found for {test_suite}!")
            continue

        concurrencies = sorted(all_concurrencies, key=lambda x: int(x))

        if args.concurrency:
            conc_list = [s.strip() for s in args.concurrency.split(",")]
            filtered_concs = [c for c in concurrencies if c in conc_list]
            if filtered_concs:
                concurrencies = filtered_concs
                print(f"Using specified concurrency levels: {', '.join(concurrencies)}")
            else:
                print(
                    f"Warning: None of the specified concurrency levels {conc_list} found, using all"
                )

        print(
            f"Found {len(concurrencies)} concurrency levels: {', '.join(concurrencies)}"
        )

        chip_data = defaultdict(lambda: defaultdict(dict))

        for chip in chip_configs:
            chip_name = chip["name"]
            print(f"\nProcessing chip: {chip_name}")

            for conc in concurrencies:
                metrics = get_chip_metrics(chip, conc)
                if metrics:
                    chip_data[chip_name][conc] = metrics
                    print(f"  - {conc}并发: OK")
                else:
                    print(f"  - {conc}并发: No data")

        print("\nGenerating comparison reports...")

        model_display = (
            model_prefix if len(model_names_for_path) > 1 else model_names_for_path[0]
        )

        generate_comparison_csv(
            chip_data, concurrencies, output_base, test_suite_to_use, chip_names
        )

        if HAS_MATPLOTLIB:
            generate_comparison_charts(
                chip_data,
                concurrencies,
                output_base,
                test_suite_to_use,
                chip_names,
                model_display,
            )
            generate_performance_trends(
                chip_data,
                concurrencies,
                output_base,
                test_suite_to_use,
                chip_names,
                model_display,
            )

        generate_markdown_report(
            chip_data,
            concurrencies,
            output_base,
            test_suite_to_use,
            scenarios_config,
            chip_names,
            model_names_for_path,
        )

        print(f"\n{'=' * 50}")
        print(f"Chip comparison for {test_suite} generated successfully!")
        print(f"Output directory: {output_base}")
        print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
