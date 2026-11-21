#!/usr/bin/env python3
"""Package the patched tweak into a deb for the requested architecture.

usage: pack.py <dylib> <arm64e|arm64>

  arm64e -> RootHide layout, .deb under packages/, Architecture iphoneos-arm64e
  arm64  -> rootless layout under var/jb, Architecture iphoneos-arm64
"""
import io
import os
import sys
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LAYOUTS = {
    "arm64e": ("./Library/MobileSubstrate/DynamicLibraries", "iphoneos-arm64e"),
    "arm64": ("./var/jb/Library/MobileSubstrate/DynamicLibraries", "iphoneos-arm64"),
}
DIRS = {
    "arm64e": ("./Library", "./Library/MobileSubstrate"),
    "arm64": ("./var", "./var/jb", "./var/jb/Library", "./var/jb/Library/MobileSubstrate"),
}


def add_file(tf, name, data, mode=0o755):
    ti = tarfile.TarInfo(name)
    ti.size = len(data)
    ti.mode = mode
    ti.uid = 0
    ti.gid = 0
    ti.uname = "root"
    ti.gname = "wheel"
    ti.mtime = 1763731200
    tf.addfile(ti, io.BytesIO(data))


def add_dir(tf, name):
    ti = tarfile.TarInfo(name)
    ti.type = tarfile.DIRTYPE
    ti.mode = 0o755
    ti.uid = 0
    ti.gid = 0
    ti.uname = "root"
    ti.gname = "wheel"
    ti.mtime = 1763731200
    tf.addfile(ti)


def member(name, data):
    hdr = ("%-16s%-12s%-6s%-6s%-8s%-10s`\n" % (name, "0", "0", "0", "100644", len(data))).encode()
    return hdr + data + (b"\n" if len(data) % 2 else b"")


def main(dylib_path, arch):
    base, debarch = LAYOUTS[arch]
    dylib = open(dylib_path, "rb").read()
    plist = open(os.path.join(ROOT, "BetterCCBrightness.plist"), "rb").read()
    lines = []
    for line in open(os.path.join(ROOT, "control")).read().splitlines():
        if line.startswith("Installed-Size:"):
            line = "Installed-Size: %d" % (len(dylib) // 1024)
        if line.startswith("Architecture:"):
            line = "Architecture: " + debarch
        if line.strip():
            lines.append(line)
    control = "\n".join(lines) + "\n"

    cbuf = io.BytesIO()
    with tarfile.open(fileobj=cbuf, mode="w:gz", format=tarfile.GNU_FORMAT) as tf:
        add_file(tf, "./control", control.encode(), 0o644)
    dbuf = io.BytesIO()
    with tarfile.open(fileobj=dbuf, mode="w:gz", format=tarfile.GNU_FORMAT) as tf:
        for d in DIRS[arch]:
            add_dir(tf, d)
        add_dir(tf, base)
        add_file(tf, base + "/BetterCCBrightness.dylib", dylib)
        add_file(tf, base + "/BetterCCBrightness.plist", plist, 0o644)

    out_dir = os.path.join(ROOT, "packages")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "com.ning.betterccbrightness_1.0.2_%s.deb" % debarch)
    with open(out, "wb") as f:
        f.write(b"!<arch>\n")
        f.write(member("debian-binary", b"2.0\n"))
        f.write(member("control.tar.gz", cbuf.getvalue()))
        f.write(member("data.tar.gz", dbuf.getvalue()))
    print(out, os.path.getsize(out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])