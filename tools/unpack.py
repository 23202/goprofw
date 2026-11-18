#!/usr/bin/env python3
# GoPro / GPRO 固件 DATA.bin 解包脚本
# 用法: python3 unpack.py DATA.bin [输出目录]
import sys, os, struct, hashlib

MAGIC = b'GPRO'

def parse(path):
    f = open(path, 'rb')
    f.seek(0, 2); L = f.tell()
    f.seek(0); hdr = f.read(0x200)
    entries = []
    off = 0x200
    while off + 16 <= L:
        f.seek(off); h = f.read(16)
        if len(h) < 16: break
        name = h[0:8].rstrip(b'\x00')
        f1, sz = struct.unpack('<II', h[8:16])
        if sz == 0 or off + 16 + sz > L:
            print('stop: bad size at %#x (%d)' % (off, sz)); break
        f.seek(off + 16); magic = f.read(4)
        entries.append(dict(offset=off, name=name, flags=f1, size=sz,
                            payload=off + 16, magic=magic))
        off += 16 + sz
    return hdr, entries, L

def gpro_header(f, payload):
    f.seek(payload); h = f.read(0x200)
    if h[:4] != MAGIC: return None
    return dict(sig96=h[0x04:0x64].hex(),
                key_slot=h[0xa4:0xb4].hex(),
                v1=struct.unpack('<I', h[0xb4:0xb8])[0],
                v2=struct.unpack('<I', h[0xb8:0xbc])[0],
                v3=struct.unpack('<I', h[0xbc:0xc0])[0],
                v4=struct.unpack('<I', h[0xc0:0xc4])[0],
                v5=struct.unpack('<I', h[0xc4:0xc8])[0],
                tag=h[0xc8:0xd8].hex())

def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else 'out'
    os.makedirs(out, exist_ok=True)
    f = open(src, 'rb')
    hdr, ents, L = parse(src)
    print('file size %d (%#x), header magic %r' % (L, L, hdr[:4]))
    for i, e in enumerate(ents, 1):
        print('\n[%d] @%#x  name=%r flags=%#x size=%d  payload=%#x magic=%r'
              % (i, e['offset'], e['name'], e['flags'], e['size'], e['payload'], e['magic']))
        info = gpro_header(f, e['payload']) if e['magic'] == MAGIC else None
        if info: print('     GPRO:', info)
        # 提取
        fn = os.path.join(out, 'part%d_%s.bin' % (i, e['magic'].decode('latin1')))
        f.seek(e['payload'])
        left = e['size']
        with open(fn, 'wb') as o:
            while left:
                b = f.read(min(1 << 20, left))
                if not b: break
                o.write(b); left -= len(b)
        print('     ->', fn, hashlib.sha256(open(fn,'rb').read()).hexdigest()[:16])

if __name__ == '__main__':
    main()
