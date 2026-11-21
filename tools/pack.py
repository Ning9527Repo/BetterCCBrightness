#!/usr/bin/env python3
"""Package the patched tweak into a RootHide deb without dpkg/dark tooling."""
import io
import os
import sys
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "./Library/MobileSubstrate/DynamicLibraries"


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


def main(dylib_path):
    dylib = open(dylib_path, "rb").read()
    plist = open(os.path.join(ROOT, "BetterCCBrightness.plist"), "rb").read()
    control = open(os.path.join(ROOT, "control")).read()
    control = "\n".join(
        ("Installed-Size: %d" % (len(dylib) // 1024)) if line.startswith("Installed-Size") else line
        for line in control.splitlines()
    ) + "\n"

    cbuf = io.BytesIO()
    with tarfile.open(fileobj=cbuf, mode="w:gz", format=tarfile.GNU_FORMAT) as tf:
        add_file(tf, "./control", control.encode(), 0o644)
    dbuf = io.BytesIO()
    with tarfile.open(fileobj=dbuf, mode="w:gz", format=tarfile.GNU_FORMAT) as tf:
        for d in ("./Library", "./Library/MobileSubstrate", BASE):
            add_dir(tf, d)
        add_file(tf, BASE + "/BetterCCBrightness.dylib", dylib)
        add_file(tf, BASE + "/BetterCCBrightness.plist", plist, 0o644)
    os.makedirs(os.path.join(ROOT, "packages"), exist_ok=True)
    out = os.path.join(ROOT, "packages",
                       "com.ning.betterccbrightness_1.0.2-ning1_iphoneos-arm64e.deb")
    with open(out, "wb") as f:
        f.write(b"!<arch>\n")
        f.write(member("debian-binary", b"2.0\n"))
        f.write(member("control.tar.gz", cbuf.getvalue()))
        f.write(member("data.tar.gz", dbuf.getvalue()))
    print(out, os.path.getsize(out))


if __name__ == "__main__":
    main(sys.argv[1])