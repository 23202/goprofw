# 06 · 运行时接口与可行路线

破签名不划算。真正的机会在"不改固件就能和 RTOS 说话"。

## 现成工具

| 工具 | 路径 | 说明 |
|---|---|---|
| `ispterm` / `gpRTOSConsole` | `/usr/bin/ispterm`、`/usr/local/gopro/bin/gpRTOSConsole` | 同一套代码。`Usage: ispcmd [t=TTY]`，默认 `/dev/ttyGS0`；也可走 `/proc/device-tree/shared_commem/term-io-addr` / `term-io-size` 共享内存 |
| `gpltcmd` | `/usr/local/gopro/bin/gpltcmd` | mbox 测试命令套件（`gptest_exec_t_cmd`，带 suite/usage 框架） |
| `gpsend` | 同上 | IPC / mbox 消息发送 |
| `gpChpTestChannel` | 同上 | "MFG builds 用来跑 Linux 命令的测试通道"，带 `validateCardID` 卡号白名单 |

`ispterm` 打印的原文：

```
version 1.0
Usage:
  ispcmd [t=TTY]
  t=TTY        : tty path (TTY=Full path)
The RTOS connection is closed when you input "close ispterm".
Example:
  ispcmd t=/dev/ttyGS0
```

## 已知的 RTOS 命令样例

`/usr/local/gopro/scripts/update` 里：

```sh
echo a:\> t hiber wipeout
```

说明 RTOS 那头是个 `a:\>` 提示符的菜单式 shell，且接受 `t hiber wipeout` 这类命令。

## 路线排序（成本 / 风险）

| 路线 | 做什么 | 风险 | 能证明什么 |
|---|---|---|---|
| R1 | 进 Linux，跑 `ispterm`，只读查询 sensor 型号 / 能力表 / 最大帧率 | 无 | 8K60 是"UI 没给"还是"管线不支持" |
| R2 | `gpltcmd` 列测试套件，找 video/res/fps 相关命令 | 无 | RTOS 是否暴露设置入口 |
| R3 | 抓 `gplogd` 日志，手动切 8K 看报错 | 无 | 同上，且能拿到错误码 |
| R4 | SD `arm-ep/` 覆盖 `settings.json`（需 `GP_NO_HIBER`，先 remount rw） | 低 | 界面能否出现 8K60 |
| R5 | 改工厂数据 `cammodel` | 中（可改回） | 机型是否纯软件分档 |
| R6 | 刷混合包（A 的 Linux 侧 + B 的 p2） | 高（可能变砖） | 验签范围 + 硬件一致性 |

R1→R3 全部无风险且信息量最大，建议先做完再决定要不要碰 R6。

## 拿到 root 的前提

rootfs 里有 `adb_script.sh`、`usb30dev_adb_func.sh`、`adb_deinit_script.sh`，
说明设备支持 ADB 通道（通常需要开发者/工厂模式）。`gpChpTestChannel` 还带卡号白名单校验
（`validateCardID` / `getCardIDStr`），大概率只对特定序列号开放。

## 风险提示

- 任何写 flash 的操作，先确认 recovery / 下载模式可用。
- R4 改的是只读分区挂载后的运行时副本，重启即失效，安全，但要先确认 remount 是否被接受。
- R6 之前务必把原厂 `DATA.bin` 完整备份。
