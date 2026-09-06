# Profiling an actual Godot application

Research and procedure guide, 6 September 2026, targeting Godot 4.7/4.7.1. **Both external measurement and Godot-specific profiling are useful.** Start with a repeatable application scenario and an external baseline, then choose the profiler that can explain the suspected bottleneck. Re-run the scenario without profiling to verify any improvement.

This guide belongs to godot-tooling. It does not run, alter, or depend on topdown-lab. No application capture was performed for this revision. The [local probe](../research/2026-09-06-profiling-environment-probe.json) records command availability, the engine executable hash, and a help/version check; it is not compatibility or performance validation. See also the [tooling-methods survey](../research/2026-09-06-benchmarking-methods-survey.md) and [observer-effect protocol](../benchmarks/profiling-protocol.md).

## Choose the question before the tool

| Question | Start with | What the result means |
| --- | --- | --- |
| How long does the scenario take, and what resources does it use? | External process timing and OS counters. | Complete elapsed/CPU time and scoped memory/I/O; limited explanation of individual game functions. |
| Which GDScript functions are expensive? | Godot Debugger → Profiler. | Script-function and engine frame activity, with self/inclusive views. |
| Is rendering expensive on the CPU or GPU? | Godot Visual Profiler, then a graphics capture if needed. | Rendering-stage costs; its CPU view is not the entire game's CPU time. |
| Which native engine/extension functions are expensive? | Linux perf/Hotspot; Windows sampling tools; macOS Instruments. | Native sampled stacks, substantially improved by matching symbols. |
| Where does a frame hitch happen across threads/phases? | A trace with named events, such as Tracy or Godot's documented Android Perfetto integration. | A timeline of recorded events, rather than only aggregate hotspot percentages. |
| Why is memory growing? | OS memory timeline plus Godot object/resource monitors, then an allocation profiler. | Distinguishes resident memory, engine objects, resource retention, and allocation sites. |
| Is loading blocked by storage or system calls? | pidstat and a separate syscall trace on Linux; OS tracing equivalents elsewhere. | I/O and scheduling clues; trace overhead must be measured separately. |

