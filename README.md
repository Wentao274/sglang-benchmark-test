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