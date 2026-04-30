# MiniMax-M2.5模型在不同芯片下的SGLang基准测试报告

<div align="center">
**测试日期：** 2026-04-30

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
| **数据集**       | random                                 |     |
| **并发数**       | 1, 2, 4, 8, 10, 16, 32, 64, 80, 128    |     |
| **总请求数**      | 320                                    |     |
| **请求输入上下文长度** | 10240（10k）                             |     |
| **请求输出上下文长度** | 256（0.25k）                             |     |
| **模型**        | MiniMax-M2.5                           |     |
| **被测芯片**      | inspur_MetaX_C550, nvidia_h100 |     |

---

## 📈 各并发级别性能对比


### 1 并发

| 指标 | inspur_MetaX_C550 | nvidia_h100 |
|------|----------- | -----------|
| Request throughput (req/s) | 0.27 | **0.37** ⭐ |
| Output token throughput (tok/s) | 69.26 | **95.49** ⭐ |
| Total token throughput (tok/s) | 2839.48 | **3915.14** ⭐ |
| P99 TTFT (ms) | **596.38** ⭐ | 1181.54 |
| P99 TPOT (ms) | 12.44 | **9.89** ⭐ |
| P99 ITL (ms) | 14.88 | **9.90** ⭐ |

---

### 10 并发

| 指标 | inspur_MetaX_C550 | nvidia_h100 |
|------|----------- | -----------|
| Request throughput (req/s) | 0.91 | **1.75** ⭐ |
| Output token throughput (tok/s) | 232.70 | **447.09** ⭐ |
| Total token throughput (tok/s) | 9540.82 | **18330.76** ⭐ |
| P99 TTFT (ms) | 5277.45 | **1604.56** ⭐ |
| P99 TPOT (ms) | 40.89 | **21.28** ⭐ |
| P99 ITL (ms) | **28.12** ⭐ | 190.68 |

---


## 📊 芯片性能柱状图

<img src="./chip_comparison_c1_test_01_inspur_metax_c550_vs_nvidia_h100.png" width="1000" />
<img src="./chip_comparison_c10_test_01_inspur_metax_c550_vs_nvidia_h100.png" width="1000" />

---

## 📈 性能趋势对比图 (所有芯片)

<img src="./performance_trends_test_01_inspur_metax_c550_vs_nvidia_h100.png" width="1000" />

---

<div align="center">
*报告生成时间: 2026-04-30*
</div>
