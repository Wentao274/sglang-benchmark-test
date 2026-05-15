# sglang-benchmark-test测试说明
SGLang benchmark serve test for llm

## 1. run_benchmark基准测试使用
#### 帮助信息：
**usage**: <br> 
run_benchmark.py [-h] --chip CHIP [--model MODEL]
                        [--test-suite TEST_SUITE] [--run-id RUN_ID]

**options**:<br>
--chip CHIP           Chip name to test <br>
--model MODEL         Model name to test (e.g., minimax-m2.5, Qwen3.5) <br>
--test-suite TEST_SUITE  Test suite to run, use "," split multiple test suite; if not specified, use TEST_SUITES list defined in scripts to run (default: test_01) <br>
--run-id RUN_ID       Run ID to identify this test run, if not specified, use RUN_ID defined in scripts <br>

### 1.1 测试 inspur_MetaX_C550 芯片上的 MiniMax-M2.5-W8A8 模型
python run_benchmark.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8

### 1.2 不指定模型则测试该芯片下所有配置的模型
python run_benchmark.py --chip inspur_MetaX_C550

### 1.3 组合使用: 执行inspur_MetaX_C550平台下MiniMax-M2.5-W8A8模型的test_01测试场景的第2次测试
python run_benchmark.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_01 --run-id 02

### 1.4 指定多个测试套件
python run_benchmark.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_05,test_06 --run-id 02


## 2. 配置文件说明

### 2.1 config/models_scenarios.yaml
SGLang基准测试的场景配置，包含：
- base_config: 基础配置（URL、端口、测试参数等）
- models: 各芯片平台下的模型配置

### 2.2 config/chip_conf.yaml
芯片配置信息，用于生成报告时的芯片详情

### 2.3 config/model_deployment.yaml
模型部署配置，用于生成报告时的SGLang启动配置信息


## 3. GPU监控
gpu_monitor.py 提供GPU监控功能，支持：
- nvidia-smi (NVIDIA GPU)
- hy-smi (海光GPU)
- rocm-smi (AMD GPU)
- xpu-smi (昆仑芯 GPU)
- mx-smi (沐曦 GPU)

监控数据会保存到 monitor/logs 目录，并生成GPU使用趋势图表。


## 4. 数据目录结构

### 4.1 Benchmark 测试结果目录结构

测试结果保存在 `reports` 目录下。

#### 目录结构：
```
reports/benchmark/<chip_name>/<model_name>/<test_suite>/<run_id>/<concurrency>-<num_prompts>-i<input_len>-o<output_len>/
```

#### 示例：
```
reports/benchmark/inspur_MetaX_C550/MiniMax-M2.5-W8A8/test_01/01/1-320-i10240-o256/
reports/benchmark/nvidia_h100/MiniMax-M2.5/test_03/02/4-100-i194560-o1024/
```

#### 说明：
- `benchmark`: 固定目录名
- `{chip_name}`: 芯片平台（如 `inspur_MetaX_C550`, `nvidia_h100`）
- `{model_name}`: 模型名称（如 `MiniMax-M2.5-W8A8`）
- `{test_suite}`: 测试套件（如 `test_01`, `test_03`, `test_05` 等）
- `{run_id}`: 测试运行 ID（如 `01`, `02`）
- `{concurrency}-{num_prompts}-i{input_len}-o{output_len}`: 并发数-提示数-输入长度-输出长度

#### 输出文件：
- `bench-<test_suite>-<conc>-<num_prompts>-i<input>-o<output>.log`: 测试日志


### 4.2 GPU 监控日志目录结构

在运行 benchmark 测试时，会自动启动 GPU 监控，记录 GPU 使用情况。监控日志保存在 `monitor` 目录下。

#### 目录结构：
```
monitor/logs/<chip_name>/<model_name>/<test_suite>/<run_id>/<concurrency>-<num_prompts>-i<input_len>-o<output_len>/
```

