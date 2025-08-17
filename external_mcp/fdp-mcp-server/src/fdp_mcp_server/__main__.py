import argparse
import asyncio
import logging

from fdp_mcp_server.streamable_client import run_streamable_http_client

DEFAULT_MCP_URL: str = "https://fdp.qianxin.com/mcp/v1/basic/mcp/"


CMD_EPILOG = """
Examples:
    fdp-mcp-server --url https://fdp.qianxin.com/mcp/v1/basic/mcp/
    fdp-mcp-server --url https://fdp.qianxin.com/mcp/v1/basic/mcp/ --debug
    fdp-mcp-server --url https://fdp.qianxin.com/mcp/v1/basic/mcp/ --header "fdp-access: xxxx" --header "fdp-secret: yyyy"
"""


def _setup_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start mcp server", epilog=CMD_EPILOG)
    parser.add_argument(
        "-d", "--debug", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument(
        "--url", default=DEFAULT_MCP_URL, help="QAX XLab's mcp server endpoint."
    )
    parser.add_argument(
        "-H",
        "--header",
        action="append",
        help="Headers to pass to the MCP server request.",
    )
    return parser


def _setup_logging(debug: bool) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
    )
    return logging.getLogger(__name__)


def main():
    parser = _setup_arg_parser()
    args = parser.parse_args()
    _setup_logging(args.debug)
    asyncio.run(run_streamable_http_client(args.url, headers=args.header))


if __name__ == "__main__":
    main()
