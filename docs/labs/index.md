---
title: 实验总览
description: 可独立运行的 C11 示例与后续实验规划
---

# 实验总览

## V0.2 可运行示例

| 示例 | 对应课程 | 验证目标 | 代码 |
| --- | --- | --- | --- |
| 字节表示 | [整数](/chapters/02-integers) | 使用 C 标准对象表示观察本机字节序 | [representation.c](https://github.com/1998x-stack/CSAPP-tutorial/blob/main/labs/bit-operations/representation.c) |
| Cache 地址拆解 | [Cache](/chapters/12-cache) | 组索引与块内偏移计算 | [cache_geometry.c](https://github.com/1998x-stack/CSAPP-tutorial/blob/main/labs/cache/cache_geometry.c) |

在仓库根目录运行：

~~~bash
npm run check:snippets
~~~

## 后续实验模块

- 汇编与编译器优化：对照 C、汇编、输入与输出
- 进程与文件描述符：观察回收、共享和错误恢复
- 内存：对齐、分配与资源生命周期
- 并发：线程同步、队列关闭与竞态测试

各模块目前属于实验规范和设计预留；尚未实现完整的官方 CSAPP Lab。实验代码应独立开发并遵守第三方内容授权限制。

