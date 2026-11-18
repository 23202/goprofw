import sys, hashlib, struct

A = '/var/minis/attachments/uploads/DATA.bin'
B = '/var/minis/attachments/uploads/DATA_1.bin'
CH = 1 << 20

fa, fb = open(A, 'rb'), open(B, 'rb')
i = 0
ranges = []
cur = None
same_blocks = 0
while True:
    a = fa.read(CH); b = fb.read(CH)
    if not a and not b: break
    if a == b:
        same_blocks += 1
        if cur: ranges.append(cur); cur = None
    else:
        # narrow down
        n = min(len(a), len(b))
        d = [k for k in range(0, n, 4096) if a[k:k+4096] != b[k:k+4096]]
        start = i * CH + (d[0] if d else 0)
        # exact first/last diff within block
        first = next(k for k in range(n) if a[k] != b[k])
        last = next(k for k in range(n - 1, -1, -1) if a[k] != b[k])
        s = i * CH + first; e = i * CH + last
        if cur and s - cur[1] <= (1 << 20):
            cur = (cur[0], e)
        else:
            if cur: ranges.append(cur)
            cur = (s, e)
    i += 1
if cur: ranges.append(cur)

print('total chunks', i, 'identical chunks', same_blocks)
print('differing ranges (%d):' % len(ranges))
for s, e in ranges:
    print('  %#010x - %#010x  (%d bytes)' % (s, e, e - s + 1))
