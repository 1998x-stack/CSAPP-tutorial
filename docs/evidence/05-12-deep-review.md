# CSAPP 第 05–12 章：第二轮逐章技术断言与证据范围

以下仅记录本轮新增的事实/推导；并非对原 8 个页面全部原有断言的完整复核。

| 章 | 被验证的教学结论 | 查证依据 | 可执行断言 |
| --- | --- | --- | --- |
| 05 | 8 位 0x80−0x01 得 SF=0、OF=1、CF=0，JL 真而 JB 假 | [Intel Software Developer's Manual](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html) CMP/Jcc | `python3 examples/deep-ch05-12.py 05` |
| 06 | System V AMD64 普通调用前对齐，call 压入 8B 返回地址，入口 %rsp mod16=8 | [x86-64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI/) | `python3 examples/deep-ch05-12.py 06` |
| 07 | 在 int 大小/对齐均 4 的模型里，char/int/char 成员偏移 0/4/8，整体大小 12 | [offsetof(3)](https://man7.org/linux/man-pages/man3/offsetof.3.html)、C11 6.7.2.1 | `python3 examples/deep-ch05-12.py 07` 和页面 C 示例 |
| 08 | Y86-64 rmmovq 10B 编码，valA 来源、valE 地址与内存写入路径 | [CS:APP HCL 描述](https://csapp.cs.cmu.edu/3e/waside/waside-hcl.pdf) | `python3 examples/deep-ch05-12.py 08` |
| 09 | 教材 PIPE 的紧邻 load-use 需停顿 F/D 并向 E 注入 bubble | [官方模拟器指南](https://csapp.cs.cmu.edu/3e/simguide.pdf) | `python3 examples/deep-ch05-12.py 09` |
| 10 | 单操作每元素/均匀独立链模型 CPE ≥ max(L/K,1/R) | [CS:APP](https://csapp.cs.cmu.edu/3e/)、[Intel 优化手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html) | `python3 examples/deep-ch05-12.py 10` |
| 11 | 1024 次 4B 元素访问，64B 行/4KiB 页下各 stride 的行与页触及数 | [CS:APP Memory Hierarchy](https://csapp.cs.cmu.edu/3e/) | `python3 examples/deep-ch05-12.py 11` |
| 12 | C128B/B16B 时直接映射 MMMM，两路组相联 MMHH | [CS:APP Cache Organization](https://csapp.cs.cmu.edu/3e/) | `python3 examples/deep-ch05-12.py 12` |

## 禁止混淆的边界

- Python 案例均为完全确定的 toy models，不是 CPU cycle、cache miss、功耗、性能跑分的实测数据。
- Y86-64 机器码不是 x86-64 机器码；五级 PIPE 的数据冒险处理不能强行泛化到现代乱序 CPU。
- 结构体成员偏移按公开假设计算，真实 ABI 应编译 HTML 中的 C11 offsetof 程序查看。
- CPE 理论下界不自动包含访存开销；拆分浮点累加顺序可能改变数值结果。
- SVG 为独立绘制的因果示意；注释和 alt/desc 允许读者在图像缺失时仍找到文字解释。

验证：`npm test && npm run build`；需要浏览器工作流实际通过，才能声称完成移动端图解与交互验收。