"""The stand-in Driver of the Root Contract's conformance suite (RCT-4, "The stand-in Driver").

One program for every Trunk. The suite puts it first on the Trunk's search path under the names
`arbol-claude-driver` and `arbol-codex-driver`, through two small launchers that name it in RCT_STANDIN_AS. It takes a
Driver's command line (DRV-0, DRV-2): an optional `-v <build>` first, then `run` with `--request <file>`, `--control`
and the other options of DRV-2, `runs stop <run>`, or `info`, which names contract 1.

A run plays the script of the scenario named in `<home>/standin/scenario`, such as "R8 tool", and writes its events
as a Driver does. It stops as a Driver does, on a `stop` line, when its control input ends, on SIGTERM or SIGINT, and
on `runs stop`: open questions close as withdrawn, running tool calls finish as interrupted, the children
it started in process groups of their own are ended, and `finished` says `cancelled`. Every start, whatever its
command, appends one `StandInRecord` to `<home>/standin/received.jsonl` when it ends: its arguments, the request as it
read it, every line of its control input, every line it wrote on its standard output, and every signal it got. A run with `"tools": "none"` and no chat session,
such as a title, gets one `text` event, "Stand-in title", and completes, unless the scenario's script for it says
otherwise.

It uses the standard library only, as the suite does.
"""

from __future__ import annotations

import json
import os
import select
import signal
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

CONTRACT = 1
VERSION = "1.0.0"
TOOL_VERSION = "stand-in 1"
STOP_GRACE_SECONDS = 2.0  # DRV-2.16: the tool is ended after 2 seconds of a stop
RUNS_STOP_SECONDS = 15.0  # DRV-2.16: the whole stop takes at most 15 seconds

OPTIONS_WITH_VALUE = {"--request", "--subscription", "--model", "--effort", "--service-tier", "--system-prompt-file",
                      "--cwd", "--add-dir", "--tools", "--chat-session", "--run-id", "--label", "--output"}
FLAGS = {"--control"}


def now() -> str:
    """A time in the form JavaScript's toISOString writes, such as 2026-10-15T09:30:00.412Z."""
    moment = datetime.now(UTC)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


def scale() -> float:
    """ARBOL_TEST_TIME_SCALE: the Driver's own waits are divided by it (DRV-5, RCT-4)."""
    try:
        value = float(os.environ.get("ARBOL_TEST_TIME_SCALE", "1"))
    except ValueError:
        return 1.0
    return value if value > 0 else 1.0


class Stopped(Exception):
    """The run was told to stop: by a stop line, the end of its control input, a signal or `runs stop`."""


class Broken(Exception):
    """Standard output can no longer take an event: the run stops and writes nothing more."""


