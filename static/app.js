document.addEventListener("DOMContentLoaded", () => {
    // 1. Grab all UI component references
    const createRoomBtn = document.getElementById("create-room-btn");
    const homeView = document.getElementById("home-view");
    const roomView = document.getElementById("room-view");
    const roomCodeDisplay = document.getElementById("room-code-display");
    
    // NEW references for our upload engine
    const fileSelector = document.getElementById("file-selector");
    const uploadBtn = document.getElementById("upload-btn");
    const fileList = document.getElementById("file-list");

    // A global variable to store our active 5-digit room token
    let activeRoomCode = null;

    // 2. Room Creation Trigger
    createRoomBtn.addEventListener("click", async () => {
        try {
            const response = await fetch("/api/rooms/create", { method: "POST" });
            
            if (response.ok) {
                const data = await response.json();
                activeRoomCode = data.room_code; // Store the code globally

                window.history.pushState({}, "", `/room/${activeRoomCode}`);

                roomCodeDisplay.textContent = activeRoomCode;
                homeView.classList.add("hidden");
                roomView.classList.remove("hidden");
            } else {
                alert("Backend failed to initialize an active transfer node.");
            }
        } catch (error) {
            console.error("Networking breakdown:", error);
            alert("Could not establish a stable connection with AeroDrop server.");
        }
    });

    // =====================================================================
    // 3. NEW COMPONENT: THE FILE UPLOAD TRIGGER ENGINE
    // =====================================================================
    uploadBtn.addEventListener("click", async () => {
        // Validation Guard A: Ensure a file has actually been selected
        if (fileSelector.files.length === 0) {
            alert("Please select a file from your device first.");
            return;
        }

        const targetedFile = fileSelector.files[0];

        // FormData is a native browser utility that builds an HTML form payload.
        // It structures the raw binary stream data exactly how FastAPI expects it!
        const payload = new FormData();
        payload.append("file", targetedFile);

        try {
            uploadBtn.textContent = "Uploading...";
            uploadBtn.disabled = true;

            // Fire the network stream to our dynamic backend endpoint
            const response = await fetch(`/api/rooms/${activeRoomCode}/upload`, {
                method: "POST",
                body: payload // Passing the raw data wrapper
            });

            if (response.ok) {
                const data = await response.json();
                
                // Construct a new visual list item line for the uploaded file
                const newListItem = document.createElement("li");
                newListItem.textContent = data.filename;
                newListItem.style.margin = "6px 0";
                
                // Inject the element live into our HTML layout code
                fileList.appendChild(newListItem);

                // Clear out the file selector box so the user can upload another file
                fileSelector.value = "";
                alert("File successfully anchored into RAM storage!");
            } else {
                alert("Upload rejected. This room might have expired.");
            }
        } catch (error) {
            console.error("Upload transmission error:", error);
            alert("Connection lost during file transfer stream.");
        } finally {
            // Restore button styling back to normal
            uploadBtn.textContent = "Upload";
            uploadBtn.disabled = false;
        }
    });
});