# F082: debugger-protocol error-line accuracy under instrumentation

Run: `python3 check.py`

See `../../fixtures/oracles/F082.json` for the full finding. Short version:
Godot's own remote debug protocol (what the Editor's Debugger panel and VS
Code's `godot-tools` extension both consume) reports the same WRONG,
instrumentation-shifted line F057 already found in raw stderr text -- for
both gd-tools and Nano Coverage, not just gd-tools.

## What this fixture does NOT establish: breakpoint binding

BP11's original open question (see F057.json's notes) was whether a
debugger's own breakpoint-binding logic -- setting a breakpoint via `-b
file::line` or an Editor gutter click, then confirming execution actually
pauses at the intended original-source statement -- is confused by the
same line shift, or immune to it via some other mechanism.

This fixture does not answer that. Attempts made, in order:

1. `-b res://subject/subject.gd::4` with `--remote-debug tcp://127.0.0.1:PORT`
   pointed at a minimal Python socket listener (accept + recv only, no
   protocol-level replies sent back). Result: the process ran to completion
   in well under a second, no `debug_enter` packet, no pause -- the
   breakpoint did not activate.
2. Same, with an absolute filesystem path instead of `res://`. Same result.
3. Longer capture window (8s) to rule out a timing race between the debug
   connection completing and the breakpoint line executing. Same result.

By contrast, the automatic "pause on unhandled error" behavior this
fixture DOES use fired reliably on the first attempt, every time, with
zero configuration -- confirming the receive-only listener itself works
correctly as a debug-protocol client for at least that message class.

**Conclusion:** Godot's real breakpoint-binding path requires the debugger
peer to do something beyond connecting and listening -- almost certainly
sending its own protocol message(s) back (the "set_pid" message Godot
sends first suggests a real handshake exists; a real debugger likely also
sends breakpoint-list/configuration messages of its own, which this
project's registered command-line `-b` flag alone does not substitute
for). Reverse-engineering that full two-way handshake, or standing up a
real Godot Editor GUI session (blocked in this environment: no
`xdotool`/`scrot`/`import` installed, would need sudo not available this
session, and the only X display present is the user's own live desktop --
not something to launch automated GUI tests against without asking first),
were both judged disproportionate scope for this verification pass.

This is a genuine, unresolved gap, not paperwork -- BP13's published
limitations section should say so plainly.
