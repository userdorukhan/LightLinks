import os
import socket
import threading
import argparse
import signal
import sys
import logging
from datetime import datetime
from collections import Counter

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add a console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Add a file handler for general logs
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = logging.FileHandler('logs/proxy.log')
file_handler.setLevel(logging.INFO)
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
                logger.info("Top URLs written to logs/top_urls.log")
    except Exception as e:
        logger.error(f"Error while writing usage logs: {e}")

    # Wait for threads to finish
    for thread in threading.enumerate():
        if thread != threading.main_thread():
            thread.join()

    # Notify user of successful shutdown
    logger.info("Proxy closed successfully.")
    print("Proxy closed.")  # Friendly message
    sys.exit(0)


def main():
    global shutting_down

    parser = argparse.ArgumentParser(description="Simple TCP Proxy")
    parser.add_argument("--ip", required=True, help="IP address to listen on")
    parser.add_argument("--port", required=True, type=int, help="Port to listen on")
    parser.add_argument("--server", required=True, help="Target server in 'ip:port' format")
    args = parser.parse_args()

    listen_ip = args.ip
    listen_port = args.port
    target_server = args.server

    try:
        target_host, target_port = target_server.split(":")
        target_port = int(target_port)
    except ValueError:
        logger.error("Target server format must be 'ip:port'")
        return

    # Set up the proxy server socket
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind((listen_ip, listen_port))
    proxy_socket.listen(5)
    logger.info(f"Proxy listening on {listen_ip}:{listen_port} and forwarding to {target_host}:{target_port}")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # Handle termination signals

    while not shutting_down:
        try:
            client_socket, addr = proxy_socket.accept()
            logger.info(f"Connection received from client {addr[0]}:{addr[1]}")
            client_handler = threading.Thread(
                target=handle_client,
                args=(client_socket, target_host, target_port, addr)
            )
            client_handler.start()
        except Exception as e:
            logger.exception("Error accepting connections")
            break


def handle_client(client_socket, target_host, target_port, client_address):
    """
    Handles communication between the client and the target server.
    """
    client_ip, client_port = client_address
    server_socket = None  # Initialize to ensure proper cleanup
    try:
        logger.info(f"Session started for {client_ip}:{client_port}")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))

        client_to_server = threading.Thread(
            target=forward_data,
            args=(client_socket, server_socket, 'Request', client_ip, client_port)
        )
        server_to_client = threading.Thread(
            target=forward_data,
            args=(server_socket, client_socket, 'Response', client_ip, client_port)
        )

        client_to_server.start()
        server_to_client.start()

        client_to_server.join()
        server_to_client.join()

    except Exception as e:
        logger.exception(f"Error handling client {client_ip}:{client_port}")
    finally:
        # Safely close client and server sockets
        try:
            if client_socket:
                client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
        except OSError as e:
            logger.debug(f"Client socket already closed: {e}")

        try:
            if server_socket:
                server_socket.shutdown(socket.SHUT_RDWR)
                server_socket.close()
        except OSError as e:
            logger.debug(f"Server socket already closed: {e}")

        logger.info(f"Session ended for {client_ip}:{client_port}")


def forward_data(src, dest, direction, client_ip, client_port):
    """
    Forwards data between the source and destination sockets.
    Logs HTTP requests/responses and updates URL counters for requests.
    """
    src.settimeout(1.0)  # Set a timeout for the source socket

    while not shutting_down:
        try:
            data = src.recv(4096)
            if not data:
                break

            if direction == 'Request' and b"HTTP" in data:
                lines = data.decode(errors='ignore').splitlines()
                request_line = lines[0]
                logger.info(f"{direction} from {client_ip}:{client_port} - {request_line}")
                try:
                    method, url, _ = request_line.split()
                    with url_counter_lock:
                        url_counter[url] += 1
                except ValueError:
                    logger.error(f"Failed to parse request line: {request_line}")
            elif direction == 'Response' and b"HTTP" in data:
                logger.debug(f"{direction} to {client_ip}:{client_port} - {data[:50].decode(errors='ignore')}...")

            dest.sendall(data)
        except socket.timeout:
            continue
        except socket.error as e:
            if shutting_down:
                break
            logger.error(f"Socket error: {e}")
            break
        except Exception as e:
            logger.exception("Unexpected error in forward_data")
            break


if __name__ == "__main__":
    main()