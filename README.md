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
--test-suite TEST_SUITE  Test suite to run, use "," split multiple test suite; if not specified, use TEST_SUITES list defined in scripts to run <br>
--run-id RUN_ID       Run ID to identify this test run, if not specified, use RUN_ID defined in scripts <br>

### 1.1 测试 hygon_bw1000 芯片上的 minimax-m2.5 模型
python run_benchmark.py --chip hygon_bw1000 --model minimax-m2.5

### 1.2 测试 hygon_bw1000 芯片上的 Qwen3.5 模型
python run_benchmark.py --chip hygon_bw1000 --model Qwen3.5

### 1.3 不指定模型则测试该芯片下所有配置的模型
python run_benchmark.py --chip hygon_bw1000

### 1.4 组合使用: 执行hygon_bw1000平台下Qwen3.5模型的test_01测试场景的第2次测试
python run_benchmark.py --chip hygon_bw1000 --model Qwen3.5 --test-suite test_01 --run-id 02

### 1.5 指定多个测试套件
python run_benchmark.py --chip kunlun_p800 --model qwen3.5-plus --test-suite test_05,test_06 --run-id 02


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
- xpu-smi (Intel GPU)

监控数据会保存到 monitor/logs 目录，并生成GPU使用趋势图表。


## 4. 如何生成单个平台下的单个模型的单次测试的性能变化
**命令**<br>
python parse_single_chip_model.py

#### 帮助信息：
usage:<br> 
parse_single_chip_model.py [-h] [--chip CHIP] [--model MODEL]
                            [--test-suite TEST_SUITE] [--run-id RUN_ID]

**options**:<br>
--chip CHIP           Chip name to test (e.g., inspur_MetaX_C500, hygon_bw1000)<br>
--model MODEL         Model name to test (e.g., MiniMax-M2.5-W8A8)<br>
--test-suite TEST_SUITE  Test suite name (e.g., test_01, test_05)<br>
--run-id RUN_ID       Run ID (e.g., 01)<br>

#### 示例：
##### 4.1 生成 inspur_MetaX_C500 芯片上 MiniMax-M2.5-W8A8 模型 test_01 测试的第01次报告
python parse_single_chip_model.py --chip inspur_MetaX_C500 --model MiniMax-M2.5-W8A8 --test-suite test_01 --run-id 01

##### 4.2 生成多I/O测试报告（test_05）
python parse_single_chip_model.py --chip inspur_MetaX_C500 --model MiniMax-M2.5-W8A8 --test-suite test_05 --run-id 01

##### 4.3 使用默认参数
python parse_single_chip_model.py

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