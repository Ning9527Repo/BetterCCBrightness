#!/usr/bin/env python3
"""Dump deb structure and Mach-O load commands for the built package."""
import os
import struct
import sys
import tarfile
import tempfile


def main(deb):
    data = open(deb, "rb").read()
    assert data[:8] == b"!<arch>\n"
    pos, members = 8, {}
    while pos + 60 <= len(data):
        hdr = data[pos:pos + 60]
        name = hdr[0:16].decode().strip().rstrip("/")
        size = int(hdr[48:58].decode().strip())
        members[name] = data[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)
    print("members:", list(members))
    out = tempfile.mkdtemp()
    for key in list(members):
        if key.startswith("control.tar") or key.startswith("data.tar"):
            path = os.path.join(out, key)
            open(path, "wb").write(members[key])
            with tarfile.open(path) as tf:
                tf.extractall(out)
    print(open(os.path.join(out, "control")).read())
    dylib = None
    for root, _, files in os.walk(out):
        for f in files:
            if f.endswith(".dylib"):
                dylib = os.path.join(root, f)
    print("dylib:", dylib, os.path.getsize(dylib))
    buf = open(dylib, "rb").read()
    magic, cpu, sub, ft, ncmds, szcmds, flags = struct.unpack("<IiiIIII", buf[:28])
    print("subtype %#x flags %#x" % (sub & 0xFFFFFFFF, flags))
    off, libs = 32, []
    for _ in range(ncmds):
        cmd, cs = struct.unpack("<II", buf[off:off + 8])
        if cmd == 0xC:
            no = struct.unpack("<I", buf[off + 8:off + 12])[0]
            libs.append(buf[off + no:off + cs].split(b"\0")[0].decode("utf-8", "replace"))
        off += cs
    print("load dylibs:")
    for l in libs:
        print("  ", l)


if __name__ == "__main__":
    main(sys.argv[1])