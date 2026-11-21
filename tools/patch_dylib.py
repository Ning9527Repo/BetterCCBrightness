#!/usr/bin/env python3
"""Rewrite the substrate load command for the target jailbreak layout.

usage: patch_dylib.py <dylib> [roothide|rootless]

  roothide -> @loader_path/.jbroot/usr/lib/libsubstrate.dylib
  rootless -> /var/jb/usr/lib/libsubstrate.dylib

Theos links the legacy rootful stub (/Library/Frameworks/CydiaSubstrate.framework/
CydiaSubstrate). That absolute path does not exist on RootHide or rootless
bootstraps, dyld cannot load the tweak and injection is silently skipped.
"""
import struct
import sys

OLD_PREFIX = b"/Library/Frameworks/CydiaSubstrate"
TARGETS = {
    "roothide": b"@loader_path/.jbroot/usr/lib/libsubstrate.dylib",
    "rootless": b"/var/jb/usr/lib/libsubstrate.dylib",
}


def patch_commands(data, base, new_path):
    magic = struct.unpack("<I", bytes(data[base:base + 4]))[0]
    if magic != 0xFEEDFACF:
        raise SystemExit("not a 64-bit Mach-O at %#x" % base)
    ncmds = struct.unpack("<I", bytes(data[base + 16:base + 20]))[0]
    off = base + 32
    patched = 0
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack("<II", bytes(data[off:off + 8]))
        if cmd == 0xC:
            nameoff = struct.unpack("<I", bytes(data[off + 8:off + 12]))[0]
            start = off + nameoff
            cur = bytes(data[start:off + cmdsize]).split(b"\0")[0]
            if cur.startswith(OLD_PREFIX):
                if len(new_path) > len(cur):
                    raise SystemExit("replacement path longer than original")
                data[start:start + len(cur)] = new_path + b"\0" * (len(cur) - len(new_path))
                patched += 1
        off += cmdsize
    return patched


def main(path, scheme="roothide"):
    new_path = TARGETS[scheme]
    data = bytearray(open(path, "rb").read())
    magic = struct.unpack(">I", data[:4])[0]
    total = 0
    if magic in (0xCAFEBABE, 0xCAFEBABF):
        for i in range(struct.unpack(">I", data[4:8])[0]):
            _, _, off, size, _ = struct.unpack(">iiIII", data[8 + i * 20:28 + i * 20])
            total += patch_commands(data, off, new_path)
    else:
        total = patch_commands(data, 0, new_path)
    open(path, "wb").write(data)
    print("patched substrate load commands (%s):" % scheme, total)
    if total == 0:
        raise SystemExit("no substrate load command found")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "roothide")