#### 示例：
```
monitor/logs/inspur_MetaX_C550/MiniMax-M2.5-W8A8/test_01/01/1-320-i10240-o256/gpu_monitor_20260430123341.log
monitor/logs/nvidia_h100/MiniMax-M2.5/test_03/01/4-100-i194560-o1024/gpu_monitor_20260430143239.log
```

#### 说明：
- `logs`: 固定目录名
- `{chip_name}`: 芯片平台（如 `inspur_MetaX_C550`, `nvidia_h100`）
- `{model_name}`: 模型名称（如 `MiniMax-M2.5-W8A8`）
- `{test_suite}`: 测试套件（如 `test_01`, `test_03`, `test_05` 等）
- `{run_id}`: 测试运行 ID（如 `01`, `02`）
- `{concurrency}-{num_prompts}-i{input_len}-o{output_len}`: 并发数-提示数-输入长度-输出长度
- `gpu_monitor_{timestamp}.log`: GPU 监控日志文件

#### 日志格式：
日志文件为 CSV 格式，包含以下字段：
- Time: 时间戳
- GPU: GPU 索引
- Name: GPU 名称
- Used_MB: 已使用显存 (MB)
- Total_MB: 总显存 (MB)
- Utilization_%: GPU 利用率 (%)
- Memory_%: 显存利用率 (%)
- Temperature_C: 温度 (°C)


## 4. 如何生成单个平台下的单个模型的单次测试的性能变化
**命令**<br>
python parse_single_chip_model.py

#### 帮助信息：
usage:<br> 
parse_single_chip_model.py [-h] [--chip CHIP] [--model MODEL]
                            [--test-suite TEST_SUITE] [--run-id RUN_ID] [--concurrency CONCURRENCY]

**options**:<br>
--chip CHIP           Chip name to test (e.g., inspur_MetaX_C550)<br>
--model MODEL         Model name to test (e.g., MiniMax-M2.5-W8A8)<br>
--test-suite TEST_SUITE  Test suite name (e.g., test_01, test_05) (default: test_01)<br>
--run-id RUN_ID       Run ID (e.g., 01)<br>
--concurrency CONCURRENCY  Specific concurrency levels to include, comma-separated (e.g., 1,2,4,8,10)<br>

#### 示例：
##### 4.1 生成 inspur_MetaX_C550 芯片上 MiniMax-M2.5-W8A8 模型 test_01 测试的第01次报告
python parse_single_chip_model.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_01 --run-id 01

##### 4.2 生成多I/O测试报告（test_05）
python parse_single_chip_model.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_05 --run-id 01

##### 4.3 使用默认参数
python parse_single_chip_model.py

##### 4.4 指定特定并发数生成报告
python parse_single_chip_model.py --chip inspur_MetaX_C550 --test-suite test_01 --concurrency 1,4,8

##### 4.5 使用简写-c指定并发数
python parse_single_chip_model.py -c 1,4,8,16 --chip inspur_MetaX_C550 --test-suite test_05

如果不指定任何参数，则默认使用CHIP_BASE_PATHS的第一个Key和代码中定义的MODEL_NAME, TEST_SUITES和RUN_ID

#### 输出说明：
- 输出目录：`analysis/single_chip/<chip_name>/<model_name>/<test_suite>/<run_id>/`
- 生成文件：
  - `concurrency_comparison.csv` - CSV格式对比数据
  - `concurrency_comparison.png` - 并发级别性能柱状图
  - `performance_trends.png` - 性能趋势折线图
  - `performance_trends.csv` - 性能趋势CSV数据
  - `<model_name>_<chip_name>_concurrency.md` - Markdown格式报告（单I/O测试）
  - `<model_name>_<chip_name>_multi_io_report.md` - Markdown格式报告（多I/O测试，如test_05）
- 多I/O测试（test_05）额外生成：
  - `i<input_len>_o<output_len>/` - 每个I/O对的性能图表
  - `compare_by_io_conc<concurrency>/` - 固定并发数下的I/O对比图表


## 5. 如何生成不同芯片平台对比的性能报告
**命令**<br>
python chip_comparison.py

