# sifTT

A high-performance, minimalist, ephemeral file-sharing engine. Drop a file, grab a secure 5-digit room key, and pass it on. Designed with a strict zero-retention policy.

## Features

* **Ephemeral Pipelines:** Rooms and data automatically expire and self-destruct after 10 minutes.
* **RAM-Buffered Registry:** Active session states live purely in-memory, leaving zero persistent tracking footprint on your server.
* **Directory Ingress Protection:** Built-in cryptographic sanitization blocks path-traversal and file injection attempts.
* **Chunked Stream Allocation:** High-speed uploads are processed in 1MB iterations to maintain server stability and prevent memory overflows.

## Tech Stack

* **Backend:** Python / FastAPI / Asyncio
* **Frontend:** HTML5 / Tailwind CSS

## Local Installation & Deployment

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/sifTT.git](https://github.com/YOUR_USERNAME/sifTT.git)
    cd sifTT
    ```

2.  **Install dependencies:**
    ```bash
    pip install fastapi uvicorn
    ```

3.  **Boot the Engine:**
    ```bash
    uvicorn main:app --reload
    ```
    Open your browser and navigate to `http://127.0.0.1:8000`.

## Infrastructure Mechanics

* **Default Expiration:** 600 seconds (10 minutes)
* **Max Payload Ceiling:** 50MB per file
* **Storage Strategy:** Disk write mapping with alphanumeric signature isolation

## License

MIT License. Feel free to use, modify, and distribute.
