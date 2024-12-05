# LightLinks
# Light Links TCP Proxy Take Home Project

Welcome to my **TCP Proxy Project**! This repository contains the implementation of a simple TCP proxy developed for the Light Links take-home assessment.

---

## **Overview**

The objective of this project is to build a reliable and simple TCP proxy that can handle client-server communication over TCP, including relaying HTTP requests and responses. The proxy is designed to demonstrate:

- **Basic TCP functionality**: Forwarding client requests to a target server and relaying responses back to the client.
- **Command-line interface**: Easy configuration via command-line arguments.
- **Signal handling**: Shutdown with informative messages.
- **HTTP handling**: Parsing and logging HTTP requests/responses.
- **Creativity**: Additional features to enhance the proxy’s functionality.

---

## **Features**

### **Core Features**
1. **Command-Line Arguments**:
   - Specify the IP, port, and target server using the format:
     ```bash
     python3 proxy.py --ip 127.0.0.1 --port 5555 --server "192.168.5.2:80"
     ```
   - **New**: Additional optional arguments for enhanced functionality:
     - `--block-url`: Blocks requests to a specified URL pattern.
     - `--inject-header`: Injects a custom header into HTTP requests.

2. **Signal Handling**:
   - Graceful shutdown with `Ctrl+C` (SIGINT) or termination signals.
   - Displays statistics about accessed URLs upon exit.

3. **Basic TCP Proxy**:
   - Relays TCP connections between clients and a target server.
   - Handles unencrypted HTTP requests and responses.

4. **HTTP Parsing**:
   - Logs HTTP request lines and counts accessed URLs for statistical insights.

### **Creative Features**

- **URL Blocking**:
  - **Description**: Allows the proxy to block requests to specific URLs or URL patterns specified by the user.
  - **Usage**:
    ```bash
    python3 proxy.py --ip 127.0.0.1 --port 5555 --server "httpbin.org:80" --block-url "/ip"
    ```
  - **Behavior**: When a client attempts to access a blocked URL, the proxy responds with a `403 Forbidden` status code and a custom message, preventing the request from reaching the target server.

- **Header Injection**:
  - **Description**: Enables the proxy to inject custom HTTP headers into client requests before forwarding them to the target server.
  - **Usage**:
    ```bash
    python3 proxy.py --ip 127.0.0.1 --port 5555 --server "httpbin.org:80" --inject-header "X-Proxy-Header: LightLinksProxy"
    ```
  - **Behavior**: The specified header is added to all HTTP requests passing through the proxy, allowing for additional identification or tracking.

- **Top Accessed URLs**:
  - Displays the most accessed URLs during the session on shutdown.
  - Logs the statistics to `logs/top_urls.log`.

- **Comprehensive Logging**:
  - Logs all session activities to `logs/proxy.log`.
  - Provides detailed information about connections, HTTP requests, and errors.

- **Error Resilience**:
  - Handles socket timeouts and unexpected client disconnects gracefully.
  - Prevents resource leaks with safe cleanup procedures.

---

## **How to Run**

### **Prerequisites**
- Python 3.7 or later
- Ensure `pip` is installed to manage dependencies (if any).

### **Setup**
Clone the repository:
```bash
git clone https://github.com/userdorukhan/LightLinks.git
cd LightLinks
```

### **Run the Proxy**
Example command:
```bash
python3 proxy.py --ip 127.0.0.1 --port 5555 --server "httpbin.org:80"
```

#### **Arguments**
- `--ip`: IP address to listen on.
- `--port`: Port to listen on.
- `--server`: Target server in the format `ip:port`.
- `--block-url`: (Optional) URL or URL pattern to block.
- `--inject-header`: (Optional) Custom header to inject into HTTP requests.

---

## **Testing**

### **Test Cases**

Below are some test cases to help you verify the functionality of the TCP proxy:

#### **1. Basic Connectivity Test**

**Objective**: Ensure that the proxy can forward requests and responses between the client and the target server.

**Steps**:
- Start the proxy:
  ```bash
  python3 proxy.py --ip 127.0.0.1 --port 5555 --server "httpbin.org:80"
  ```
- In a separate terminal, send a request through the proxy using `curl`:
  ```bash
  curl -x 127.0.0.1:5555 http://httpbin.org/get
  ```
- **Expected Result**: You should receive a JSON response from httpbin.org containing details about your request.

**Verification**:
- Check the proxy logs in `logs/proxy.log` to see the logged request and response.
- Confirm that the URL `/get` is counted in the top accessed URLs.

#### **2. Blocking a Specific URL**

**Objective**: Test the proxy's ability to block requests to a specified URL.

