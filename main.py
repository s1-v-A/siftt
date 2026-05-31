import os
import time
import random
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# =====================================================================
# SYSTEM INITIALIZATION
# =====================================================================
app = FastAPI(title="AeroDrop Engine")

# Global In-Memory Registry Mapping Room Codes to Active Sessions
vault_database = {}

# Local Disk Path Config for Storing Uploaded Binaries
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


# =====================================================================
# UTILITY HELPER FUNCTIONS
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


# =====================================================================
# CORE API ENDPOINTS (Evaluated Top-to-Bottom)
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
    Accepts a raw binary file stream, saves it to the local storage folder,
    and attaches the file metadata to the active RAM room.
    """
    if room_code not in vault_database:
        raise HTTPException(status_code=404, detail="Target room does not exist or has expired.")
    
    safe_filename = f"{room_code}_{file.filename}"
    file_save_path = os.path.join(STORAGE_DIR, safe_filename)
    
    with open(file_save_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    vault_database[room_code]["files"].append(file.filename)
    
    return {
        "status": "success",
        "filename": file.filename,
        "message": f"File successfully anchored to room {room_code}"
    }


@app.get("/api/rooms/{room_code}")
async def get_room_details(room_code: str):
    """
    Looks inside the RAM registry to see if a requested room exists.
    If found, returns the list of active files anchored to it.
    """
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
    """
    Verifies room ownership in RAM, matches the physical file on disk,
    and streams the binary data back to the user as an active download.
    """
    if room_code not in vault_database:
        raise HTTPException(status_code=404, detail="This sharing link has expired.")
        
    if filename not in vault_database[room_code]["files"]:
        raise HTTPException(status_code=404, detail="File not found in this specific room space.")

    safe_filename = f"{room_code}_{filename}"
    file_path = os.path.join(STORAGE_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Physical asset missing from disk storage.")

    return FileResponse(
        path=file_path, 
        filename=filename, 
        media_type="application/octet-stream"
    )


# =====================================================================
# STATIC ASSETS & SINGLE-PAGE ROUTING SYSTEM (Must remain at the bottom)
# =====================================================================
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/assets", StaticFiles(directory=static_dir), name="static")

@app.get("/{catchall:path}")
async def serve_frontend(catchall: str):
    """
    Fallback Route: Catches any URL path typed into the browser bar 
    and safely hands over our single-page index.html interface file.
    """
    return FileResponse(os.path.join(static_dir, "index.html"))