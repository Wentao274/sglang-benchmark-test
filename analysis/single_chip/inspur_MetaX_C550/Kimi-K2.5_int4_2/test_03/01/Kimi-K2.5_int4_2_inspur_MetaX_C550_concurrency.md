# Kimi-K2.5_int4_2模型在inspur_MetaX_C550上的Benchmark基准测试报告

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
| **model_name** | Kimi-K2.5_int4_2 |
| **quantization_config** | int4 |
| **model_size** | 496G |
| **max_position_embeddings** | 262144 |
| **temperature** | N/A |
| **top_k** | N/A |
| **top_p** | N/A |
| **transformers_version** | 4.56.2 |
| **sglang_version** | 0.5.9+maca3.5.3.204 |
| **python_version** | 3.10.10 |


## 🤖 SGLang启动配置信息

| 参数名称                   | inspur_MetaX_C550 |
|------------------------|-------------|
| **Model Name** | Kimi-K2.5_int4_2 |
| **Attention Backend** | flashinfer |
| **Quantization** | w4a8_int8 |
| **Tp Size** | 16 |
| **Pp Size** | 1 |
| **Nnodes** | 2 |
| **Context Length** | 262144 |
| **Cuda Graph Max Bs** | 64 |
| **Max Running Requests** | 64 |
| **Max Queued Requests** | None |
| **Chunked Prefill Size** | 8192 |
| **Disable Radix Cache** | True |
| **Tool Call Parser** | kimi_k2 |
| **Reasoning Parser** | kimi_k2 |
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
| **模型**        | Kimi-K2.5_int4_2                           |     |
| **被测芯片**      | inspur_MetaX_C550 |     |
| **SGLang版本**   | 0.5.9                           |     |

---

## 📋 测试结果汇总

| 并发数 | 请求吞吐量 (req/s) | 输出Token吞吐量 (tok/s) | 总Token吞吐量 (tok/s) | TTFT P99 (ms) | TPOT P99 (ms) | E2E延迟均值 (ms) |
| ----------- | ----------- | ----------- | ----------- | ----------- | ----------- | ----------- |
| 32 | 0.03 | 52.87 | 2432.03 | 1202590.10 | 47.41 | 1192521.83 |
| 64 | 0.03 | 52.84 | 2430.50 | 2422100.16 | 46.53 | 2348201.18 |


## 📊 各并发级别性能柱状图

<img src="./concurrency_comparison.png" width="1000" />


## 📈 性能趋势分析

<img src="./performance_trends.png" width="1000" />

---

### 🎯 服务基准结果详情

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 成功请求数 | 1000 | 1000 |
| 测试持续时间 (s) | 37828.41 | 37852.28 |
| 总输入 tokens | 90000000 | 90000000 |
| 总生成 tokens | 2000000 | 2000000 |
| **请求吞吐量 (req/s)** | 0.03 | 0.03 |
| **输出 token 吞吐量 (tok/s)** | 52.87 | 52.84 |
| 峰值输出 token 吞吐量 (tok/s) | 327.00 | 111.00 |
| 峰值并发请求数 | 34 | 65 |
| **总 token 吞吐量 (tok/s)** | 2432.03 | 2430.50 |


### ⏱️ 端到端延迟 (E2E Latency)

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 平均 E2E 延迟 (ms) | 1192521.83 | 2348201.18 |
| 中位 E2E 延迟 (ms) | 1208254.90 | 2418139.26 |
| P90 E2E 延迟 (ms) | 1232412.36 | 2453542.71 |
| P99 E2E 延迟 (ms) | 1268376.33 | 2489275.83 |


### ⏱️ 首Token延迟 (TTFT)

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 平均 TTFT (ms) | 1129290.87 | 2284903.96 |
| 中位 TTFT (ms) | 1145005.00 | 2355764.75 |
| P99 TTFT (ms) | 1202590.10 | 2422100.16 |


### ⚡ 每Token生成时间 (TPOT)

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 平均 TPOT (ms) | 31.63 | 31.66 |
| 中位 TPOT (ms) | 31.35 | 31.40 |
| P99 TPOT (ms) | 47.41 | 46.53 |


### 🔄 Token间延迟 (ITL)

| 指标 | 32 并发 | 64 并发 |
|------|----------- | -----------|
| 平均 ITL (ms) | 31.63 | 31.66 |
| 中位 ITL (ms) | 21.03 | 21.06 |
| P95 ITL (ms) | 42.14 | 42.19 |
| P99 ITL (ms) | 42.99 | 43.10 |

---

## 📝 分析总结

### 1. 吞吐量性能分析

**请求吞吐量 (QPS)**: 随着并发级别增加，QPS持续上升。
中并发(32)平均 QPS: 0.03 req/s；
高并发(64)平均 QPS: 0.03 req/s；
最高 QPS 出现在 32 并发，达到 0.03 req/s。

**Token总吞吐量**: 最高达到 2432 tok/s (32 并发)。

### 2. 端到端延迟 (E2E Latency) 分析

E2E延迟随并发增加显著上升。
高并发平均 P99 E2E: 2489276ms；
最高 P99 E2E 出现在 64 并发，达到 2489276ms。

### 3. 首Token延迟 (TTFT) 分析

TTFT随并发增加显著上升。
高并发平均 P99 TTFT: 2422100ms；
最高 P99 TTFT 出现在 64 并发，达到 2422100ms。

### 4. Token生成时间 (TPOT) 分析

TPOT随并发增加也呈上升趋势。
高并发平均 P99 TPOT: 46.53ms；
最高 P99 TPOT 出现在 32 并发，达到 47.41ms。

### 5. Token间延迟 (ITL) 分析

ITL随并发增加呈上升趋势。
高并发平均 P99 ITL: 43.10ms；
最高 P99 ITL 出现在 64 并发，达到 43.10ms。

### 6. 综合评估

**吞吐量增长**: 从最低并发到最高并发，QPS增长了 0.0%。

---

<div align="center">
*报告生成时间: 2026-05-13*
</div>