class StandIn:
    """One start of the stand-in: what it was given, and what it has received so far."""

    def __init__(self, argv: list[str]) -> None:
        self.arguments = argv
        self.launcher = os.environ.get("RCT_STANDIN_AS", os.path.basename(sys.argv[0]))
        self.home = Path.home()
        self.folder = self.home / "standin"
        name = self._read_scenario()
        self.scenario, _, self.part = name.partition(" ")
        self.request: Any = None
        self.control: list[Any] = []
        self.events: list[str] = []  # every line it wrote on its standard output, without the newline (RCT-D33)
        self.signals: list[str] = []

    def _read_scenario(self) -> str:
        try:
            return (self.folder / "scenario").read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    def record(self) -> None:
        """Appends this start's StandInRecord to received.jsonl, as one whole line."""
        record = {"scenario": self.scenario, "part": self.part, "launcher": self.launcher,
                  "arguments": self.arguments, "request": self.request, "control": self.control,
                  "events": self.events, "signals": self.signals, "workingDirectory": os.getcwd()}
        self.folder.mkdir(parents=True, exist_ok=True)
        line = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8", "surrogatepass")
        descriptor = os.open(self.folder / "received.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(descriptor, line)
        finally:
            os.close(descriptor)


def refuse(code: str, message: str) -> NoReturn:
    print(json.dumps({"error": {"code": code, "message": message}}))
    raise SystemExit(1)


# The run ------------------------------------------------------------------------------------------------------------


class Run:
    """A run in progress: its event stream, its control input, its open calls and questions, its children."""

    def __init__(self, standin: StandIn, request: dict[str, Any], control: bool) -> None:
        self.standin = standin
        self.request = request
        self.run_id = str(request.get("runId") or f"standin-{uuid.uuid4()}")
        self.labels = request.get("labels")
        self.seq = 0
        self.scale = scale()
        self.control_open = control
        self.buffer = b""
        self.stopping = False
        self.broken = False
        self.open_calls: list[str] = []
        self.open_asks: dict[str, str] = {}  # askId to the callId of its tool call
        self.answers: dict[str, Any] = {}
        self.children: list[subprocess.Popen[bytes]] = []
        self.produced = False
        self.usage_so_far: dict[str, Any] = {}
        self.wake_read, self.wake_write = os.pipe()
        os.set_blocking(self.wake_write, False)
        self.record_file = standin.folder / "runs" / f"{self.run_id}.json"

    # The record of a run in progress, so that `runs stop` finds it (DRV-2.27).

    def register(self) -> None:
        self.record_file.parent.mkdir(parents=True, exist_ok=True)
        self.record_file.write_text(json.dumps({"runId": self.run_id, "pid": os.getpid()}), encoding="utf-8")

    def unregister(self) -> None:
        self.record_file.unlink(missing_ok=True)

    # Signals and the control input.

    def on_signal(self, number: int, _frame: object) -> None:
        self.standin.signals.append(signal.Signals(number).name)
        self.stopping = True
        try:
            os.write(self.wake_write, b"!")
        except OSError:
            pass

    def _take_control(self, data: bytes) -> None:
        self.buffer += data
        while b"\n" in self.buffer:
            raw, self.buffer = self.buffer.split(b"\n", 1)
            text = raw.decode("utf-8", "replace")
            try:
                line: Any = json.loads(text)
            except ValueError:
                line = text
            self.standin.control.append(line)
            self._handle(line)

    def _handle(self, line: Any) -> None:
        if isinstance(line, dict) and line.get("type") == "stop":
            self.stopping = True
            return
        if isinstance(line, dict) and line.get("type") == "answer" and isinstance(line.get("askId"), str):
            if line["askId"] in self.open_asks:
                self.answers[line["askId"]] = line.get("answer")
                return
            self.event("control_refused", error={"code": "not_found", "message": "No such open question."},
                       askId=line["askId"], check=False)
            return
        self.event("control_refused", error={"code": "invalid_input", "message": "Unknown control line."},
                   check=False)

    def poll(self, timeout: float = 0.0) -> None:
        """Takes what arrived on the control input and from signals, waiting at most `timeout` seconds."""
        readers = [self.wake_read] + ([0] if self.control_open else [])
        ready, _, _ = select.select(readers, [], [], max(timeout, 0.0))
        if self.wake_read in ready:
            os.read(self.wake_read, 1024)
        if 0 in ready:
            data = os.read(0, 65536)
            if data:
                self._take_control(data)
            else:  # the control input ended: the caller has gone (DRV-2.26)
                self.control_open = False
                self.stopping = True

    def check(self) -> None:
        self.poll()
        if self.stopping:
            raise Stopped()

    # Events.

    def event(self, kind: str, *, check: bool = True, **fields: Any) -> None:
        if check:
            self.check()
        if self.broken:
            raise Broken()
        self.seq += 1
        event: dict[str, Any] = {"runId": self.run_id, "seq": self.seq, "at": now()}
        if self.labels:
            event["labels"] = self.labels
        event["type"] = kind
        event.update(fields)
        line = json.dumps(event, ensure_ascii=False)
        try:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
            self.standin.events.append(line)
        except (BrokenPipeError, OSError):
            self.broken = True
            raise Broken() from None

    # What a script does.

    def started(self) -> None:
        history = self.request.get("history") or []
        fields: dict[str, Any] = {"continuity": "rebuilt" if history else "fresh"}
        if history:
            fields["rebuildReason"] = "first_run" if self.request.get("chatSessionId") else "no_chat_session"
        fields["subscriptionId"] = self.request.get("subscriptionId") or "standin"
        for name in ("model", "effort"):
            if self.request.get(name):
                fields[name] = self.request[name]
        build = self.standin.arguments[1] if self.standin.arguments[:1] == ["-v"] else "0"
        self.event("started", **fields, toolVersion=TOOL_VERSION, driverBuild=build)

    def text(self, text: str, *, deltas: tuple[str, ...] = ()) -> None:
        for piece in deltas:
            self.event("text_delta", text=piece)
        self.event("text", text=text)
        self.produced = True

    def tool(self, name: str, tool_input: Any, *, result: Any = None, ok: bool = True, error: str | None = None,
             output: tuple[str, ...] = (), call_id: str | None = None, **extra: Any) -> str:
        call = call_id or f"call_{self.seq + 1}"
        self.event("tool_started", callId=call, name=name, input=tool_input)
        self.open_calls.append(call)
        for piece in output:
            self.event("tool_output_delta", callId=call, text=piece)
        self.finish_tool(call, ok=ok, result=result, error=error, **extra)
        return call

    def open_tool(self, name: str, tool_input: Any, *, call_id: str | None = None) -> str:
        call = call_id or f"call_{self.seq + 1}"
        self.event("tool_started", callId=call, name=name, input=tool_input)
        self.open_calls.append(call)
        return call

    def finish_tool(self, call: str, *, ok: bool = True, result: Any = None, error: str | None = None,
                    check: bool = True, **extra: Any) -> None:
        fields: dict[str, Any] = {"callId": call, "ok": ok}
        if result is not None:
            fields["result"] = result
        if error is not None:
            fields["error"] = error
        fields.update(extra)
        self.event("tool_finished", check=check, **fields)
        if call in self.open_calls:
            self.open_calls.remove(call)

    def shell(self, command: str, output: str, exit_code: int = 0) -> str:
        return self.tool("shell", {"command": command}, result={"output": output, "exitCode": exit_code},
                         ok=exit_code == 0, output=(output,) if output else ())

    def ask(self, questions: list[dict[str, Any]]) -> Any:
        """A question to the Leather Bag (DRV-3): waits for its answer on the control input and gives it."""
        call = self.open_tool("ask_user", {"questions": questions})
        ask_id = f"ask_{self.seq + 1}"
        self.event("ask_opened", askId=ask_id, ask={"callId": call, "questions": questions})
        self.open_asks[ask_id] = call
        while ask_id not in self.answers:
            self.poll(0.05)
            if self.stopping:
                raise Stopped()
        answer = self.answers.pop(ask_id)
        del self.open_asks[ask_id]
        self.event("ask_closed", askId=ask_id, reason="answered", check=False)
        if isinstance(answer, dict) and answer.get("type") == "decline":
            self.finish_tool(call, ok=False, error="The Leather Bag declined the question.", check=False)
            self.stopping = True
            raise Stopped()
        self.finish_tool(call, ok=True, result=answer, check=False)
        return answer

    def usage(self, **usage: Any) -> None:
        self.usage_so_far = {"model": self.request.get("model") or "standin", **usage}
        self.event("usage", usage=self.usage_so_far)

    def silence(self, seconds: float) -> None:
        """No event for `seconds`, divided by the time scale, while control lines and signals are still taken."""
        deadline = time.monotonic() + seconds / self.scale
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            self.poll(min(remaining, 0.05))
            if self.stopping:
                raise Stopped()

    def wait_for_stop(self) -> NoReturn:
        while True:
            self.silence(3600)

    def hold(self) -> None:
        """No event until the suite lets the run go on by writing `<home>/standin/release`, while control lines and
        signals are still taken."""
        release = self.standin.folder / "release"
        while not release.exists():
            self.poll(0.05)
            if self.stopping:
                raise Stopped()

    def child(self, seconds: float = 3600) -> int:
        """Starts a child in a process group of its own, as a Driver starts its vendor tool, and names it in
        `<home>/standin/children.jsonl` so that the suite can make sure it is gone."""
        process = subprocess.Popen(["/bin/sleep", str(int(seconds))], start_new_session=True,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.children.append(process)
        line = json.dumps({"pid": process.pid, "runId": self.run_id}) + "\n"
        self.standin.folder.mkdir(parents=True, exist_ok=True)
        with (self.standin.folder / "children.jsonl").open("a", encoding="utf-8") as children:
            children.write(line)
        return process.pid

    def end_children(self) -> None:
        """Ends the children's process groups: SIGTERM, and SIGKILL after the grace of a stop."""
        alive = [child for child in self.children if child.poll() is None]
        for child in alive:
            _signal_group(child.pid, signal.SIGTERM)
        deadline = time.monotonic() + STOP_GRACE_SECONDS / self.scale
        for child in alive:
            try:
                child.wait(max(deadline - time.monotonic(), 0))
            except subprocess.TimeoutExpired:
                _signal_group(child.pid, signal.SIGKILL)
                child.wait()
        for child in self.children:  # what else the child's group still holds
            _signal_group(child.pid, signal.SIGKILL)

    def finished(self, outcome: str, *, error: dict[str, Any] | None = None, check: bool = True) -> int:
        self.end_children()
        fields: dict[str, Any] = {"outcome": outcome}
        if error is not None:
            fields["error"] = error
        if self.usage_so_far:
            fields["usage"] = self.usage_so_far
        fields["producedOutput"] = self.produced
        fields["unfinishedCalls"] = list(self.open_calls)
        self.event("finished", check=check, **fields)
        return {"completed": 0, "failed": 1, "cancelled": 2}[outcome]

    def cancel(self) -> int:
        """Stops the run as a Driver does (DRV-2.16, 2.17)."""
        for ask_id in list(self.open_asks):
            self.event("ask_closed", askId=ask_id, reason="withdrawn", check=False)
            del self.open_asks[ask_id]
        self.end_children()
        for call in list(self.open_calls):
            self.finish_tool(call, ok=False, error="The run was stopped.", interrupted=True, check=False)
        return self.finished("cancelled", check=False)


def _signal_group(pid: int, number: int) -> None:
    try:
        os.killpg(pid, number)
    except (ProcessLookupError, PermissionError):
        pass


# Scripts ------------------------------------------------------------------------------------------------------------

Script = Callable[[Run], int]


def title(run: Run) -> int:
    """A small call with no tools and no chat session, such as a title (RCT-4)."""
    run.started()
    run.text("Stand-in title")
    run.usage(inputTokens=12, outputTokens=3)
    return run.finished("completed")


def selftest_plain(run: Run) -> int:
    """The suite's own test of the stand-in: text, a shell call, more text and usage, completed."""
    run.started()
    run.text("Let me read it.", deltas=("Let me ", "read it."))
    run.shell("cat build.sh", "#!/bin/sh\nset -e\n")
    run.text("It sets -e.")
    run.usage(inputTokens=100, outputTokens=20)
    return run.finished("completed")


def selftest_stop(run: Run) -> int:
    """Waits for ever with a tool call open, until the run is stopped."""
    run.started()
    run.open_tool("shell", {"command": "make"})
    run.wait_for_stop()


def selftest_child(run: Run) -> int:
    """Starts a child in a process group of its own and waits, with a tool call open, until the run is stopped."""
    run.started()
    run.open_tool("shell", {"command": "make"})
    run.child()
    run.wait_for_stop()


def selftest_ask(run: Run) -> int:
    """Asks a question, and completes once it has its answer."""
    run.started()
    answer = run.ask([{"id": "branch", "question": "Which branch?", "multiple": False,
                       "options": [{"label": "main"}, {"label": "dev"}]}])
    run.text(f"Answered: {json.dumps(answer)}")
    return run.finished("completed")


def selftest_hold(run: Run) -> int:
    """Holds the run open until the suite lets it go, then completes."""
    run.started()
    run.hold()
    run.text("Let go.")
    return run.finished("completed")


def selftest_fail(run: Run) -> int:
    """Fails with a rate limit and a time to wait."""
    run.started()
    run.usage(inputTokens=5)
    return run.finished("failed", error={"code": "rate_limited", "message": "Rate limited.", "retryable": True,
                                         "retryAfterSeconds": 1800})


def r1(run: Run) -> int:
    """R1: a plain answer. A pause first, in which the suite looks at the folder and the tables of the open Exchange;
    then text, a shell call, more text and usage, and the run completes."""
    run.started()
    run.silence(30)
    run.text("Let me read it.", deltas=("Let me ", "read it."))
    run.shell("cat build.sh", "#!/bin/sh\nset -e\nmake all\n")
    run.text("It compiles the three packages and copies them to dist/.")
    run.usage(inputTokens=5120, outputTokens=812)
    return run.finished("completed")


def r3_busy(run: Run) -> int:
    """R3 "busy": the run is held open, so that the chat has an open Exchange, until the suite lets it go."""
    run.started()
    run.hold()
    run.text("Done.")
    run.usage(inputTokens=40, outputTokens=2)
    return run.finished("completed")


def r2(run: Run) -> int:
    """R2: keep the folder available until its reader opens it, then end with the requested outcome."""
    run.started()
    run.hold()
    run.text("A foreground answer.")
    run.usage(inputTokens=40, outputTokens=4)
    outcome = run.standin.part if run.standin.part in ("failed", "cancelled") else "completed"
    error = {"code": "rate_limited", "message": "Rate limited.", "retryable": True} if outcome == "failed" else None
    return run.finished(outcome, error=error)


def r2_unread(run: Run) -> int:
    """R2: more output than an unread pipe can hold; the file and the database must still reach the end."""
    run.started()
    run.hold()
    for _ in range(512):
        run.text("x" * 4096)
    return run.finished("completed")


def r5(run: Run) -> int:
    """R5: a short answer that completes."""
    run.started()
    run.text("A short answer.")
    run.usage(inputTokens=40, outputTokens=4)
    return run.finished("completed")


def r5_fails(run: Run) -> int:
    """R5 "fails": the run fails with a rate limit."""
    run.started()
    run.usage(inputTokens=40)
    return run.finished("failed", error={"code": "rate_limited", "message": "Rate limited.", "retryable": True,
                                         "retryAfterSeconds": 60})


def r5_stopped(run: Run) -> int:
    """R5 "stopped": text, then nothing until the run is stopped."""
    run.started()
    run.text("Working on it.")
    run.wait_for_stop()


def r5_together(run: Run) -> int:
    """R5 "together": the run is held open, so that the chat's Exchange stays open, until the suite lets it go."""
    run.started()
    run.hold()
    run.text("Done.")
    return run.finished("completed")


def r8_text(run: Run) -> int:
    """R8 "text": text streams, a fragment every second (divided), until the run is stopped."""
    run.started()
    run.produced = True
    while True:
        run.event("text_delta", text="More of the answer. ")
        run.silence(1)


def r8_tool(run: Run) -> int:
    """R8 "tool": text, then a shell call that runs until the run is stopped."""
    run.started()
    run.text("Let me build it.")
    run.open_tool("shell", {"command": "make"})
    run.wait_for_stop()


BRANCH_QUESTION = [{"id": "branch", "question": "Which branch should I push to?", "multiple": False,
                    "options": [{"label": "main"}, {"label": "dev"}]}]


def r8_ask(run: Run) -> int:
    """R8 "ask": a question to the Leather Bag that stays open until the run is stopped."""
    run.started()
    run.ask(BRANCH_QUESTION)
    return run.finished("completed")


def r9(run: Run) -> int:
    """R9: a question to the Leather Bag; once it has its answer, the run goes on and completes."""
    run.started()
    answer = run.ask(BRANCH_QUESTION)
    run.text(f"Answered: {json.dumps(answer)}")
    run.usage(inputTokens=60, outputTokens=8)
    return run.finished("completed")


def r19(run: Run) -> int:
    """R19: the agent's run in every part, a short answer that completes."""
    run.started()
    run.text("A short answer.")
    run.usage(inputTokens=40, outputTokens=4)
    return run.finished("completed")


def r10(run: Run) -> int:
    run.started()
    run.text("Before the signal.")
    run.usage(inputTokens=40, outputTokens=4)
    run.child()
    run.open_tool("shell", {"command": "make"})
    run.wait_for_stop()


def r19_small_fails(run: Run) -> int:
    """R19 "fails": a small call, such as a title, that fails with a rate limit."""
    run.started()
    run.usage(inputTokens=12)
    return run.finished("failed", error={"code": "rate_limited", "message": "Rate limited.", "retryable": True,
                                         "retryAfterSeconds": 60})


# A script by the scenario and its part, such as "R8 tool", or by the scenario alone. "<scenario> small" (or
# "<scenario> <part> small") is the script of a run with no tools and no chat session; without one, `title`.
SCRIPTS: dict[str, Script] = {
    "selftest plain": selftest_plain,
    "selftest stop": selftest_stop,
    "selftest child": selftest_child,
    "selftest ask": selftest_ask,
    "selftest hold": selftest_hold,
    "selftest fail": selftest_fail,
    "R1": r1,
    "R2": r2,
    "R2 unread": r2_unread,
    "R2 interrupt": r8_tool,
    "R3 busy": r3_busy,
    "R4": r3_busy,
    "R5": r5,
    "R5 fails": r5_fails,
    "R5 stopped": r5_stopped,
    "R5 together": r5_together,
    "R8 text": r8_text,
    "R8 tool": r8_tool,
    "R8 ask": r8_ask,
    "R9": r9,
    "R10": r10,
    "R19": r19,
    "R19 fails small": r19_small_fails,
}


def script_for(standin: StandIn, request: dict[str, Any]) -> Script | None:
    name = f"{standin.scenario} {standin.part}".strip()
    if request.get("tools") == "none" and not request.get("chatSessionId"):
        return SCRIPTS.get(f"{name} small") or SCRIPTS.get(f"{standin.scenario} small") or title
    return SCRIPTS.get(name) or SCRIPTS.get(standin.scenario)


# Commands -----------------------------------------------------------------------------------------------------------


def parse_run(args: list[str]) -> tuple[dict[str, Any], bool, str | None]:
    """The options of `run` (DRV-2): the request, whether there is a control input, and the request file named."""
    options: dict[str, list[str]] = {}
    message: str | None = None
    control = False
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in FLAGS:
            control = True
        elif arg.split("=", 1)[0] in OPTIONS_WITH_VALUE:
            name, equals, value = arg.partition("=")
            if not equals:
                index += 1
                if index >= len(args):
                    raise ValueError(f"{name} needs a value.")
                value = args[index]
            options.setdefault(name, []).append(value)
        elif arg.startswith("--"):
            raise ValueError(f"Unknown option: {arg}")
        elif message is None and index == len(args) - 1:
            message = arg
        else:
            raise ValueError(f"Unexpected argument: {arg}")
        index += 1
    request: dict[str, Any] = {}
    file = options.get("--request", [None])[-1]
    if file == "-":
        request = json.loads(sys.stdin.buffer.readline())
    elif file is not None:
        request = json.loads(Path(file).read_text(encoding="utf-8"))
    if not isinstance(request, dict):
        raise ValueError("The request file holds no JSON object.")
    single = {"--subscription": "subscriptionId", "--model": "model", "--effort": "effort",
              "--service-tier": "serviceTier", "--cwd": "workingDirectory", "--tools": "tools",
              "--chat-session": "chatSessionId", "--run-id": "runId"}
    for option, field in single.items():
        if option in options:
            request[field] = options[option][-1]
    if "--add-dir" in options:
        request["additionalDirectories"] = options["--add-dir"]
    if "--label" in options:
        request["labels"] = dict(label.partition("=")[::2] for label in options["--label"])
    if "--system-prompt-file" in options:
        request["systemPrompt"] = Path(options["--system-prompt-file"][-1]).read_text(encoding="utf-8")
    if message is not None:
        request["input"] = {"role": "user", "text": message}
    if file is None and "--tools" not in options:
        request["tools"] = "none"  # DRV-2: with neither a request file nor --tools, tools are off
    return request, control, file


def command_run(standin: StandIn, args: list[str]) -> int:
    try:
        request, control, _file = parse_run(args)
    except (ValueError, OSError) as error:
        run = Run(standin, {}, False)
        return run.finished("failed", error={"code": "invalid_input", "message": str(error)}, check=False)
    standin.request = request
    run = Run(standin, request, control)
    for number in (signal.SIGTERM, signal.SIGINT):
        signal.signal(number, run.on_signal)
    run.register()
    try:
        script = script_for(standin, request)
        try:
            if script is None:
                run.started()
                name = f"{standin.scenario} {standin.part}".strip()
                return run.finished("failed", error={"code": "internal",
                                                     "message": f"The stand-in has no script for {name!r}."})
            return script(run)
        except Stopped:
            return run.cancel()
    except Broken:
        run.end_children()
        return 1
    finally:
        run.unregister()


def command_runs_stop(standin: StandIn, run_id: str) -> int:
    """Stops a run by its identifier from another invocation; an ended or unknown run is no error (DRV-2.18)."""
    file = standin.folder / "runs" / f"{run_id}.json"
    try:
        pid = int(json.loads(file.read_text(encoding="utf-8"))["pid"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0
    try:
        os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return 0
    deadline = time.monotonic() + RUNS_STOP_SECONDS / scale()
    while file.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    return 0


def command_info(standin: StandIn, build: str) -> int:
    driver = "codex" if "codex" in standin.launcher else "claude"
    info = {"driver": driver, "version": VERSION, "build": build, "contract": CONTRACT,
            "stateDirectory": str(standin.folder / "state"),
            "settingsFile": str(standin.home / ".arbol" / f"arbol-{driver}-driver.json"),
            "tool": {"name": "stand-in", "version": TOOL_VERSION, "supported": True, "oldestSupported": "1"}}
    print(json.dumps(info))
    return 0


def main(argv: list[str]) -> int:
    standin = StandIn(argv)
    try:
        args = list(argv)
        build = "0"
        if args[:1] == ["-v"]:
            if len(args) < 2:
                refuse("invalid_input", "-v needs a build number.")
            build = args[1]
            args = args[2:]
        if args[:1] == ["run"]:
            return command_run(standin, args[1:])
        if args[:2] == ["runs", "stop"] and len(args) == 3:
            return command_runs_stop(standin, args[2])
        if args == ["info"]:
            return command_info(standin, build)
        if args == ["subscriptions", "families"]:
            family = "chatgpt" if "codex" in standin.launcher else "anthropic"
            print(json.dumps([{"id": family, "auth": "vendor_login"}]))
            return 0
        if args == ["subscriptions", "list"]:
            family = "chatgpt" if "codex" in standin.launcher else "anthropic"
            print(json.dumps([{"id": "standin", "family": family}, {"id": family, "family": family}]))
            return 0
        refuse("invalid_input", f"Unknown command: {' '.join(args) or '(none)'}")
    finally:
        standin.record()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
