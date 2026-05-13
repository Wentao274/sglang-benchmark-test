
<style>
@page {
    margin: 2cm;
    @bottom-center {
        content: "九章云极";
        font-size: 12pt;
        color: #ccc;
        opacity: 0.3;
    }
}

body {
    position: relative;
}

/* 背景水印图片 */
body::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 99998 !important;
    pointer-events: none;
    background-image: url('watermark.png');
    background-repeat: repeat;
    background-position: center;
    opacity: 0.05;
}

/* 主水印 - 确保在所有内容之上 */
.watermark {
    position: fixed !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) rotate(-45deg) !important;
    font-size: 80px !important;
    color: rgba(200, 200, 200, 0.15) !important;
    pointer-events: none !important;
    z-index: 99999 !important;
    white-space: nowrap !important;
    font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif !important;
}

/* 确保图片在水印下方 */
img {
    z-index: 1 !important;
    position: relative !important;
}

/* 打印时确保水印可见 */
@media print {
    .watermark {
        z-index: 99999 !important;
    }
}
</style>

<div class="watermark">九章云极</div>


# 浪潮MetaX-C550、英伟达H100 - 单节点MiniMax-M2.5模型整体测试比对报告

<div align="center">
*测试日期：2026-04-22 ~ 2026-04-26 <br>
*测试人员：九章云极

</div>

---

## 1. 测试场景及概况

### 1.1 测试场景列表
| 序号  | 测试场景                 |
|-----|----------------------|
| 场景一 | sglang benchmark基准测试 |
| 场景二 | 单、多并发超长上下文请求         |


### 1.2 模型推理测试问题汇总

- **关闭思考模式不生效**，关闭思考模式后，请求响应输出依然有思考模型下的content: 如果parser是minimax-append-think, 思考的内容会在content里以<think>...</think>标签对包裹。如果parser是minimax，思考的内容会直接显示在reasoning_content里

---

---

## 测试场景一：sglang/vllm benchmark基准测试

### 📊 测试概览

| 项目            | 配置                                                                                          | 备注  |
|---------------|---------------------------------------------------------------------------------------------|-----|
| **数据集**       | inspur_MetaX_C550 (ShareGPT_V3_unfiltered_cleaned_split.json, random), nvidia_h100 (random) |     |
| **并发数**       | 1, 2, 4, 8, 10, 16, 32, 64, 80, 128                                                         |     |
| **总请求数**      | 320                                                                                         |     |
| **请求输入上下文长度** | 10240（10k）                                                                                  |     |
| **请求输出上下文长度** | 256（0.25k）                                                                                  |     |
| **被测芯片**      | inspur_MetaX_C550, nvidia_h100                                                              |     |
| **被测模型**      | inspur_MetaX_C550 (MiniMax-M2.5-W8A8), nvidia_h100 (MiniMax-M2.5)                           |     |


### 📊 芯片性能对比柱状图
**1并发**

<img src="./chip_comparison_c1_test_01_inspur_metax_c550_vs_nvidia_h100.png" width="1000" />


### 📈 性能趋势对比图

<img src="./performance_trends_test_01_inspur_metax_c550_vs_nvidia_h100.png" width="1000" />

### 📈 各指标随并发级别性能对比详情

#### 总token吞吐量（Total token throughput (tok/s)）

| 并发数 | inspur_MetaX_C550 | nvidia_h100    |
|-----|-------------------|----------------|
| 1   | 2839.48           | **4745.14** ⭐ |
| 2   | 4336.07           | **8217.92** ⭐ |
| 4   | 6617.46           | **13310.92** ⭐ |
| 8   | 8757.21           | **19176.39** ⭐ |
| 10  | 9540.82           | **21996.95** ⭐ |
| 16  | 11348.92          | **26494.03** ⭐ |
| 32  | 13322.11          | **32831.81** ⭐ |
| 64  | 14744.38          | **38566.45** ⭐ |
| 80  | 14765.49          | **38638.21** ⭐ |
| 128 | 14756.01          | **38585.00** ⭐ |


#### 首token延迟（P99 TTFT (ms)）

| 并发数 | inspur_MetaX_C550 | nvidia_h100    |
|-----|-------------------|----------------|
| 1   | 596.38            | **286.01** ⭐  |
| 2   | 1097.81           | **466.40** ⭐  |
| 4   | 2137.97           | **826.89** ⭐   |
| 8   | 4216.68           | **1364.44** ⭐  |
| 10  | 5277.45           | **1534.23** ⭐  |
| 16  | 8059.86           | **2630.84** ⭐  |
| 32  | 15782.91          | **6556.86** ⭐  |
| 64  | 31672.66          | **12557.76** ⭐ |
| 80  | 53556.78          | **19679.20** ⭐ |
| 128 | 76792.15          | **29645.32** ⭐ |

---

---

## 测试场景二：超长上下文请求测试
**测试目标**：对超长上下文的请求，使用sglang/vllm bench serve工具对并发数逐级增加场景的性能基准验证.

### 📊 测试概览

| 项目            | 配置                                                                                  | 备注  |
|---------------|-------------------------------------------------------------------------------------|-----|
| **数据集**       | inspur_MetaX_C550 (ShareGPT_V3_unfiltered_cleaned_split.json), nvidia_h100 (random) |     |
| **并发数**       | 1, 2, 4, 8, 10                                                                      |     |
| **总请求数**      | 100                                                                                 |     |
| **请求输入上下文长度** | 194560（190k）                                                                        |     |
| **请求输出上下文长度** | 1024（1k）                                                                            |     |
| **被测芯片**      | inspur_MetaX_C550, nvidia_h100                                                      |     |
| **被测模型**      | inspur_MetaX_C550 (MiniMax-M2.5-W8A8), nvidia_h100 (MiniMax-M2.5)                   |     |



### 📊 芯片性能对比柱状图

**1并发**

<img src="./chip_comparison_c1_test_02_inspur_metax_c550_vs_nvidia_h100.png" width="1000" />

### 📈 各并发级别性能对比详情

#### Total token throughput (tok/s)

| 并发数 | inspur_MetaX_C550 | nvidia_h100     |
|-----|-------------------|-----------------|
| 1   | 2424.14           | **8921.40** ⭐   |
| 2   | 2610.79           | **11850.06** ⭐  |
| 4   | 2739.69           | **13726.45** ⭐  |
| 8   | 2741.37           | **14443.68** ⭐  |
| 10  | 2739.59           | **14398.41** ⭐  |


#### P99 TTFT (ms)

| 并发数 | inspur_MetaX_C550 | nvidia_h100       |
|-----|-------------------|-------------------|
| 1   | 63374.54          | **10539.10** ⭐    |
| 2   | 126438.40         | **20205.87** ⭐    |
| 4   | 252746.14         | **37530.99** ⭐    |
| 8   | 550123.80         | **81506.35** ⭐    |
| 10  | 721962.01         | **108342.29** ⭐   |

---

---
