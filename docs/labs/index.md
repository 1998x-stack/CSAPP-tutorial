---
title: CSAPP 实验工程
description: C11/POSIX 教学实验、可复现测试、固定输入输出与错误路径
---

# CSAPP 实验工程

V0.3 将概念讲解配套为**可以编译、可以运行、可以复核**的独立小实验，不要求安装后端服务。所有代码为本项目自主编写的示例，并非官方 CS:APP 实验材料。

## 快速开始

在 Linux 或 macOS 安装 CMake 3.20+、C11 编译器和 Python 3.10+：

~~~bash
cmake -S . -B .build/labs -DCMAKE_BUILD_TYPE=Debug
cmake --build .build/labs --parallel
ctest --test-dir .build/labs --output-on-failure

# 演示 Cache 中的命中、缺失和 LRU 替换：
./.build/labs/lab_cache_sim 4 2 4 tests/labs/fixtures/lru.trace
# hits=4 misses=5 evictions=2
~~~

也可执行 `npm run test:labs`。C 语言实验不需要 Node.js；Node.js 用于构建文档站和整体质量门禁。

## 实验目录

| 主题 | 教学关联 | 可观察结果 | 源码 |
| --- | --- | --- | --- |
| 对象表示与位运算 | [整数](/chapters/02-integers) | 字节序；移位与字段提取边界 | [bit-operations](https://github.com/1998x-stack/CSAPP-tutorial/tree/main/labs/bit-operations) |
| 二维数组内存布局 | [汇编与数据](/chapters/07-data-and-memory-layout) | 行优先地址偏移与源代码关系 | [assembly](https://github.com/1998x-stack/CSAPP-tutorial/tree/main/labs/assembly) |
| Cache 几何与 LRU | [Cache](/chapters/12-cache) | 命中、未命中、逐出；错误输入 | [cache](https://github.com/1998x-stack/CSAPP-tutorial/tree/main/labs/cache) |
| 共享文件偏移 | [系统 I/O](/chapters/19-system-io) | POSIX `dup` 共享当前文件位置 | [processes](https://github.com/1998x-stack/CSAPP-tutorial/tree/main/labs/processes) |
| 动态数组增长 | [内存分配](/chapters/18-memory-allocation) | `realloc` 所有权与容量不变量 | [memory](https://github.com/1998x-stack/CSAPP-tutorial/tree/main/labs/memory) |
| 生产者–消费者 | [并发编程](/chapters/23-concurrency-patterns) | 有界队列、关闭通知、无丢失数据 | [concurrency](https://github.com/1998x-stack/CSAPP-tutorial/tree/main/labs/concurrency) |

## 验收方式

`tests/labs/fixtures/` 存放固定输入，`tests/labs/golden/` 存放标准输出与期望错误信息，`tests/labs/check_case.py` 比较完整输出和退出码。CI 使用 GCC 与 Clang 两套编译器，开启 `-Wall -Wextra -Wpedantic -Werror`。

实验专注于**正确性**：Cache 是软件教学模型，不反映真实 CPU 缓存表现；线程实验检验结果不变量，不根据运行快慢做性能推断。

## 逐项练习

阅读 [实验练习与验收](/labs/exercises)，按照六个模块逐步完成预测、验证、修改与复查。

## 挑战与扩展

先解释固定示例为什么满足预期，再修改数据规模和边界条件，观察哪些不变量应该保持不变。每个可变实验都应增加黄金测试，避免只依赖人工观察。
