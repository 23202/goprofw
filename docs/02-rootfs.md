# 02 · 根文件系统

## squashfs 参数

```
magic            hsqs（小端 squashfs 4.0）
block_size       131072
compression      lz4 (id=5)
inodes           2072
fragments        229
bytes_used       66,087,859
mkfs_time        2026-09-18 01:24
```

解包命令：

```sh
dd if=DATA.bin of=rootfs.sqsh bs=1 skip=$((0x73A6670)) count=$((0x3F07010))
unsquashfs -d rootfs rootfs.sqsh
```

体积 115 MB。发行版是 Yocto 3.3.6（Poky），内核 5.15.127，glibc 2.33，aarch64。

## 目录要点

```
usr/local/gopro/bin/      GoPro 应用栈（22 MB）
usr/local/gopro/etc/      5 个机型的 settings.json（64/65/69/71/74）
usr/local/gopro/scripts/  update、dmsg、procmon、envdump、gpsend…
usr/lib/                  libgpCtrlD.so、libgpBlacklistHandler.so、libgpProto.so…
lib/modules/              仅 WiFi（bcmdhd.ko）与 shared-mem.ko，无 sensor 驱动
```

主程序：

| 程序 | 作用 |
|---|---|
| `gpControlD` | 控制协议守护进程（相机 API 的大脑） |
| `gpCamApi` / `gpHttpServer` | 本地/HTTP API |
| `gpDeviceManager` / `gpUsb` / `gpNet` / `gpWifi` | 外设与网络 |
| `gpRTOSConsole` | RTOS 控制台（= `ispcmd`） |
| `gpltcmd` / `gpsend` / `gpChpTestChannel` | mbox / IPC 命令通道 |
| `gpAWTuning` | ISP tuning 数据转发 |

## 关键结论

1. **没有 sensor 驱动**。`/lib/modules` 里只有无线和共享内存模块，说明采集/ISP/编码全在 RTOS 侧。
2. **没有 DATA.bin 解析代码**。全盘搜索 `GPRO` 只命中 gpHttpServer / gpCAHApp 的机型名字符串表（`GPRO`、`HERO5 Black`…）。
3. **升级由 RTOS 完成**。gpNet 里有 `FRW_POWER_BOOT_REASON_RESET_FWUPDATE`，`/etc/init.d` 里也看不到任何验签逻辑。
4. **arm-ep 覆盖通道**：`usr/local/gopro/scripts/update` 会把 SD 卡 `arm-ep/` 下的
   `bin/ cgi-bin/ etc/ scripts/ library/` 覆盖到 `/usr/local/gopro` 与 `/usr/lib`（需 `GP_NO_HIBER` 标记，
   且要先 `mount -o remount,rw /`）。这是不重刷固件替换 `settings.json` 的官方通道。

## 启动链（Linux 侧）

```
/etc/init.d/S10gopro      gpsv -k gpIpcSrv
/etc/init.d/S31_gpdev_extension  可选 SD 扩展（RAMFS_extension_gpdev.BIN → /tmp/fuse_x）
/etc/init.d/S32_mount_verify     等 RTOS 生成 /tmp/fuse_b/mfg.json
/etc/init.d/S70gopro      gpUsb、iptables、wifi bdata 校验
/etc/init.d/S75gopro2     gpControlD、gpBleSdkD、gpBtMan、womDaemon、gpHttpServer、gpPlatform、gpWifi
```

`/tmp/fuse_b` 是 RTOS 侧配置文件系统（`fwdwupdate -> /tmp/fuse_b`），里面的 `mfg.json` 带
`cammodel`、`camerasn`、`boardname` 等工厂数据。
