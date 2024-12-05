"""
TCP Proxy Server
@author Dorukhan User
"""

import os
import socket
import threading
import argparse
import signal
import sys
import logging
from collections import Counter

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set logger to capture DEBUG and higher-level messages

# Add a console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)  # Console handler captures DEBUG and higher-level messages
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Add a file handler for general logs
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = logging.FileHandler('logs/proxy.log')
file_handler.setLevel(logging.DEBUG)  # File handler captures DEBUG and higher-level messages
file_handler.setFormatter(console_formatter)
logger.addHandler(file_handler)

# Global variables
shutting_down = False
url_counter = Counter()
url_counter_lock = threading.Lock()


def handle_exit(signal_received, frame):
    """
    Handles the exit signal of the program.
    Closes the proxy socket, waits for all threads to terminate,
    and logs the total usage statistics.
    """
    global shutting_down

    if shutting_down:  # Prevent duplicate handling
        return

    shutting_down = True  # Signal all threads to stop
    logger.info("Shutting down proxy...")

    # Output top accessed URLs
    try:
        logger.info("Top Accessed URLs:")
        with url_counter_lock:
            if len(url_counter) == 0:
                logger.info("No URLs accessed during this session.")
            else:
                top_urls = url_counter.most_common(10)
                for url, count in top_urls:
                    logger.info(f"{url}: {count} times")

                # Write to a separate log file
                with open('logs/top_urls.log', 'w') as f:
                    f.write("Top Accessed URLs:\n")
                    for url, count in top_urls:
                        f.write(f"{url}: {count} times\n")
                    f.flush()  # Ensure all data is written
                logger.info("Top URLs written to logs/top_urls.log")
    except Exception as e:
        logger.error(f"Error while writing usage logs: {e}")

    # Wait for threads to finish
    for thread in threading.enumerate():
        if thread != threading.main_thread():
            thread.join()

    # Notify user of successful shutdown
    logger.info("Proxy closed successfully.")
    sys.exit(0)


def main():
    global shutting_down

    # Required Arguments
    parser = argparse.ArgumentParser(description="Simple TCP Proxy")
    parser.add_argument("--ip", required=True, help="IP address to listen on")
    parser.add_argument("--port", required=True, type=int, help="Port to listen on")
    parser.add_argument("--server", required=True, help="Target server in 'ip:port' format")

    # Optional Arguments
    parser.add_argument("--block-url", default=None, help="Block requests to this URL")
    parser.add_argument("--inject-header", default=None, help="Inject this header into requests")

    args = parser.parse_args()

    listen_ip = args.ip
    listen_port = args.port
    target_server = args.server
    block_url = args.block_url
    inject_header = args.inject_header

    try:
        target_host, target_port = target_server.split(":")
        target_port = int(target_port)
    except ValueError:
        logger.error("Target server format must be 'ip:port'")
        return

    # Set up the proxy server socket
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reusing the same address (For test cases)
    proxy_socket.bind((listen_ip, listen_port))
    proxy_socket.listen(5)

    logger.info(
        "\n"
        "***************************************************\n"
        "      TCP Proxy is Running\n"
        "   ️  Listening on:  {listen_ip}:{listen_port}\n"
        "      Forwarding to:  {target_host}:{target_port}\n"
        "***************************************************\n"
        .format(listen_ip=listen_ip, listen_port=listen_port, target_host=target_host, target_port=target_port)
    )

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)  # Handle Ctrl+C
    signal.signal(signal.SIGTSTP, handle_suspend)  # Handle CTRL+Z
    signal.signal(signal.SIGTERM, handle_exit)  # Handle termination signals

    while not shutting_down:
        try:
            client_socket, addr = proxy_socket.accept()
            logger.info(f"Connection received from client {addr[0]}:{addr[1]}")
            client_handler = threading.Thread(
                target=handle_client,
                args=(client_socket, target_host, target_port, addr, block_url, inject_header)
            )
            client_handler.start()
        except Exception as e:
            logger.exception("Error accepting connections")
            break


def handle_client(client_socket, target_host, target_port, client_address, block_url, inject_header):
    client_ip, client_port = client_address
    server_socket = None
    client_socket_closed = False
    server_socket_closed = False
    socket_closed_flags = {'client_socket_closed': client_socket_closed, 'server_socket_closed': server_socket_closed}
    try:
        logger.info(f"Session started for {client_ip}:{client_port}")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.connect((target_host, target_port))
        except socket.gaierror as e:
            logger.error(f"Failed to resolve server address {target_host}:{target_port}: {e}")
            response = (
                "HTTP/1.1 502 Bad Gateway\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 77\r\n"
                "\r\n"
                "The proxy could not resolve or connect to the target server. Please check the server address.\r\n"
            ).encode()
            client_socket.sendall(response)
            client_socket.close()
            socket_closed_flags['client_socket_closed'] = True
            return

        client_to_server = threading.Thread(
            target=forward_data,
            args=(client_socket, server_socket, 'Request', client_ip, client_port, block_url, inject_header,
                  socket_closed_flags)
        )
        server_to_client = threading.Thread(
            target=forward_data,
            args=(server_socket, client_socket, 'Response', client_ip, client_port, None, None, socket_closed_flags)
        )

        client_to_server.start()
        server_to_client.start()

        client_to_server.join()
        server_to_client.join()

    except Exception as e:
        logger.exception(f"Error handling client {client_ip}:{client_port}")
    finally:
        # Close client socket if it's not already closed
        if not socket_closed_flags['client_socket_closed']:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
                logger.debug("Client socket closed successfully.")
            except OSError as e:
                if e.errno != 57:
                    logger.error(f"Unexpected error when closing client socket: {e}")
            socket_closed_flags['client_socket_closed'] = True

        # Close server socket if it's not already closed
        if server_socket and not socket_closed_flags['server_socket_closed']:
            try:
                server_socket.shutdown(socket.SHUT_RDWR)
                server_socket.close()
                logger.debug("Server socket closed successfully.")
            except OSError as e:
                if e.errno != 57:
                    logger.error(f"Unexpected error when closing server socket: {e}")
            socket_closed_flags['server_socket_closed'] = True

        logger.info(f"Session ended for {client_ip}:{client_port}")