#### 帮助信息：
usage:<br> 
chip_comparison.py [-h] [--chip CHIP] [--model MODEL]
                          [--test-suite TEST_SUITE] [--run-id RUN_ID] [--concurrency CONCURRENCY]

**options**:<br>
--chip CHIP           Chip names to compare, comma-separated (e.g., inspur_MetaX_C550,nvidia_h100)<br>
--model MODEL         Model name to test (e.g., MiniMax-M2.5-W8A8)<br>
--test-suite TEST_SUITE  Test suite name (e.g., test_01) (default: test_01)<br>
--run-id RUN_ID       Run IDs, can be '01' for all chips or '01,02' for each chip<br>
--concurrency CONCURRENCY  Specific concurrency levels to compare, comma-separated (e.g., 1,2,4,8,10)<br>

#### 示例：
##### 5.1 对比inspur_MetaX_C550和nvidia_h100芯片
python chip_comparison.py --chip inspur_MetaX_C550,nvidia_h100 --test-suite test_01

##### 5.2 使用默认参数（对比所有配置的芯片）
python chip_comparison.py

##### 5.3 指定不同的run-id
python chip_comparison.py --chip inspur_MetaX_C550,nvidia_h100 --test-suite test_01 --run-id '01,02'

##### 5.4 指定特定并发数进行对比
python chip_comparison.py --chip inspur_MetaX_C550,nvidia_h100 --test-suite test_01 --concurrency 1,2,4,8

##### 5.5 使用简写-c指定并发数
python chip_comparison.py -c 1,4,8,16 --chip inspur_MetaX_C550,nvidia_h100

**注意**：
- run-id 参数如果只有一个值，所有芯片使用相同 run-id
- run-id 参数如果有多个值（逗号分隔），按 --chip 参数顺序一一对应
- 所有参数值大小写不敏感

#### 输出说明：
- 输出目录：`analysis/chip_comparison/<model_name>/<test_suite>/<run_id1_run_id2>/`
- 生成文件：
  - `comparison_<test_suite>_<chip_suffix>.csv` - CSV格式对比数据
  - `chip_comparison_c<conc>_<test_suite>_<chip_suffix>.png` - 各并发级别性能柱状图
  - `performance_trends_<test_suite>_<chip_suffix>.png` - 性能趋势折线图
  - `<model_name>_chip_comparison_<test_suite>_<chip_suffix>.md` - Markdown格式报告
- 比对指标：
  - Request throughput (req/s)
  - Output token throughput (tok/s)
  - Total token throughput (tok/s)
  - P99 TTFT (ms)
  - P99 TPOT (ms)
  - P99 ITL (ms)


## 6. 如何生成同一芯片下不同模型之间的性能对比报告

**命令**<br>
python model_comparison.py

#### 帮助信息：
usage:<br> 
model_comparison.py [-h] --chip CHIP --model MODEL
                          [--test-suite TEST_SUITE] [--run-id RUN_ID]
                          [-c CONCURRENCY]

**options**:<br>
--chip CHIP           Chip platform (e.g., inspur_MetaX_C550, nvidia_h100)<br>
--model MODEL         Model names to compare, separated by comma (e.g., MiniMax-M2.5-W8A8,GLM-5-W8A8)<br>
--test-suite TEST_SUITE  Test suite name (e.g., test_01) (default: test_01)<br>
--run-id RUN_ID       Run IDs for each model, separated by comma (e.g., 01 or 01,02)<br>
-c CONCURRENCY        Specific concurrency levels to compare, comma-separated (e.g., 1,2,4,8,10)<br>

#### 示例：
##### 6.1 对比同一run-id（所有模型使用相同的run-id）
python model_comparison.py --chip inspur_MetaX_C550 --model "MiniMax-M2.5-W8A8,GLM-5-W8A8" --test-suite test_01 --run-id 01

##### 6.2 对比不同run-id（第一个模型用01，第二个用02）
python model_comparison.py --chip inspur_MetaX_C550 --model "MiniMax-M2.5-W8A8,GLM-5-W8A8" --test-suite test_01 --run-id '01,02'