**Steps**:
- Start the proxy with the `--block-url` option:
  ```bash
  python3 proxy.py --ip 127.0.0.1 --port 5555 --server "httpbin.org:80" --block-url "/ip"
  ```
- Send a request to the blocked URL:
  ```bash
  curl -x 127.0.0.1:5555 http://httpbin.org/ip
  ```
- **Expected Result**: You should receive a `403 Forbidden` response with the message "This request was blocked by the proxy. Access to this URL is restricted."

**Verification**:
- The proxy logs should indicate that the request to `/ip` was blocked.
- The URL `/ip` should be counted in the top accessed URLs.

#### **3. Injecting a Custom Header**

**Objective**: Verify that the proxy can inject a custom header into HTTP requests.

**Steps**:
- Start the proxy with the `--inject-header` option:
  ```bash
  python3 proxy.py --ip 127.0.0.1 --port 5555 --server "httpbin.org:80" --inject-header "X-Proxy-Header: LightLinksProxy"
  ```
- Send a request through the proxy:
  ```bash
  curl -x 127.0.0.1:5555 http://httpbin.org/headers
  ```
- **Expected Result**: The response should include the custom header `X-Proxy-Header` with the value `LightLinksProxy`.

**Verification**:
- Check the response from `httpbin.org/headers` to confirm the presence of the injected header.
- The proxy logs should indicate that the header was injected.

#### **4. Combining URL Blocking and Header Injection**

**Objective**: Test the proxy's functionality when both blocking and header injection features are used simultaneously.

**Steps**:
- Start the proxy with both `--block-url` and `--inject-header` options:
  ```bash
  python3 proxy.py --ip 127.0.0.1 --port 5555 --server "httpbin.org:80" --block-url "/status/200" --inject-header "X-Proxy-Header: LightLinksProxy"
  ```
- Send a request to a non-blocked URL:
  ```bash
  curl -x 127.0.0.1:5555 http://httpbin.org/get
  ```
- Send a request to the blocked URL:
  ```bash
  curl -x 127.0.0.1:5555 http://httpbin.org/status/200
  ```
- **Expected Results**:
  - For the first request, you should receive a normal response with the injected header.
  - For the second request, you should receive a `403 Forbidden` response.

**Verification**:
- Confirm that the injected header is present in the response from `/get`.
- Verify that the request to `/status/200` was blocked as per the proxy logs.
- The URLs should be counted and reflected in the top accessed URLs upon shutdown.

#### **5. Handling Multiple Simultaneous Connections**

**Objective**: Test the proxy's ability to handle multiple clients at the same time.

**Steps**:
- Start the proxy:
  ```bash
  python3 proxy.py --ip 127.0.0.1 --port 5555 --server "httpbin.org:80"
  ```
- Open multiple terminals or use a script to send several requests simultaneously:
  ```bash
  for i in {1..5}; do curl -x 127.0.0.1:5555 http://httpbin.org/delay/2 & done
  ```
- **Expected Result**: All requests should complete successfully, even though they include a 2-second delay.

**Verification**:
- All responses should be received without errors.
- Proxy logs should show simultaneous session handling.

#### **6. Graceful Shutdown Test**

**Objective**: Ensure that the proxy can shut down gracefully and display usage statistics.

**Steps**:
- Start the proxy and perform some requests as in previous test cases.
- Stop the proxy using `Ctrl+C`.
- **Expected Result**: The proxy should display a shutdown message and output the top accessed URLs.

**Verification**:
- Check the console output for the shutdown messages.
- Verify that `logs/top_urls.log` contains the correct statistics.

#### **7. Error Handling Test**

**Objective**: Test the proxy's resilience to errors, such as connecting to an invalid server.

**Steps**:
- Start the proxy with an invalid target server:
  ```bash
  python3 proxy.py --ip 127.0.0.1 --port 5555 --server "invalidserver:80"
  ```
- Send a request through the proxy:
  ```bash
  curl -x 127.0.0.1:5555 http://invalidserver/
  ```
- **Expected Result**: The client should receive a `502 Bad Gateway` response indicating that the proxy could not connect to the target server.

**Verification**:
- Proxy logs should show an error connecting to the target server.
- The proxy should not crash and should continue to accept new connections.

#### **8. Testing Signal Handling (Ctrl+Z)**

**Objective**: Verify that the proxy handles the `SIGTSTP` signal (Ctrl+Z) appropriately.

**Steps**:
- Start the proxy.
- Press `Ctrl+Z` to suspend the proxy.
- Resume the proxy by typing `fg` in the terminal.
- **Expected Result**: The proxy should suspend and resume without issues.

