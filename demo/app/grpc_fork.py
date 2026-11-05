"""Keep gRPC's fork handlers out of the controller's child processes.

The OpenShell client loads gRPC in the controller. gRPC core enables fork support by default in
the Python build, so every fork() that precedes an exec (subprocess launches of git, docker,
node) restarts gRPC's thread pool in the child. On macOS one of those threads can resolve DNS
before the exec and abort the child (EXC_BREAKPOINT in libxpc): the launch fails and the
system shows "Python quit unexpectedly". Measured 2026-11-05: 10 native threads in a forked
child by default, 1 with the variable below. It must be set before gRPC is imported.
"""
import os

VARIABLE = "GRPC_ENABLE_FORK_SUPPORT"


def disable_grpc_fork_handlers(target=None):
    target = os.environ if target is None else target
    target[VARIABLE] = "false"
    return target
