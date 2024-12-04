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
2. **Signal Handling**:
   - Graceful shutdown with `Ctrl+C` (SIGINT) or termination signals.
   - Displays statistics about accessed URLs upon exit.
3. **Basic TCP Proxy**:
   - Relays TCP connections between clients and a target server.
   - Handles unencrypted HTTP requests and responses.
4. **HTTP Parsing**:
   - Logs HTTP request lines and counts accessed URLs for statistical insights.

### **Creative Features**
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

### **Test the Proxy**
Use `curl` or Python's `requests` library to test the proxy:
```bash
curl -x 127.0.0.1:5555 http://httpbin.org/ip
```

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
   - Each client connection is handled in a separate thread (Multiple-Threading), allowing the proxy to serve multiple clients simultaneously.
   - Threads are used for bidirectional data forwarding (client-to-server and server-to-client).

2. **Timeouts and Resilience**:
   - `socket.settimeout()` ensures the proxy remains responsive and can gracefully handle network interruptions.

3. **HTTP Parsing**:
   - Minimal HTTP parsing is implemented to log requests and count accessed URLs. This is sufficient for basic unencrypted API calls.

4. **Cross-Platform Design**:
   - Standard Python libraries (`socket`, `argparse`, `signal`, etc.) are used to ensure compatibility across operating systems, so the performance can be high.

---
### **Performance**
   - The time complexity of the code is O(C⋅D+N⋅logN).

### **Factors Affecting Performance**

1. **Number of Connections ( C )**:
   - A high number of concurrent clients increases the number of threads and data to process.
2. **Data Size per Connection ( D )**:
   - Larger data transfers increase the number of `recv` and `sendall` operations.
3. **Number of Unique URLs ( N )**:
   - Affects the performance of URL counting and sorting for the top accessed URLs.

---

## **Testing**

### **Manual Testing**
1. **Basic Connectivity**:
   - Confirmed the proxy accepts connections and forwards data using tools like `curl` and Postman.
2. **HTTP Handling**:
   - Verified that HTTP requests and responses are logged and counted accurately.
3. **Signal Handling**:
   - Tested graceful shutdown with `Ctrl+C` and confirmed cleanup of threads and sockets.
4. **Multiple Testing**
   - Tested the proxy under multiple simultaneous connections to ensure stability.

---

## **Citations**
- See `Citations.md` for a detailed list of resources and references used during the project.

---

## **Contact**

For questions or feedback, feel free to reach out:

- **Email**: userdorukhan@berkeley.edu
- **LinkedIn**: [Dorukhan User](https://www.linkedin.com/in/dorukhanuser/)

---