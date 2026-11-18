#!/usr/bin/env python3
# 生成 "混合固件"：保留 A 包的 Linux 侧（kernel/rootfs/资源/DTB），
# 只把 RTOS 镜像（p2, 0x19A20..0x6A6AC30, 111,481,360 字节）替换成 B 包的。
# 两个包的 p2 大小完全相同，所以分区表不需要改；只需重算 CAMFWV.bin 里的 CRC32。
import zlib, os, sys

A = '/var/minis/attachments/uploads/DATA.bin'      # MISSION 包
B = '/var/minis/attachments/uploads/DATA_1.bin'    # PRO 包
OUT_DIR = '/var/minis/workspace/fw/hybrid'

P2_START, P2_END = 0x19A20, 0x6A6AC30

def crc32_of(path):
    h = 0
    with open(path, 'rb') as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            h = zlib.crc32(b, h)
    return h

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, 'DATA_hybrid.bin')
    with open(A, 'rb') as fa, open(B, 'rb') as fb, open(out, 'wb') as fo:
        # 1. A 的 0 .. P2_START
        left = P2_START
        while left:
            b = fa.read(min(1 << 22, left)); fo.write(b); left -= len(b)
        # 2. B 的 p2（含 GPRO 头与自带签名）
        fb.seek(P2_START)
        left = P2_END - P2_START
        while left:
            b = fb.read(min(1 << 22, left)); fo.write(b); left -= len(b)
        # 3. A 的 P2_END .. 结尾
        fa.seek(P2_END)
        while True:
            b = fa.read(1 << 22)
            if not b:
                break
            fo.write(b)
    crc = crc32_of(out)
    print('hybrid size', os.path.getsize(out), 'crc32 %08x' % crc)

    # 4. 重写 CAMFWV.bin：保留 A 的产品字母 WFPGG，替换 0x24 起的 CRC32
    cam = bytearray(open('/var/minis/attachments/uploads/CAMFWV.bin', 'rb').read())
    cam[0x24:0x28] = crc.to_bytes(4, 'little')
    with open(os.path.join(OUT_DIR, 'CAMFWV_hybrid.bin'), 'wb') as f:
        f.write(cam)
    print('CAMFWV_hybrid.bin magic', cam[:6], 'crc field %08x' % crc)

if __name__ == '__main__':
    main()
