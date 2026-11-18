# 05 · 信任链与验签

## 推断的链路

```
SoC ROM（公钥/哈希烧在 OTP）
  └── p1  stage-1，104 KB ARM64（0xAA1F03E0 = mov x0, xzr 之类的指令）
        ├── p3  Linux 内核 Image
        ├── p5  DTB（d00dfeed，"socionext,milbeaut-tpk-evb"）
        └── p2  RTOS / ISP 固件（AES 密文）
```

证据：

- p5 是标准 FDT，含 `socionext,milbeaut-tpk-evb`、`Socionext TPK EVB`、`cpus / cpu@0`
  → **SoC 是 Socionext Milbeaut**，ARM 侧跑 Linux，图像管线跑在它自己的 RTOS/DSP 上。
- p1 两包只差 64 B 签名 → 它是不随机型变化的通用 stage-1。
- p2 是全文件唯一的 AES 密文（熵 8.000），也是唯一按机型变化的内容。

## 每张镜像都有签名

```
+0x004  96 B   签名（每次构建都不同，P-384 尺寸 → 疑似 ECDSA）
+0x0C8  16 B   tag（同上，且不是 header/body 的简单摘要，见 01 文档）
```

如果外层容器也是"整包签名"，内层签名就是冗余的——但嵌入式里"外层给升级器、内层给链式加载"的双保险很常见。

## 验签范围：无法离线判定

两种常见设计：

| 设计 | 行为 | 对混合包的影响 |
|---|---|---|
| A. 外层签全包 / 签清单 | bootloader 一次验完 | 换 p2 当场失败 |
| B. 外层只描述分区表，每级验下一级 | p2 自带签名有效 | 混合包可能通过 |

实测能排除的：tag 不是 md5/sha1/sha256/sha384/sha512 对 header、body 或其拼接的摘要（全部试过，不匹配）。

**结论：不做实验无法判断走的是 A 还是 B。**

## 不可绕过的部分

- 没有厂商私钥 → 无法重新签任何一张镜像。
- p1 的验签由 ROM 完成，密钥在芯片里 → 改 p1 死路。
- 即使混合包过签，RTOS 启动时可能核对 sensor / EEPROM（`CSI_MODEL_NUMBER` 就是它给的），
  硬件不匹配可能拒绝启动或降级到安全模式。
- 防回滚：容器表项 flags 高位、CAMFWV 版本占位、`CSI_FW_FORCE_UPDATE` 都可能参与。

## 变砖与恢复

验签失败通常停在 bootloader。Milbeaut 有 USB/UART 下载模式，但 Socinext 的烧写工具不公开。
**在确认 recovery 通道之前，不要写 flash。**

## 实践建议

1. 不要试图伪造签名。
2. 先确认相机自己的 fwupdate 是"先整包校验再写"还是"边写边校验"——这决定了实验失败是否可恢复。
3. 更划算的路线见 [06-attack-surface.md](06-attack-surface.md)：不打固件，直接和 RTOS 对话。
