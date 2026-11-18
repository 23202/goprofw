# GoPro / Milbeaut 相机固件逆向笔记

对 `DATA.bin`（257,600,064 B，`GPRO` 容器）的静态分析记录：容器格式、根文件系统、机型配置、8K60 能力链路、两版固件差异，以及可行的实验路线。

> 结论速览：**8K60 的限制不在 Linux 用户层，也不在配置文件里，而在加密的 RTOS 镜像（p2）**。两版固件的 Linux 侧（内核 / rootfs / 5 套机型配置 / 资源）完全一致，差异只在 p2 和各级签名。

## 文档索引

| 文件 | 内容 |
|---|---|
| [docs/01-container-format.md](docs/01-container-format.md) | GPRO 容器、分区表、镜像头字段、加密判定 |
| [docs/02-rootfs.md](docs/02-rootfs.md) | squashfs 结构、Yocto 用户层、关键二进制 |
| [docs/03-8k60.md](docs/03-8k60.md) | 8K/60 在 UI 配置、黑名单、capability 接口中的位置 |
| [docs/04-build-diff.md](docs/04-build-diff.md) | 两版固件逐字节对比结果 |
| [docs/05-boot-chain.md](docs/05-boot-chain.md) | 信任链推断、p1/p2/p3/p5/p6 分别是什么 |
| [docs/06-attack-surface.md](docs/06-attack-surface.md) | 运行时接口（ispterm / gpltcmd）、可行路线与风险 |
| [docs/07-todo.md](docs/07-todo.md) | 待验证清单与实验顺序 |
| [data/partitions.csv](data/partitions.csv) | 分区表原始数值 |
| [data/models.md](data/models.md) | 5 个机型的配置对照 |
| [tools/](tools) | 解包、差分、混合包生成脚本 |

## 快速开始

```sh
python3 tools/unpack.py DATA.bin out/          # 拆出 6 个分区
python3 tools/diff_chunks.py A.bin B.bin       # 分块差分
python3 tools/build_hybrid.py A.bin B.bin      # 用 B 的 RTOS 镜像生成混合包
```

工具目录里的脚本默认使用本仓库作者手上的路径，实际使用时改文件头部的常量即可。

## 样本

- A 包：`WFPGG` + crc32 `00f570a0`
- B 包：`WFPGE` + crc32 `3847bb71`
- 两包 `DATA.bin` 大小完全相同（0xF5AAA40），分区表逐字节一致

## 免责

仅为自有设备的静态分析与学习记录。涉及签名、刷写、交叉刷机的操作都有变砖风险，后果自负。
