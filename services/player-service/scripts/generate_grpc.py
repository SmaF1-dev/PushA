from pathlib import Path

from grpc_tools import protoc


SERVICE_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = SERVICE_ROOT.parent.parent
PROTO_ROOT = REPOSITORY_ROOT / "proto"
GENERATED_PACKAGE = SERVICE_ROOT / "app" / "grpc" / "generated"
VIRTUAL_PROTO = "app/grpc/generated/valorant_player_service.proto"


def main() -> None:
    """Generate protobuf messages and the asynchronous-compatible gRPC stub.

    The virtual include mapping makes generated imports use the real Python
    package path without copying or modifying the shared ``.proto`` file.

    :returns: ``None``.
    :raises RuntimeError: If ``protoc`` reports a generation failure.
    """
    GENERATED_PACKAGE.mkdir(parents=True, exist_ok=True)
    result = protoc.main(
        [
            "grpc_tools.protoc",
            f"-Iapp/grpc/generated={PROTO_ROOT}",
            f"--python_out={SERVICE_ROOT}",
            f"--grpc_python_out={SERVICE_ROOT}",
            VIRTUAL_PROTO,
        ]
    )
    if result != 0:
        raise RuntimeError(f"protoc exited with status {result}")


if __name__ == "__main__":
    main()
