import socket
from http import HTTPStatus
from urllib.parse import parse_qs
from urllib.parse import urlparse


HOST = "127.0.0.1"
PORT = 8080

ENC_HEADER = "iso-8859-1"
ENC_BODY = "utf-8"
CRLFCRLF = b"\r\n\r\n"
READ_CHUNK_SIZE = 1024
MAX_HEADER_BYTES = 8192


def read_until_headers_complete(conn: socket.socket) -> bytes:
    """Read the HTTP header block (everything up to CRLFCRLF)."""
    buf = bytearray()

    while CRLFCRLF not in buf:
        if len(buf) > MAX_HEADER_BYTES:
            raise ValueError("HTTP headers too large")

        chunk = conn.recv(READ_CHUNK_SIZE)
        if not chunk:
            break
        buf += chunk

    header_bytes, _, _ = buf.partition(CRLFCRLF)
    return header_bytes


def parse_http_request(header_bytes: bytes) -> tuple[str, str, str, list[str]]:
    """
    Parse request line + raw header lines.
    Returns: method, target, version, headers_raw_lines
    """
    text = header_bytes.decode(ENC_HEADER, errors="replace")
    lines = text.split("\r\n")

    request_line = lines[0] if lines else ""
    parts = request_line.split(" ")

    method = parts[0] if len(parts) > 0 and parts[0] else "GET"
    target = parts[1] if len(parts) > 1 and parts[1] else "/"
    version = parts[2] if len(parts) > 2 and parts[2] else "HTTP/1.1"

    headers_raw = [ln for ln in lines[1:] if ln]
    return method, target, version, headers_raw


def status_from_target(target: str) -> HTTPStatus:
    """Extract `?status=<code>` from request target."""
    try:
        query = urlparse(target).query
        code = parse_qs(query).get("status", [None])[0]
        if code in (None, ""):
            return HTTPStatus(200)
        return HTTPStatus(int(code))
    except Exception:
        return HTTPStatus(200)


def build_plain_text_response(
    method: str,
    addr,
    status: HTTPStatus,
    version: str,
    request_headers: list[str],
) -> bytes:
    """Build a full HTTP response (status line + headers + plain-text body)."""
    if not version.startswith("HTTP/"):
        version = "HTTP/1.1"

    body_lines = [
        f"Request Method: {method}",
        f"Request Source: {addr}",
        f"Response Status: {status.value} {status.phrase}",
        *request_headers,
    ]
    body = ("\r\n".join(body_lines) + "\r\n").encode(ENC_BODY)

    status_line = f"{version} {status.value} {status.phrase}\r\n"
    resp_headers = [
        "Content-Type: text/plain; charset=utf-8",
        f"Content-Length: {len(body)}",
        "Connection: close",
    ]
    headers_blob = "\r\n".join(resp_headers)
    return (status_line + headers_blob + "\r\n\r\n").encode(ENC_HEADER) + body


def build_500_response(addr, err: Exception) -> bytes:
    """Build a consistent 500 response payload."""
    body = (
        "Request Method: UNKNOWN\r\n"
        f"Request Source: {addr}\r\n"
        "Response Status: 500 Internal Server Error\r\n"
        f"error: {err}\r\n"
    ).encode(ENC_BODY)

    head = (
        "HTTP/1.1 500 Internal Server Error\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n\r\n"
    ).encode(ENC_HEADER)

    return head + body


def handle_client(conn: socket.socket, addr) -> None:
    """Handle one TCP client connection."""
    header_bytes = read_until_headers_complete(conn)
    method, target, version, headers_raw = parse_http_request(header_bytes)
    status = status_from_target(target)

    response = build_plain_text_response(
        method=method,
        addr=addr,
        status=status,
        version=version,
        request_headers=headers_raw,
    )
    conn.sendall(response)


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(128)

        print(f"Listening on http://{HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            with conn:
                try:
                    handle_client(conn, addr)
                except Exception as e:
                    try:
                        conn.sendall(build_500_response(addr, e))
                    except Exception:
                        pass


if __name__ == "__main__":
    main()
