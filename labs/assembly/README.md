# 二维数组与汇编地址计算

构建并运行 `lab_matrix_layout`，验证 3×4 的 C 数组 `values[1][2]` 的行优先偏移等于 24 字节（在项目目标的 4 字节 int 平台上）。

自行观察编译器生成的汇编（针对 GCC/Clang）：

~~~bash
cc -std=c11 -O2 -S labs/assembly/matrix_layout.c -o .build/matrix_layout.s
~~~

比较 `-O0` 与 `-O2` 的差异。**不要**断言编译器一定生成 `imul` 或某种 `lea`，可观察的是地址公式与程序输出。