##### 6.3 使用默认参数（test_01, run-id 01）
python model_comparison.py --chip inspur_MetaX_C550 --model "MiniMax-M2.5-W8A8,GLM-5-W8A8"

##### 6.4 指定特定并发级别
python model_comparison.py --chip inspur_MetaX_C550 --model "MiniMax-M2.5-W8A8,GLM-5-W8A8" -c 1,2,4,8

**注意**：所有参数值大小写不敏感

#### 输出说明：
**注：此脚本输出的比对报告是每个并发级别单独分开的**
- 输出目录：`analysis/<chip>_model_comparison/<test_suite>/<concurrency>-<num_prompts>-i<input>-o<output>/`
- 生成文件：
  - `concurrency<XXX>_comparison.csv` - CSV格式对比数据
  - `concurrency<XXX>_comparison.png` - 可视化图表
  - `concurrency<XXX>_comparison.md` - Markdown格式报告
- 汇总报告：`analysis/<chip>_model_comparison/<test_suite>/summary.md`
- 比对指标：
  - 请求吞吐量 (req/s)
  - 输出token吞吐量 (tok/s)
  - 总token吞吐量 (tok/s)
  - TTFT (ms)
  - TPOT (ms)
  - ITL (ms)
  - E2E延迟 (ms)


## 7. 如何生成同一芯片下不同模型的全并发级别对比报告

**命令**<br>
python model_comparison_all_concurrency.py

#### 帮助信息：
usage:<br> 
model_comparison_all_concurrency.py [-h] --chip CHIP --model MODEL
                              [--test-suite TEST_SUITE] [--run-id RUN_ID]

**options**:<br>
--chip CHIP           Chip platform (e.g., inspur_MetaX_C550, nvidia_h100)<br>
--model MODEL         Model names to compare, separated by comma (e.g., MiniMax-M2.5-W8A8,GLM-5-W8A8)<br>
--test-suite TEST_SUITE  Test suite name (e.g., test_01) (default: test_01)<br>
--run-id RUN_ID       Run IDs for each model, separated by comma (e.g., 01 or 01,02)<br>

#### 示例：
##### 7.1 对比同一run-id（所有模型使用相同的run-id）
python model_comparison_all_concurrency.py --chip inspur_MetaX_C550 --model "MiniMax-M2.5-W8A8,GLM-5-W8A8" --test-suite test_01 --run-id 01

##### 7.2 对比不同run-id（第一个模型用01，第二个用02）
python model_comparison_all_concurrency.py --chip inspur_MetaX_C550 --model "MiniMax-M2.5-W8A8,GLM-5-W8A8" --test-suite test_01 --run-id '01,02'

##### 7.3 使用默认参数（test_01, run-id 01）
python model_comparison_all_concurrency.py --chip inspur_MetaX_C550 --model "MiniMax-M2.5-W8A8,GLM-5-W8A8"

**注意**：此脚本会自动生成所有并发级别的对比数据，并合并到一个Markdown报告中

#### 输出说明：
- 输出目录：`analysis/<chip>_comparison_all_concurrency/<test_suite>/`
- 生成文件：
  - `all_concurrency_comparison.csv` - 所有并发级别的CSV格式对比数据
  - `all_concurrency_comparison.png` - 所有并发级别的可视化图表
  - `all_concurrency_comparison.md` - Markdown格式汇总报告（包含所有并发级别）
- 报告结构：
  - 芯片和模型配置信息
  - SGLang 启动配置信息
  - 模型列表
  - 测试概览
  - 模型性能对比图表
  - 分析小结
  - 各并发级别详细对比（服务基准结果、TTFT、TPOT、ITL、E2E延迟）


## 8. 如何生成同一芯片、同一模型下不同测试RUN-ID的性能对比报告

**命令**<br>
python compare_runids.py

#### 帮助信息：
usage:<br> 
compare_runids.py [-h] --chip CHIP --model MODEL
                  [--test-suite TEST_SUITE] --run-id RUN_ID
                  [--concurrency CONCURRENCY]