**Verification**:
- Proxy logs should indicate that it was suspended and resumed.
- The proxy should continue to function correctly after resuming.

---

## **Project Structure**

```
.
├── proxy.py             # Main proxy script
├── README.md            # Project description and instructions
├── Citations.md         # List of resources and citations
└── logs/                # Directory for log files
    ├── proxy.log        # Session logs
    ├── top_urls.log     # Top accessed URLs
└── LightLinksAssessment.pdf # Provided assignment details
```
---

## **Design Decisions**


1. **Thread-Based Architecture**:

   - **Reasoning**: I wanted the proxy to handle multiple client connections simultaneously without performance issues. After evaluating different concurrency models, I chose a multi-threaded approach because it allows each client connection to operate independently.
   - **Implementation**: The proxy spawns a new thread for each client connection, handling the bidirectional data forwarding between the client and the server. This means that the client-to-server and server-to-client communications are managed in separate threads, ensuring that delays or issues in one direction do not affect the other.

2. **Timeouts and Resilience**:

   - **Reasoning**: Network operations are unpredictable, and sockets can hang indefinitely if not managed properly. To prevent the proxy from becoming unresponsive due to network issues, I decided to implement timeouts.
   - **Implementation**: I utilized `socket.settimeout()` to set timeouts on socket operations. This ensures that if a network operation takes longer than expected, the proxy can handle it gracefully rather than hanging indefinitely.

3. **HTTP Parsing**:

   - **Reasoning**: For features like logging, URL blocking, and header injection, the proxy needs to understand and manipulate HTTP requests. I wanted to implement this functionality without adding unnecessary complexity or dependencies.
   - **Implementation**: I performed minimal HTTP parsing by manually reading and modifying the request lines and headers. This lightweight parsing is sufficient for handling unencrypted HTTP traffic and enables the proxy to log requests, block specific URLs, and inject headers.

4. **Cross-Platform Design**:

   - **Reasoning**: I aimed to make the proxy accessible to users on various operating systems. By relying solely on standard Python libraries, I could ensure compatibility without requiring users to install additional packages or deal with OS-specific issues.
   - **Implementation**: The proxy uses built-in Python modules like `socket`, `threading`, `argparse`, and `signal`. I avoided any platform-specific code or third-party dependencies that might limit portability.

5. **Logging and Monitoring**:

   - **Reasoning**: Effective logging is essential for monitoring the proxy's behavior and troubleshooting issues. I wanted to provide detailed logs without overwhelming the user with excessive information.
   - **Implementation**: I configured a logging system that records events to both the console and log files, with adjustable verbosity levels. Important events like connections, disconnections, errors, and blocked requests are clearly logged.

6. **Resource Cleanup and Error Handling**:

   - **Reasoning**: To ensure the proxy runs reliably over time, it's crucial to handle exceptions gracefully and clean up resources properly. Neglecting this can lead to memory leaks or crashes.
   - **Implementation**: I used `try...except...finally` blocks to manage exceptions and guarantee that sockets and threads are closed appropriately. Signal handlers for `SIGINT` and `SIGTERM` facilitate graceful shutdowns.

8. **URL Blocking and Header Injection**:

   - **Reasoning**: Enhancing the proxy with the ability to block specific URLs and inject custom headers provides greater control over the traffic passing through it. I wanted to implement these features in a way that was both effective and minimally invasive to the existing code.
   - **Implementation**: I extended the HTTP parsing logic to inspect request lines for URL patterns to block. For header injection, I modified the request headers before forwarding them to the server. Both features are configurable via command-line arguments.

Throughout the development process, my focus was on creating a proxy that is not only functional but also user-friendly and adaptable. Thank you so much for providing this opportunity to me :)

---

### **Performance**

- The time complexity of the code is O(C⋅D + N⋅logN).

### **Factors Affecting Performance**

1. **Number of Connections (C)**:
   - A high number of concurrent clients increases the number of threads and data to process.

2. **Data Size per Connection (D)**:
   - Larger data transfers increase the number of `recv` and `sendall` operations.

3. **Number of Unique URLs (N)**:
   - Affects the performance of URL counting and sorting for the top accessed URLs.

4. **URL Blocking and Header Injection**:
   - Additional processing is required to parse and modify HTTP requests, which may slightly impact performance.

---

## **Citations**

- See `Citations.md` for a detailed list of resources and references used during the project.

---

## **Contact**

For questions or feedback, feel free to reach out:

- **Email**: userdorukhan@berkeley.edu
- **LinkedIn**: [Dorukhan User](https://www.linkedin.com/in/dorukhanuser/)