An external tool can profile a closed executable at the process level, but useful function attribution depends on symbols and runtime visibility. A native sample in the GDScript VM is not automatically a particular GDScript source function. Conversely, a script profile does not explain every native, GPU, driver, or storage cost. Godot distinguishes sampling from event tracing in its [native profiling guide](https://docs.godotengine.org/en/4.7/engine_details/development/profiling/index.html).

## Define a reproducible scenario

Choose a specific operation: launch to a ready screen, load a named level, run a fixed simulation/input replay, navigate a UI sequence, or repeat a gameplay action. Record project/assets revision, save state, seeds, input sequence, useful work completed, warmup and measurement boundaries, and an observable expected result.

Use a disposable project copy and isolated test user data. The same initial state must be available for each run. Preparation/import, first launch, prepared launch, and an already-running session are separate cases. A developer playing differently each time can still obtain useful diagnostic clues, but that is weaker comparative evidence than an automated replay.

Record engine hash/build, export template, renderer, GPU/driver, resolution, VSync/frame cap, physics tick rate, audio, debugger attachment, power state, and machine/session identity. A release export is the main production-performance reference; an editor/debug run is useful for diagnosis and constitutes its own comparison stratum. Keep the editor process separate from the game process in resource records.

Do not use headless mode for a rendering claim. Do not treat movie recording or fixed simulated FPS as natural frame pacing. Do not infer wall seconds from `--quit-after`: the checked engine help describes iterations. A capped run is a convenient smoke capture, not a specified gameplay workload.

## 1. Establish an external baseline on Linux

The following are **command recipes**, not completed experiments. Replace the paths and use a new output directory for each attempt. The target project and its scenario must already work. Do not assume tools shown below are installed merely because the recipe uses them.

```sh
GODOT_PROFILE_ENGINE="/absolute/path/to/godot"
GODOT_PROFILE_PROJECT="/absolute/path/to/disposable-project-copy"
GODOT_PROFILE_OUT="$HOME/code/godot-tooling/artifacts/profiles/example-run"
mkdir -p "$GODOT_PROFILE_OUT"

"$GODOT_PROFILE_ENGINE" --version
"$GODOT_PROFILE_ENGINE" --help
```

For a prepared-project run, perform import/setup first and keep its duration separate:

```sh
"$GODOT_PROFILE_ENGINE" --headless --path "$GODOT_PROFILE_PROJECT" --import
```

Capture a bounded application process with GNU time:

```sh
/usr/bin/time -v -o "$GODOT_PROFILE_OUT/resources.txt" \
  "$GODOT_PROFILE_ENGINE" --path "$GODOT_PROFILE_PROJECT" --quit-after 600
```

This example includes process startup, the chosen iterations, and shutdown. Replace the iteration cap with the application's deterministic completion mechanism for a real benchmark. For an exported game, run its actual executable instead of assuming the editor binary or `--path` reproduces deployment.

GNU time supplies command elapsed time and resource-use statistics. Preserve its exit status and output alongside application logs. Its maximum resident-set-size field is not a simultaneous sum of every process in a complex tool workflow. Use the process-tree metric defined in the [performance protocol](../benchmarks/performance-protocol.md) when multiple processes matter. [GNU time](https://www.gnu.org/software/time/)

For a longer-running game, obtain its actual PID and capture a resource timeline from another terminal:

```sh
GODOT_PROFILE_PID="12345"  # Replace with the game PID.
pidstat -h -u -r -d -p "$GODOT_PROFILE_PID" 1 30 \
  > "$GODOT_PROFILE_OUT/pidstat.txt"
```

This samples the selected process at one-second intervals; it can miss brief spikes and does not automatically include an unrelated editor or every child process. CPU percentage, resident memory, and disk I/O answer different questions. [pidstat manual](https://man7.org/linux/man-pages/man1/pidstat.1.html)

When available, a separate perf-stat pass adds execution counters:

```sh
perf stat -e task-clock,context-switches,page-faults \
  -o "$GODOT_PROFILE_OUT/perf-stat.txt" -- \
  "$GODOT_PROFILE_ENGINE" --path "$GODOT_PROFILE_PROJECT" --quit-after 600
```

Record unavailable events and access failures; they are not zero counts. Counter passes also introduce measurement work and should have an unmeasured control. Do not change system-wide perf settings automatically. [Perf tutorial](https://perfwiki.github.io/main/tutorial/), [Kernel perf access](https://www.kernel.org/doc/html/latest/admin-guide/perf-security.html)

## 2. Find GDScript hotspots with Godot

Run the project from the Godot editor, open Debugger → Profiler, and start recording around the chosen scenario. Use Autostart when investigating startup, then verify that the capture includes the event of interest. Inspect both frame activity and script functions. Compare self time with inclusive time so nested calls are not repeatedly counted as separate total costs. Record the capture interval and relevant settings. Profiling is disabled by default because it is costly; the built-in script profiler does not currently cover C# scripts. [Godot profiler](https://docs.godotengine.org/en/4.7/tutorials/scripting/debug/the_profiler.html)

Use a short initial capture to identify a candidate bottleneck, then rerun that exact scenario after a change. A large percentage in a call tree identifies where recorded time went; it does not alone establish that total application time improved. Retain absolute times and unchanged useful work.

For manual external launch, Godot provides `--remote-debug` and `--profiling`. A receiving debugger must be configured appropriately and the capture must be inspected. The debugger connection is distinct from the IDE's DAP endpoint. The flag is not a promise of a standalone machine-readable script-profile file. Use the editor workflow first; building an automated script-profile exporter would require an additional verified capture/integration path. [Command-line reference](https://docs.godotengine.org/en/4.7/tutorials/editor/command_line_tutorial.html)

PyCharm can remain the editing environment while Godot or an external profiler performs capture. PyCharm's Python profiler does not automatically profile GDScript. DAP debugging and coverage navigation remain separate integration capabilities to verify.

## 3. Separate script/physics work from rendering

The Visual Profiler reports rendering work on the CPU and GPU. Its CPU measurements exclude other work such as scripting and physics. Run the same scenario at a fixed viewport size and record the rendering method. The Godot 4.7 documentation describes support across rendering methods, with a macOS Compatibility-renderer exception. Preserve the selected frame/range and category breakdown; do not add overlapping CPU and GPU spans into a fabricated frame total. [Visual Profiler documentation](https://docs.godotengine.org/en/4.7/tutorials/scripting/debug/debugger_panel.html#visual-profiler)

The locally checked help also exposes `--gpu-profile` for a textual GPU-task profile. Treat that as a separate diagnostic run, validate what the renderer actually emits, and save the output. The presence of a help flag does not prove a particular driver's support or precision. `--gpu-validation` enables graphics API checks and should not be included in ordinary performance baselines. These help observations are recorded in the [probe](../research/2026-09-06-profiling-environment-probe.json).

A graphics frame capture can help investigate draw calls, resources, and shader behavior after the Visual Profiler points to rendering. Godot documents RenderDoc-related shader debug information and a limitation for local RenderingDevices. Verify the exact graphics API, device path, and capture workflow before relying on it; a single instrumented frame does not establish natural frame pacing. [Godot command-line reference](https://docs.godotengine.org/en/4.7/tutorials/editor/command_line_tutorial.html), [Compute-shader capture limitation](https://docs.godotengine.org/en/stable/tutorials/shaders/compute_shaders.html)

## 4. Obtain native CPU stacks

On Linux, perf can record sampled native stacks and Hotspot can visualize them. Use a production-like Godot/extension build with matching debugging symbols. Godot's documentation recommends production optimization with symbols for this purpose. If profiling requires a different binary, benchmark that binary against its own unprofiled control and label the difference from the shipped build. [Native build guidance](https://docs.godotengine.org/en/4.7/engine_details/development/profiling/index.html)

After the required tool and symbols are available:

```sh
perf record -F 99 --call-graph dwarf \
  -o "$GODOT_PROFILE_OUT/perf.data" -- \
  "$GODOT_PROFILE_ENGINE" --path "$GODOT_PROFILE_PROJECT" --quit-after 600

perf report -i "$GODOT_PROFILE_OUT/perf.data"
```

The requested sampling rate is a starting point, not a universal accuracy setting. Inspect achieved capture quality, dropped samples, unwind failures, unresolved symbols, and thread/process inclusion. A sampled native stack can identify physics, rendering submission, resource loading, GDExtension, allocation, or VM costs. Use script profiling or suitable script events to attribute VM work to application functions. [Perf tutorial](https://perfwiki.github.io/main/tutorial/)

Hotspot can launch the game or attach to an already-running process. Attachment can avoid startup when the question concerns steady gameplay. Its thread views and flame graph offer complementary ways to inspect the same capture. [Godot Hotspot workflow](https://docs.godotengine.org/en/4.7/engine_details/development/profiling/hotspot.html)

CPU sampling shows recorded on-CPU activity. A frame stalled on storage, synchronization, VSync, or GPU completion may require scheduler, I/O, or GPU evidence. Do not interpret a small CPU hotspot as proof that a wall-time delay did not occur.

## 5. Investigate memory and I/O

Use OS resident-memory trends together with Godot object, node, resource, and rendering monitors. Some engine metrics are debug-only; an unavailable release metric must not become a measured zero. Godot's static-memory counter, OS RSS, GPU allocation, and retained application objects are different quantities. [Godot Performance API](https://docs.godotengine.org/en/4.7/classes/class_performance.html)

First define the expected lifecycle: load and unload a scene repeatedly, create and free resources, or perform a fixed allocation batch. Measure checkpoints after an explicit settling interval. Allocator caching and delayed freeing can produce resident-memory plateaus without proving a leak. Confirm unintended retained work or an allocation path before labeling it a defect.

For native allocation attribution, heaptrack records allocation events with stack traces; Valgrind Massif can analyze heap evolution in a separate diagnostic environment. Both change the execution being observed. Engine/custom allocators and missing symbols can limit useful attribution. Keep allocation captures out of ordinary speed measurements. [heaptrack](https://github.com/KDE/heaptrack), [Massif manual](https://valgrind.org/docs/manual/ms-manual.html)

A short Linux syscall summary can investigate repeated file opens, reads, or synchronization:

```sh
strace -f -c -o "$GODOT_PROFILE_OUT/strace-summary.txt" -- \
  "$GODOT_PROFILE_ENGINE" --path "$GODOT_PROFILE_PROJECT" --quit-after 600
```

This is a diagnostic trace, not a substitute for an untraced elapsed measurement. Keep its process scope and capture interval explicit. For a detailed timeline, use a separately bounded trace with timestamps and retain only the necessary scope. [strace project and documentation](https://strace.io/)

## 6. Add application-level context when black-box data is insufficient

For a scenario you control, add sparse named markers around meaningful work, such as level load, pathfinding batch, enemy update, or save serialization. Use `Time.get_ticks_usec()` differences within the same process and retain a declared count of completed work. Buffer records and write outside the measured region where possible. Cross-thread/process timelines require synchronized clock domains; unrelated relative timestamps cannot be directly subtracted. [Godot Time API](https://docs.godotengine.org/en/4.7/classes/class_time.html)

Custom monitors can expose counters such as active enemies, pending jobs, loaded chunks, or a rolling subsystem duration. Pair timing with useful-work counts: a faster enemy update may simply have processed fewer enemies. Register/read monitors using the supported Performance API and verify update frequency and build availability. Polling a monitor is not automatically a per-frame raw event stream. [Godot Performance API](https://docs.godotengine.org/en/4.7/classes/class_performance.html)

For asynchronous work, distinguish elapsed latency from CPU-active segments. A marker spanning an `await` measures the suspension as well as resumed work; it is not the CPU cost of that function. For frame pacing, retain monotonic frame-arrival intervals separately from simulation delta, which can be clamped, smoothed, or fixed. Freeze percentile definitions and required frame counts before reporting tails.

This instrumentation creates another observer. Retain an uninstrumented variant and measure sparse-marker overhead before promoting its numbers to benchmark evidence.

## 7. Use tracing for hitches and cross-thread behavior

Tracy is an option when aggregate samples cannot explain event order or overlap. Godot's documented workflow requires a Tracy-enabled engine/template build, compatible capture tooling, and explicit connection behavior. Record compiler/options, symbols, Tracy revision, enabled zones, capture state, losses, and trace size. Compare inactive/active capture on the same binary. A trace can show only the events actually recorded. [Godot Tracy workflow](https://docs.godotengine.org/en/4.7/engine_details/development/profiling/tracy.html)

Godot 4.7 documents official **Android Perfetto templates**. Its workflow selects a matching template, configures tracked categories, records on the Android device, and inspects the resulting trace. The `godot` category records engine events; `godot_scripting` records script activity and is explicitly described as substantially more expensive. Treat them as separate capture conditions. This is a documented Android path, not a verified desktop-Python exporter or a capture performed here. [Godot Perfetto workflow](https://docs.godotengine.org/en/4.7/engine_details/development/profiling/perfetto.html)

This gives us a concrete observer-effect experiment: engine events alone versus engine-plus-script events, on the same template, scenario, and device. Preserve unprofiled and matched capture controls rather than assuming trace overhead is negligible.

## Platform paths

| Platform | Initial external path | Deeper path and boundary |
| --- | --- | --- |
| Linux | GNU time/pidstat; perf when available. | Hotspot, allocation tracing, syscall analysis, and a matched Tracy build. |
| Windows | OS resource recording; WPR capture analyzed in WPA. | CPU scheduling/I/O analysis; Godot also documents a VerySleepy sampling workflow. Validate exact installation and symbols. |
| macOS | Instruments CPU/resource capture on the named machine. | Sampling/trace configurations and Godot rendering support must be recorded separately. |
| Android, later stage | Named device and reproducible exported scenario. | Godot's documented Perfetto templates and explicitly chosen event categories. |

WPR records ETW events for WPA analysis; Instruments supplies CPU profile call-tree views. Platform tools are optional diagnostic integrations, not mandatory dependencies of the open benchmark core. Public source availability for our harness does not make every platform SDK or commercial IDE open source. [Microsoft WPR](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/windows-performance-recorder), [Apple Instruments](https://developer.apple.com/documentation/xcode/analyzing-cpu-profiles-with-call-tree-views), [Godot profiler index](https://docs.godotengine.org/en/4.7/engine_details/development/profiling/index.html)

## Avoid misleading automation shortcuts

The available engine lists `--benchmark` and `--benchmark-file` as editor-build tools. Inspection of Godot 4.7.1's native source shows named engine timing marks and JSON dumping, including startup/shutdown marks. These are useful for engine setup questions; they are not automatic coverage, arbitrary GDScript function profiles, or a complete gameplay timeline. Inspect the resulting keys and units before interpreting a file. [Engine mark storage](https://github.com/godotengine/godot/blob/4.7.1-stable/core/os/os.cpp), [Startup/shutdown call sites](https://github.com/godotengine/godot/blob/4.7.1-stable/main/main.cpp)

Unknown or build-inapplicable flags may be ignored, so validate the actual capture output as well as checking `--help`. A process exiting successfully does not prove profiling occurred. A profiler attached to an IDE or Python launcher may have missed the child game. Logging every line/frame can itself dominate a short task. These are explicit validity checks for our future adapters, not claims of defects in the engine.

## First practical execution plan

1. Select a small standalone Godot application scenario and validate its behavior without instrumentation.
2. Record the executable, project, environment, renderer, scenario, and output identities; establish external elapsed/resource observations.
3. Capture the same scenario with the Godot script profiler. Use the Visual Profiler if rendering is implicated.
4. Add native, allocation, or OS tracing only for a specific unresolved question.
5. Make one targeted change, rerun the unprofiled scenario, and retain both the effect and uncertainty.
6. Run the [observer experiment](../benchmarks/profiling-protocol.md) on selected scenarios before comparing profiler-derived measurements as if they were neutral.

Archive native captures, settings, losses/unavailable metrics, source/binary hashes, behavior checks, and an exported view suitable for readers. Link them to the corresponding unprofiled run. Screenshots illustrate a finding; raw observations and reproduction steps support it.
