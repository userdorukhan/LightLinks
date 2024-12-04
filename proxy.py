"""
@author Dorukhan User
"""

import socket
import threading
import argparse
import signal
import sys

# Global variable for the proxy socket and shutdown flag
proxy_socket = None
shutting_down = False


def handle_exit(signal_received, frame):
    """
    Handles the exit signal of the program.
    Closes the proxy socket and terminates the program gracefully.
    """
    global proxy_socket, shutting_down

    if shutting_down:  # Prevent duplicate handling
        return

    shutting_down = True  # Signal all threads to stop
    print("\nShutting down proxy...")
    if proxy_socket:
        proxy_socket.close()  # Close the proxy socket if it's open
    sys.exit(0)  # Exit the program gracefully


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

    try:
        while True:
            connection = proxy_socket.accept()
            client_socket = connection[0]
            addr = connection[1]
            print(f"Connection received from client IP: {addr[0]}, Port: {addr[1]}")

            # Thread to handle the client connection
            client_handler = threading.Thread(
                target=handle_client,
                args=(client_socket, target_host, target_port)
            )
            client_handler.start()
    finally:
        if not shutting_down:  # Only run if the signal handler hasn’t already done cleanup!!!
            print("\nProxy socket closed. Exiting...")
            proxy_socket.close()


def handle_client(client_socket, target_host, target_port):
    """
    Handling communication between the client and the target server.
    """
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))

        # Start threads to forward data in both directions (For Multi-Threading)
        client_to_server = threading.Thread(target=forward_data, args=(client_socket, server_socket))
        server_to_client = threading.Thread(target=forward_data, args=(server_socket, client_socket))

        client_to_server.start()
        server_to_client.start()

        # Wait for threads to finish
        client_to_server.join(timeout=1)
        server_to_client.join(timeout=1)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
        server_socket.close()


# Forwarding data between client and server
def forward_data(src, dest):
    global shutting_down

    while not shutting_down:  # Stop if the proxy is shutting down
        try:
            data = src.recv(4096)
            if not data:
                break
            dest.send(data)  # Forward the data
        except socket.error:
            break  # Handle socket errors


if __name__ == "__main__":
    main()
