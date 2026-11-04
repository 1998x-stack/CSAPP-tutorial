---
title: 实验练习与验收
description: 从运行程序到预测结果、测试边界与解释行为
---

# 实验练习与验收

**学习流程：** 阅读相关章节、预测程序输出、运行对应可执行文件、核对黄金测试、解释因果关系，最后自行修改一个边界条件并补充测试。统一操作入口见 [实验总览](/labs/)。

## 1. 位表示与移位

- 预测 `rotl32(0x12345678, 8)` 和位字段提取的结果。
- 思考为何无符号 32 位移位 32 位不能直接执行。
- 修改输入，再为零位移、完整 32 位字段添加断言。
- 验收：`ctest --test-dir .build/labs -R "bit_math|endian" --output-on-failure`。

## 2. 二维数组地址计算

- 对一个 3×4 的 `int` 数组，计算 `values[1][2]` 与数组起点的字节偏移。
- 解释为什么 `row*columns+col` 等于行优先的元素下标。
- 比较 `-O0` 与 `-O2` 的汇编：机器指令不同，但可观察结果应保持一致。
- 验收：`ctest --test-dir .build/labs -R matrix_layout --output-on-failure`。

## 3. Cache 与 LRU

- 给定 4 组、2 路、16 字节一行，先逐条手工计算访问轨迹的 Hit/Miss。
- 运行 `lab_cache_sim`，比较标准输出。
- 改变组数或访问顺序，尝试设计一段会产生逐出的轨迹，并保存为新的 fixture 与 golden 文件。
- 验收：`ctest --test-dir .build/labs -R cache --output-on-failure`，同时测试不合法的几何参数和 trace。
- 注意该模拟器并不代表真实 CPU 的 Cache 性能。

## 4. 共享文件偏移

- 预测两个通过 `dup()` 得到的 fd 交替读取同一文件后，文件位置会发生什么变化。
- 与“两次独立 open 文件”对比，说明共享的是文件描述符数值还是内核中的打开文件描述。
- 验收：`ctest --test-dir .build/labs -R file_offset --output-on-failure`。

## 5. 安全的动态数组扩容

- 按 2 倍增长策略，预测装入 6 个元素后容量为什么为 8。
- 解释为什么必须用临时指针接收 `realloc()` 返回值，及应当在何时 `free()`。
- 自行扩展测试，覆盖容量 0、边界容量及输入长度限制。
- 验收：`ctest --test-dir .build/labs -R dynamic_array --output-on-failure`。

## 6. 生产者–消费者队列

- 解释“队列为空”和“生产者已经关闭”为什么是不同状态。
- 说明为什么条件变量必须与循环检查配合。
- 分析为什么两个消费者的各自处理数量可能变化，但总计和校验和必须固定。
- 验收：`ctest --test-dir .build/labs -R bounded_queue --output-on-failure`，包括 20 次重复测试。

## 结束标准

能够在 Linux 上用 GCC 与 Clang 构建所有实验、解释每项黄金测试的输入和输出，并为至少一项改动补上失败路径或边界测试。该标准衡量的是**可复现的理解**，不是硬件性能分数。
