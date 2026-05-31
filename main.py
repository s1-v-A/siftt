import os
import time
import random
import re
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# =====================================================================
# SYSTEM INITIALIZATION & SAFETY CONFIGS
# =====================================================================
app = FastAPI(title="AeroDrop Engine")

# Global In-Memory Registry Mapping Room Codes to Active Sessions
vault_database = {}

# Local Disk Path Config for Storing Uploaded Binaries
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Safety Caps
MAX_FILE_SIZE = 50 * 1024 * 1024  # Enforce absolute maximum 50MB file size limit


# =====================================================================
# UTILITY HELPER FUNCTIONS & SECURITY PURIFIERS
# =====================================================================
def generate_room_code(length: int = 5) -> str:
    """
    Generates a unique, uppercase alphanumeric string.
    Excludes visually ambiguous characters like O, 0, I, and 1.
    """
    allowed_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        code = "".join(random.choice(allowed_chars) for _ in range(length))
        if code not in vault_database:
            return code


def sanitize_filename(filename: str) -> str:
    """
    Strips path traversal sequences (like ../) and malicious special character
    vectors to ensure files cannot escape the designated storage directory.
    """
    sanitized = re.sub(r'[^a-zA-Z0-9.\-_]', '', filename)
    if not sanitized:
        return f"unnamed_file_{int(time.time())}.bin"
    return sanitized


# =====================================================================
# ASYNCHRONOUS BACKGROUND SWEEPER (Auto-Destruct Loop)
# =====================================================================
async def cleanup_expired_rooms_loop():
    """
    Asynchronous daemon loop. Sweeps RAM and storage disk every 60 seconds 
    to permanently purge items older than 10 minutes (600 seconds).
    """
    while True:
        await asyncio.sleep(60)
        current_time = time.time()
        expired_rooms = [
            room_code for room_code, data in vault_database.items()
            if current_time - data["created_at"] > 600
        ]
        
        for room_code in expired_rooms:
            # Safely clear physical disk footprint
            for filename in vault_database[room_code]["files"]:
                safe_filename = f"{room_code}_{filename}"
                file_path = os.path.join(STORAGE_DIR, safe_filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass  # Ignore file-system locks; will catch on next cycle
            
            # Wipe tracking state from RAM
            del vault_database[room_code]


@app.on_event("startup")
async def startup_event():
    """Triggers the background janitor task when the engine boots up."""
    asyncio.create_task(cleanup_expired_rooms_loop())


# =====================================================================
# CORE API ENDPOINTS
# =====================================================================

@app.post("/api/rooms/create")
async def create_room():
    """Initializes a brand new, empty transfer room in our RAM database."""
    room_code = generate_room_code()
    
    vault_database[room_code] = {
        "files": [],
        "created_at": time.time()
    }
    
    return {
        "status": "success",
        "room_code": room_code
    }


@app.post("/api/rooms/{room_code}/upload")
async def upload_file_to_room(room_code: str, file: UploadFile = File(...)):
    """
    Accepts a raw binary stream, evaluates constraints chunk-by-chunk,
    sanitizes filenames, and registers metadata to the storage vault.
    """
    if room_code not in vault_database:
        raise HTTPException(status_code=404, detail="Target room does not exist or has expired.")
    
    # Clean filename against directory breakout injections
    clean_name = sanitize_filename(file.filename)
    safe_filename = f"{room_code}_{clean_name}"
    file_save_path = os.path.join(STORAGE_DIR, safe_filename)
    
    file_size = 0
    try:
        # Stream file write in 1MB allocations to prevent RAM overflows and verify file size limit
        with open(file_save_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    buffer.close()
                    if os.path.exists(file_save_path):
                        os.remove(file_save_path)
                    raise HTTPException(
                        status_code=413, 
                        detail="File dimensions exceed safety policies. Maximum capacity is 50MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_save_path):
            os.remove(file_save_path)
        raise HTTPException(status_code=500, detail=f"File IO stream exception: {str(e)}")
        
    vault_database[room_code]["files"].append(clean_name)
    
    return {
        "status": "success",
        "filename": clean_name,
        "message": f"File successfully anchored to room {room_code}"
    }


@app.get("/api/rooms/${room_code}")
@app.get("/api/rooms/{room_code}")
async def get_room_details(room_code: str):
    """Looks inside the RAM registry to see if a requested room exists."""
    normalized_code = room_code.upper()
    
    if normalized_code not in vault_database:
        raise HTTPException(
            status_code=404, 
            detail="This room linkage is invalid, or the lease has expired."
        )
        
    return {
        "status": "success",
        "room_code": normalized_code,
        "files": vault_database[normalized_code]["files"]
    }


@app.get("/api/rooms/{room_code}/files/{filename}")
async def download_file_from_room(room_code: str, filename: str):
    """Streams physical storage blocks back to the client as an isolated file stream."""
    if room_code not in vault_database:
        raise HTTPException(status_code=404, detail="This sharing link has expired.")
        
    clean_name = sanitize_filename(filename)
    
    if clean_name not in vault_database[room_code]["files"]:
        raise HTTPException(status_code=404, detail="File not found in this specific room space.")

    safe_filename = f"{room_code}_{clean_name}"
    file_path = os.path.join(STORAGE_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Physical asset missing from disk storage.")

    return FileResponse(
        path=file_path, 
        filename=clean_name, 
        media_type="application/octet-stream"
    )


# =====================================================================
# STATIC ASSETS & SINGLE-PAGE ROUTING SYSTEM (Must remain at the bottom)
# =====================================================================
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/{catchall:path}")
async def serve_frontend(catchall: str):
    """
    Fallback Route: Catches any URL path typed into the browser bar 
    and safely hands over our single-page index.html interface file.
    """
    return FileResponse(os.path.join(static_dir, "index.html"))