**options**:<br>
--chip CHIP           Chip platform (e.g., inspur_MetaX_C550, nvidia_h100)<br>
--model MODEL         Model name (e.g., MiniMax-M2.5-W8A8)<br>
--test-suite TEST_SUITE  Test suite name (e.g., test_01, test_05) (default: test_01)<br>
--run-id RUN_ID       Run IDs to compare, separated by comma (e.g., 01,02 or 01,02,03)<br>
--concurrency CONCURRENCY  Specific concurrency levels, comma-separated (e.g., 1,2,4,8,10)<br>

#### 示例：
##### 8.1 对比两个RUN-ID
python compare_runids.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_01 --run-id 01,02

##### 8.2 对比三个RUN-ID
python compare_runids.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_01 --run-id 01,02,03

##### 8.3 指定特定并发级别
python compare_runids.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_01 --run-id 01,02 --concurrency 1,4,8,16

##### 8.4 使用简写-c指定并发数
python compare_runids.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_01 --run-id 01,02 -c 1,2,4

**注意**：
- 至少需要2个RUN-ID才能进行对比
- 所有参数值大小写不敏感
- 支持多I/O测试套件（test_05）

#### 输出说明：
- 输出目录：`analysis/single_chip/<chip_name>/<model_name>/compare_run/<test_suite>/run_<runid1>_<runid2>_<...>/`
- 生成文件：
  - `runid_comparison.csv` - CSV格式对比数据
  - `runid_comparison.png` - 各指标柱状图对比
  - `<model_name>_<chip_name>_<test_suite>_runid_compare_<runids>.md` - Markdown格式报告
- 报告结构：
  - 测试场景说明
  - 芯片和模型配置信息
  - SGLang 启动配置信息
  - 测试概览
  - RUN-ID对比柱状图
  - 各并发级别详细对比（服务基准结果、TTFT、TPOT、ITL、E2E延迟）
  - 分析总结（吞吐量对比、延迟对比）


## 9. 一键运行基准测试并生成报告

**命令**<br>
python run_benchmark_gen_report.py

#### 帮助信息：
usage:<br> 
run_benchmark_gen_report.py [-h] --chip CHIP [--model MODEL]
                              [--test-suite TEST_SUITE] [--run-id RUN_ID]
                              [--skip-benchmark] [--only-report]
                              [-c CONCURRENCY]

**options**:<br>
--chip CHIP           Chip platform (e.g., inspur_MetaX_C550, nvidia_h100)<br>
--model MODEL         Model name to test. If not specified, uses first model in config.<br>
--test-suite TEST_SUITE  Test suite name (e.g., test_01, test_05) (default: test_01)<br>
--run-id RUN_ID       Run ID to identify this test run (default: 01)<br>
--skip-benchmark      Skip running benchmark, only generate reports<br>
--only-report         Only generate reports without running benchmark<br>
-c CONCURRENCY        Specific concurrency levels, comma-separated (e.g., 1,2,4,8,10)<br>

#### 示例：
##### 9.1 运行基准测试并生成报告
python run_benchmark_gen_report.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_01

##### 9.2 运行特定测试套件
python run_benchmark_gen_report.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --test-suite test_05 --run-id 02

##### 9.3 只生成报告（基于已有测试数据）
python run_benchmark_gen_report.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --only-report

##### 9.4 跳过基准测试，只生成报告
python run_benchmark_gen_report.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 --skip-benchmark

##### 9.5 指定特定并发级别生成报告
python run_benchmark_gen_report.py --chip inspur_MetaX_C550 --model MiniMax-M2.5-W8A8 -c 1,4,8,16

**功能说明**：
- 自动运行基准测试（如果未跳过）
- 测试完成后自动生成报告
- 自动检测RUN-ID数量：
  - 单个RUN-ID → 生成单次测试报告
  - 多个RUN-ID → 自动生成RUN-ID对比报告
- 支持GPU监控（如果可用）
