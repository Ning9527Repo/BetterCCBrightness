#!/usr/bin/env python3
"""Rewrite the substrate load command so the tweak resolves on RootHide.

Theos links the legacy rootful stub, which stamps the absolute path
/Library/Frameworks/CydiaSubstrate.framework/CydiaSubstrate into the Mach-O.
On a RootHide bootstrap that path does not exist, dyld refuses to load the
tweak and injection is silently skipped (no crash, no effect observed).
Working RootHide tweaks reference @loader_path/.jbroot/usr/lib/libsubstrate.dylib
instead, so the load command is rewritten in place and ldid re-signs afterwards.
"""
import struct
import sys

OLD_PREFIX = b"/Library/Frameworks/CydiaSubstrate"
NEW_PATH = b"@loader_path/.jbroot/usr/lib/libsubstrate.dylib"


def patch_commands(data, base):
    magic = struct.unpack("<I", bytes(data[base:base + 4]))[0]
    if magic != 0xFEEDFACF:
        raise SystemExit("not a 64-bit Mach-O at %#x" % base)
    ncmds = struct.unpack("<I", bytes(data[base + 16:base + 20]))[0]
    off = base + 32
    patched = 0
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack("<II", bytes(data[off:off + 8]))
        if cmd == 0xC:  # LC_LOAD_DYLIB
            nameoff = struct.unpack("<I", bytes(data[off + 8:off + 12]))[0]
            start = off + nameoff
            cur = bytes(data[start:off + cmdsize]).split(b"\0")[0]
            if cur.startswith(OLD_PREFIX):
                if len(NEW_PATH) > len(cur):
                    raise SystemExit("replacement path is longer than the original")
                data[start:start + len(cur)] = NEW_PATH + b"\0" * (len(cur) - len(NEW_PATH))
                patched += 1
        off += cmdsize
    return patched


def main(path):
    data = bytearray(open(path, "rb").read())
    magic = struct.unpack(">I", data[:4])[0]
    total = 0
    if magic in (0xCAFEBABE, 0xCAFEBABF):
        nslices = struct.unpack(">I", data[4:8])[0]
        for i in range(nslices):
            _, _, off, size, _ = struct.unpack(">iiIII", data[8 + i * 20:28 + i * 20])
            total += patch_commands(data, off)
    else:
        total = patch_commands(data, 0)
    open(path, "wb").write(data)
    print("patched substrate load commands:", total)
    if total == 0:
        raise SystemExit("no substrate load command found")


if __name__ == "__main__":
    main(sys.argv[1])