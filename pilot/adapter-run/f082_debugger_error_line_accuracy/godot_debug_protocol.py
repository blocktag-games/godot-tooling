"""BP11: minimal decoder for Godot's remote debug protocol (the same
TCP wire protocol the Godot Editor's own Debugger panel and VS Code's
`godot-tools` extension speak to a running `--remote-debug`-enabled
process). Reverse-engineered directly against the pinned Godot 4.7.1
binary for this project -- no third-party debugger-client library was
available to reuse, and none is a project dependency.

Each debug-protocol packet is a length-prefixed Godot Variant (the same
binary encoding Godot uses for `bytes_to_var`/`var_to_bytes`), almost
always an Array whose first element is the message name (a String) and
second element is another Array of that message's own arguments --
e.g. `["error", ["res://subject.gd", "run", 4, "message text", ...]]`.

Only the Variant types actually observed on the wire during this
project's BP11 captures are implemented: NIL, BOOL, INT, FLOAT, STRING,
DICTIONARY, ARRAY, and the five numeric/string PACKED_*_ARRAY types.
Anything else raises ValueError rather than silently misparsing --
safer for a reverse-engineered decoder with no official spec to check
against.

Confirmed message names relevant to BP11:
- "set_pid": sent once, right after connection.
- "output": a captured stdout/stderr line (used elsewhere in this
  project's harness; not needed for this fixture).
- "debug_enter": sent when the engine pauses for the debugger (either
  an explicit breakpoint hit -- not reproduced by this fixture, see its
  README -- or, as used here, the built-in "pause on unhandled error"
  behavior, which fires automatically with no debugger-side
  configuration required).
- "error": a structured error/warning report. Observed field order
  for a genuine runtime error (not a reload-time parser warning):
  [hour, minute, second, msec, source_file, source_function,
   source_line, error_message, error_description, is_warning,
   stack_frame_count, then (file, function, line) repeated per frame].
  `source_line` (and every stack frame's own line) is exactly the
  field F057/F082 compare between instrumented and uninstrumented
  runs.
"""
from __future__ import annotations

import struct


def decode_variant(buf: bytes, off: int):
    type_tag = struct.unpack_from('<I', buf, off)[0]
    off += 4
    base_type = type_tag & 0xFF
    flags = type_tag >> 16
    if base_type == 0:  # NIL
        return None, off
    if base_type == 1:  # BOOL
        v = struct.unpack_from('<I', buf, off)[0]
        return bool(v), off + 4
    if base_type == 2:  # INT
        if flags & 1:
            v = struct.unpack_from('<q', buf, off)[0]
            return v, off + 8
        v = struct.unpack_from('<i', buf, off)[0]
        return v, off + 4
    if base_type == 3:  # FLOAT
        if flags & 1:
            v = struct.unpack_from('<d', buf, off)[0]
            return v, off + 8
        v = struct.unpack_from('<f', buf, off)[0]
        return v, off + 4
    if base_type == 4:  # STRING
        length = struct.unpack_from('<I', buf, off)[0]
        off += 4
        s = buf[off:off + length].split(b'\x00')[0].decode('utf-8', errors='replace')
        off += length + (4 - (length % 4)) % 4
        return s, off
    if base_type == 27:  # DICTIONARY
        count = struct.unpack_from('<I', buf, off)[0] & 0x7FFFFFFF
        off += 4
        d = {}
        for _ in range(count):
            k, off = decode_variant(buf, off)
            v, off = decode_variant(buf, off)
            d[k] = v
        return d, off
    if base_type == 28:  # ARRAY
        count = struct.unpack_from('<I', buf, off)[0] & 0x7FFFFFFF
        off += 4
        arr = []
        for _ in range(count):
            v, off = decode_variant(buf, off)
            arr.append(v)
        return arr, off
    if base_type == 29:  # PACKED_BYTE_ARRAY
        count = struct.unpack_from('<I', buf, off)[0]
        off += 4
        arr = list(buf[off:off + count])
        off += count + (4 - (count % 4)) % 4
        return arr, off
    if base_type == 30:  # PACKED_INT32_ARRAY
        count = struct.unpack_from('<I', buf, off)[0]
        off += 4
        arr = list(struct.unpack_from(f'<{count}i', buf, off))
        return arr, off + count * 4
    if base_type == 31:  # PACKED_INT64_ARRAY
        count = struct.unpack_from('<I', buf, off)[0]
        off += 4
        arr = list(struct.unpack_from(f'<{count}q', buf, off))
        return arr, off + count * 8
    if base_type == 32:  # PACKED_FLOAT32_ARRAY
        count = struct.unpack_from('<I', buf, off)[0]
        off += 4
        arr = list(struct.unpack_from(f'<{count}f', buf, off))
        return arr, off + count * 4
    if base_type == 33:  # PACKED_FLOAT64_ARRAY
        count = struct.unpack_from('<I', buf, off)[0]
        off += 4
        arr = list(struct.unpack_from(f'<{count}d', buf, off))
        return arr, off + count * 8
    if base_type == 34:  # PACKED_STRING_ARRAY
        count = struct.unpack_from('<I', buf, off)[0]
        off += 4
        arr = []
        for _ in range(count):
            length = struct.unpack_from('<I', buf, off)[0]
            off += 4
            s = buf[off:off + length].split(b'\x00')[0].decode('utf-8', errors='replace')
            off += length + (4 - (length % 4)) % 4
            arr.append(s)
        return arr, off
    raise ValueError(f"unhandled Variant type tag {base_type} at offset {off - 4}")


def parse_packets(data: bytes) -> list:
    off = 0
    packets = []
    while off < len(data):
        plen = struct.unpack_from('<I', data, off)[0]
        off += 4
        packet_end = off + plen
        val, _ = decode_variant(data, off)
        packets.append(val)
        off = packet_end
    return packets


def capture_session(port: int, listen_seconds: float) -> bytes:
    """Listens on 127.0.0.1:`port`, accepts exactly one connection (the
    Godot process under test), and returns every byte received within
    `listen_seconds` of the connection completing. Caller starts this
    (in a thread or subprocess) BEFORE launching Godot with
    `--remote-debug tcp://127.0.0.1:<port>`."""
    import socket
    import time

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', port))
    s.listen(1)
    conn, _ = s.accept()
    chunks = []
    start = time.time()
    while time.time() - start < listen_seconds:
        conn.settimeout(1)
        try:
            data = conn.recv(65536)
            if not data:
                break
            chunks.append(data)
        except socket.timeout:
            pass
    return b"".join(chunks)
