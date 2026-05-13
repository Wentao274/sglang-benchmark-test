# GLM-5-W8A8模型在inspur_MetaX_C550上的Benchmark基准测试报告

<div align="center">
**测试日期：** 2026-05-13

</div>

---

## 测试场景
使用sglang bench serve基准测试工具对不同并发数，请求上下文长度下的性能变化趋势。

**主要采集指标**：

| 指标                  | 单位         | 含义                                 |
|---------------------|------------|------------------------------------|
| E2E Latency         | ms         | End-to-End Latency，端到端延迟         |
| TTFT                | ms         | Time To First Token，首 token 延迟     |
| TPOT                | ms/token   | Time Per Output Token，每 token 生成时间 |
| ITL                 | ms         | Inter-Token Latency，token间延迟       |
| Throughput          | tokens/s   | 系统总吞吐                              |
| QPS                 | requests/s | 请求吞吐                               |


## 🤖 芯片和模型配置信息

| 参数名称                    | inspur_MetaX_C550 |
|------------------------|-------------|
| **model_name** | GLM-5-W8A8 |
| **quantization_config** | int8 |
| **model_size** | 712G |
| **max_position_embeddings** | 202752 |
| **temperature** | N/A |
| **top_k** | N/A |
| **top_p** | N/A |
| **transformers_version** | 5.1.0 |
| **sglang_version** | 0.5.9+maca3.5.3.204 |
| **python_version** | 3.10.10 |


## 🤖 SGLang启动配置信息

| 参数名称                   | inspur_MetaX_C550 |
|------------------------|-------------|
| **Model Name** | GLM-5-W8A8 |
| **Attention Backend** | flashinfer |
| **Quantization** | w8a8_int8 |
| **Tp Size** | 16 |
| **Dp Size** | 4 |
| **Pp Size** | 1 |
| **Nnodes** | 2 |
| **Context Length** | 202752 |
| **Cuda Graph Max Bs** | 64 |
| **Max Running Requests** | 64 |
| **Max Queued Requests** | None |
| **Chunked Prefill Size** | 8192 |
| **Disable Radix Cache** | True |
| **Tool Call Parser** | glm47 |
| **Reasoning Parser** | glm45 |
| **Mem Fraction Static** | 0.8 |

- **inspur_MetaX_C550**: 浪潮MetaX_C550 SGLang启动配置


## 📊 测试概览

| 项目            | 配置                                     | 备注  |
|---------------|----------------------------------------|-----|
| **数据集**       | random                                 |     |
| **并发数**       | 32, 64    |     |
| **总请求数**      | 1000                                    |     |
| **请求输入上下文长度** | 90000（87k）                             |     |
| **请求输出上下文长度** | 2000（1k）                             |     |
| **模型**        | GLM-5-W8A8                           |     |
| **被测芯片**      | inspur_MetaX_C550 |     |
| **SGLang版本**   | 0.5.9                           |     |

---

## 📋 测试结果汇总

| 并发数 | 请求吞吐量 (req/s) | 输出Token吞吐量 (tok/s) | 总Token吞吐量 (tok/s) | TTFT P99 (ms) | TPOT P99 (ms) | E2E延迟均值 (ms) |
| ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- |
| 32 | 6.27 | 6.27 | 563888.21 | 8234.15 | 0.00 | 5088.28 |
| 64 | 6.23 | 6.23 | 560604.28 | 18597.83 | 0.00 | 10243.30 |


## 📊 各并发级别性能柱状图

<img src="./concurrency_comparison.png" width="1000" />


## 📈 性能趋势分析

<img src="./performance_trends.png" width="1000" />

---

### 🎯 服务基准结果详情

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 成功请求数 | 1000 | 1000 |
| 测试持续时间 (s) | 159.61 | 160.54 |
| 总输入 tokens | 90000000 | 90000000 |
| 总生成 tokens | 1000 | 1000 |
| **请求吞吐量 (req/s)** | 6.27 | 6.23 |
| **输出 token 吞吐量 (tok/s)** | 6.27 | 6.23 |
| 峰值输出 token 吞吐量 (tok/s) | 22.00 | 62.00 |
| 峰值并发请求数 | 46 | 73 |
| **总 token 吞吐量 (tok/s)** | 563888.21 | 560604.28 |


### ⏱️ 端到端延迟 (E2E Latency)

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 平均 E2E 延迟 (ms) | 5088.28 | 10243.30 |
| 中位 E2E 延迟 (ms) | 5093.21 | 10246.51 |
| P90 E2E 延迟 (ms) | 5501.08 | 10713.14 |
| P99 E2E 延迟 (ms) | 8234.16 | 18597.84 |


### ⏱️ 首Token延迟 (TTFT)

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 平均 TTFT (ms) | 5088.27 | 10243.29 |
| 中位 TTFT (ms) | 5093.20 | 10246.50 |
| P99 TTFT (ms) | 8234.15 | 18597.83 |


### ⚡ 每Token生成时间 (TPOT)

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 平均 TPOT (ms) | 0.00 | 0.00 |
| 中位 TPOT (ms) | 0.00 | 0.00 |
| P99 TPOT (ms) | 0.00 | 0.00 |


### 🔄 Token间延迟 (ITL)

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 平均 ITL (ms) | 0.00 | 0.00 |
| 中位 ITL (ms) | 0.00 | 0.00 |
| P95 ITL (ms) | 0.00 | 0.00 |
| P99 ITL (ms) | 0.00 | 0.00 |

---

## 📝 分析总结

### 1. 吞吐量性能分析

**请求吞吐量 (QPS)**: 随着并发级别增加，QPS持续上升。
中并发(32)平均 QPS: 6.27 req/s；
高并发(64)平均 QPS: 6.23 req/s；
最高 QPS 出现在 32 并发，达到 6.27 req/s。

**Token总吞吐量**: 最高达到 563888 tok/s (32 并发)。

### 2. 端到端延迟 (E2E Latency) 分析

E2E延迟随并发增加显著上升。
高并发平均 P99 E2E: 18598ms；
最高 P99 E2E 出现在 64 并发，达到 18598ms。

### 3. 首Token延迟 (TTFT) 分析

TTFT随并发增加显著上升。
高并发平均 P99 TTFT: 18598ms；
最高 P99 TTFT 出现在 64 并发，达到 18598ms。

### 4. Token生成时间 (TPOT) 分析

TPOT随并发增加也呈上升趋势。
高并发平均 P99 TPOT: 0.00ms；
最高 P99 TPOT 出现在 None 并发，达到 0.00ms。

### 5. Token间延迟 (ITL) 分析

ITL随并发增加呈上升趋势。
高并发平均 P99 ITL: 0.00ms；
最高 P99 ITL 出现在 None 并发，达到 0.00ms。

### 6. 综合评估

**吞吐量增长**: 从最低并发到最高并发，QPS增长了 -0.6%。

---

<div align="center">
*报告生成时间: 2026-05-13*
</div>
