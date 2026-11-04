# 可运行系统实验

本目录包含自主编写、可编译验证的 C11 与 POSIX 学习项目，不包括需要单独授权的官方 CS:APP Lab 发行包。

## 标准流程

1. 阅读 `docs/labs/index.md` 中对应主题和输出说明。
2. 阅读对应子目录的 README 和代码。
3. 使用 `cmake -S . -B .build/labs` 与 `cmake --build .build/labs --parallel` 构建。
4. 使用 `ctest --test-dir .build/labs --output-on-failure` 运行全部黄金测试。
5. 对每个实验，记录假设、预测结果和实际结果。
6. 修改代码前先扩展对应的 `tests/labs/fixtures/` 或 `tests/labs/golden/`。

**平台说明：** 进程与线程实验依赖 POSIX，并在 Linux CI 使用 GCC/Clang 验证。Cache、内存、整数等模块是教育用模型，不能视为机器级真实性能测量。
