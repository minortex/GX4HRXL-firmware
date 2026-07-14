#!/usr/bin/env python3
"""Inspect and extract AMI UAF resources without executing the wrapper."""

import argparse
import hashlib
import struct
from pathlib import Path


TAGS = (b"@UAF", b"@UII", b"@CMD", b"@ROM", b"@W64")


def records(data: bytes):
    found = []
    for tag in TAGS:
        start = 0
        while (offset := data.find(tag, start)) >= 0:
            if offset + 16 <= len(data):
                _, size, value, flags = struct.unpack_from("<4sIII", data, offset)
                found.append((offset, tag.decode(), size, value, flags))
            start = offset + 1
    return sorted(found)


def rom_stream(data: bytes) -> bytes:
    """Return the EFI compression stream stored in the final valid @ROM record."""
    candidates = []
    for offset, tag, resource_size, _checksum, _flags in records(data):
        if tag != "@ROM" or resource_size < 0x20:
            continue
        stream_offset = offset + 16
        if stream_offset + 8 > len(data):
            continue
        compressed, original = struct.unpack_from("<II", data, stream_offset)
        end = stream_offset + 8 + compressed
        if end <= len(data) and original and resource_size >= compressed:
            candidates.append(data[stream_offset:end])
    if not candidates:
        raise ValueError("no bounds-valid @ROM EFI compression stream found")
    return candidates[-1]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wrapper", type=Path)
    parser.add_argument("--stream", type=Path, help="write the EFI compression stream")
    parser.add_argument("--rom", type=Path, help="write the decompressed ROM")
    args = parser.parse_args()
    data = args.wrapper.read_bytes()
    print(f"wrapper size={len(data):#x} sha256={sha256(data)}")
    for offset, tag, size, value, flags in records(data):
        print(f"{offset:#010x} {tag} size={size:#x} value={value:#x} flags={flags:#x}")
    stream = rom_stream(data)
    compressed, original = struct.unpack_from("<II", stream)
    print(f"ROM stream compressed={compressed:#x} original={original:#x} sha256={sha256(stream)}")
    if args.stream:
        args.stream.parent.mkdir(parents=True, exist_ok=True)
        args.stream.write_bytes(stream)
    if args.rom:
        from uefi_firmware.efi_compressor import EfiDecompress

        rom = EfiDecompress(stream, len(stream))
        if len(rom) != original:
            raise ValueError(f"decompressed length {len(rom):#x} != declared {original:#x}")
        args.rom.parent.mkdir(parents=True, exist_ok=True)
        args.rom.write_bytes(rom)
        print(f"ROM output size={len(rom):#x} sha256={sha256(rom)}")


if __name__ == "__main__":
    main()