def forward_data(src, dest, direction, client_ip, client_port, block_url=None, inject_header=None, socket_closed_flags=None):
    """
    Forwards data between the source and destination sockets.
    Allows filtering and modification based on user-defined rules.
    """
    # Determine which flags correspond to src and dest
    if direction == 'Request':
        src_closed_key = 'client_socket_closed'
        dest_closed_key = 'server_socket_closed'
    else:
        src_closed_key = 'server_socket_closed'
        dest_closed_key = 'client_socket_closed'

    # Check if sockets have been closed before starting
    if socket_closed_flags[src_closed_key] or socket_closed_flags[dest_closed_key]:
        logger.debug(f"Sockets already closed for {direction}. Exiting thread.")
        return  # Exit if sockets are already closed

    try:
        src.settimeout(1.0)  # Set a timeout for the source socket
    except OSError as e:
        if e.errno == 9:  # Bad file descriptor
            logger.debug(f"Socket already closed when setting timeout for {direction}. Exiting thread.")
            return  # Socket is closed, exit the function
        else:
            logger.error(f"Unexpected error when setting socket timeout: {e}")
            return

    while not shutting_down:
        # Check if sockets have been closed in each iteration
        if socket_closed_flags[src_closed_key] or socket_closed_flags[dest_closed_key]:
            logger.debug(f"Sockets have been closed during {direction}. Exiting thread.")
            break

        try:
            data = src.recv(4096)
            if not data:
                break

            if direction == 'Request' and b"HTTP" in data:
                lines = data.decode(errors='ignore').splitlines()
                request_line = lines[0]
                try:
                    method, url, _ = request_line.split()
                    with url_counter_lock:
                        url_counter[url] += 1
                    logger.debug(f"URL counted: {url}")

                    # Block specific URLs
                    if block_url and block_url in url:
                        logger.info(f"Blocked request to {url}")
                        # Send a 403 Forbidden response to the client
                        body = "This request was blocked by the proxy. Access to this URL is restricted.\r\n"
                        response = (
                            "HTTP/1.1 403 Forbidden\r\n"
                            "Content-Type: text/plain\r\n"
                            f"Content-Length: {len(body)}\r\n"
                            "\r\n"
                            f"{body}"
                        ).encode()
                        src.sendall(response)
                        # Close the sockets and update flags
                        src.close()
                        dest.close()
                        socket_closed_flags[src_closed_key] = True
                        socket_closed_flags[dest_closed_key] = True
                        return  # Stop processing this request

                    # Inject headers if specified
                    if inject_header:
                        # Ensure proper header format and inject after the request line
                        header_key, header_value = inject_header.split(":", 1)
                        header_value = header_value.strip()
                        header_line = f"{header_key}: {header_value}\r\n"

                        # Insert the custom header right after the request line
                        if len(lines) > 1 and ":" in lines[1]:  # Make sure headers exist
                            lines.insert(1, header_line.strip())
                            logger.debug(f"Header injected: {header_key}: {header_value}")
                        else:
                            logger.warning(f"Cannot inject header: {inject_header}. No valid headers section.")

                        # Reassemble the HTTP request
                        data = "\r\n".join(lines).encode() + b"\r\n\r\n"

                    logger.info(f"{direction} from {client_ip}:{client_port} - {request_line}")

                except ValueError:
                    logger.warning(f"Could not parse request line: {request_line}")

            dest.sendall(data)
        except socket.timeout:
            continue
        except socket.error as e:
            if shutting_down:
                break
            if e.errno == 9:  # Bad file descriptor
                # Socket has been closed, exit the loop without logging an error
                break
            logger.error(f"Socket error while forwarding {direction}: {e}")
            break
        except Exception as e:
            logger.exception("Unexpected error in forward_data")
            break


def handle_suspend(signal_received, frame):
    """
    Handles the SIGTSTP (CTRL+Z) signal.
    Logs the message stating it was interrupted by CTRL+Z.
    """
    logger.info("Proxy suspended with CTRL+Z. Use 'fg' to resume or 'kill' to terminate.")
    os.kill(os.getpid(), signal.SIGSTOP)  # Suspend the process


if __name__ == "__main__":
    main()
