"""
@author Dorukhan User
"""

import os
import socket
import threading
import argparse
import signal
import sys
import logging
from datetime import datetime
from collections import Counter

# Global variables
proxy_socket = None
shutting_down = False
url_counter = Counter()
url_counter_lock = threading.Lock()


def handle_exit(signal_received, frame):
    """
    Handles the exit signal of the program.
    Closes the proxy socket, waits for all threads to terminate,
    and logs the total usage statistics.
    """
    global proxy_socket, shutting_down

    if shutting_down:  # Prevent duplicate handling
        return

    shutting_down = True  # Signal all threads to stop
    print("\nShutting down proxy...")

    # Don't accept new connections so closing the socket
    if proxy_socket:
        proxy_socket.close()

    # Wait for threads to finish
    for thread in threading.enumerate():
        if thread != threading.main_thread():
            thread.join()

    # Output top accessed URLs
    try:
        print("\nTop Accessed URLs:")
        with url_counter_lock:
            if len(url_counter) == 0:
                print("No URLs accessed during this session.")
            else:
                # Sort URLs by count
                top_urls = url_counter.most_common(10)

                # Print top accessed URLs to the console
                for url, count in top_urls:
                    print(f"{url}: {count} times")

                # Write top accessed URLs to a log file
                log_path = 'logs/top_urls.log'
                with open(log_path, 'w') as f:
                    f.write("Top Accessed URLs:\n")
                    for url, count in top_urls:
                        f.write(f"{url}: {count} times\n")
                print(f"Top URLs written to {log_path}")
    except Exception as e:
        print(f"Error while writing usage logs: {e}")
    sys.exit(0)


def main():
    global proxy_socket

    # For command line arguments
    parser = argparse.ArgumentParser(description="Simple TCP Proxy")
    parser.add_argument("--ip", required=True, help="IP address to listen on")
    parser.add_argument("--port", required=True, type=int, help="Port to listen on")
    parser.add_argument("--server", required=True, help="Target server in 'ip:port' format")
    args = parser.parse_args()

    listen_ip = args.ip
    listen_port = args.port
    target_server = args.server

    # Ensure the logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Target Server Details
    try:
        target_host, target_port = target_server.split(":")
        target_port = int(target_port)
    except ValueError:
        print("Error: Target server format must be 'ip:port'")
        return

    # The proxy server socket
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind((listen_ip, listen_port))
    proxy_socket.listen(5)  # Maximum 5 connections at a time

    print(f"Listening: {listen_ip}:{listen_port} and forwarding to {target_host}:{target_port}")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # Handle termination signals

    while True:
        try:
            client_socket, addr = proxy_socket.accept()
            print(f"Connection received from client IP: {addr[0]}, Port: {addr[1]}")

            # Thread to handle the client connection
            client_handler = threading.Thread(
                target=handle_client,
                args=(client_socket, target_host, target_port, addr)
            )
            client_handler.start()
        except Exception as e:
            print(f"Error: {e}")
            break


def handle_client(client_socket, target_host, target_port, client_address):
    """
    Handling communication between the client and the target server.
    """
    client_ip, client_port = client_address
    try:
        # Create a logger for this session
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'logs/session_{timestamp}_{client_ip}_{client_port}.log'
        logger = logging.getLogger(f'session_{client_ip}_{client_port}')
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(log_filename)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Log session start
        logger.info(f"Session started for {client_ip}:{client_port}")

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))

        # Start threads to forward data in both directions
        client_to_server = threading.Thread(
            target=forward_data,
            args=(client_socket, server_socket, logger, 'Request', client_ip, client_port)
        )
        server_to_client = threading.Thread(
            target=forward_data,
            args=(server_socket, client_socket, logger, 'Response', client_ip, client_port)
        )

        client_to_server.start()
        server_to_client.start()

        client_to_server.join()
        server_to_client.join()

        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except socket.error:
            pass
        try:
            server_socket.shutdown(socket.SHUT_RDWR)
            server_socket.close()
        except socket.error:
            pass

        # Log session end
        logger.info(f"Session ended for {client_ip}:{client_port}")
        logger.removeHandler(fh)
        fh.close()

    except Exception as e:
        print(f"Error: {e}")


def forward_data(src, dest, logger, direction, client_ip, client_port):
    global shutting_down

    src.settimeout(1.0)

    while not shutting_down:
        try:
            # Read data from source
            data = src.recv(4096)
            if not data:
                break

            # Log HTTP data
            if b"HTTP" in data:
                lines = data.decode(errors='ignore').splitlines()
                if lines:
                    if direction == 'Request':
                        request_line = lines[0]
                        logger.info(f"{direction} from {client_ip}:{client_port} - {request_line}")
                        # Track URL
                        try:
                            method, url, _ = request_line.split()
                            with url_counter_lock:
                                url_counter[url] += 1
                        except Exception as e:
                            logger.error(f"Failed to parse request line: {e}")
                    elif direction == 'Response':
                        status_line = lines[0]
                        logger.info(f"{direction} to {client_ip}:{client_port} - {status_line}")

            # Send data to destination
            dest.sendall(data)
        except socket.timeout:
            # Timeout occurred, check if shutting down
            continue
        except (socket.error, OSError) as e:
            if shutting_down:
                break
            logger.error(f"Socket error: {e}")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break


if __name__ == "__main__":
    main()
