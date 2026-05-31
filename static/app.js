document.addEventListener("DOMContentLoaded", async () => {
    const createRoomBtn = document.getElementById("create-room-btn");
    const homeView = document.getElementById("home-view");
    const roomView = document.getElementById("room-view");
    const roomCodeDisplay = document.getElementById("room-code-display");
    const fileSelector = document.getElementById("file-selector");
    const uploadBtn = document.getElementById("upload-btn");
    const fileList = document.getElementById("file-list");
    const joinRoomInput = document.getElementById("join-room-input");
    const joinRoomBtn = document.getElementById("join-room-btn");

    let activeRoomCode = null;
    let isSender = false;

    // =====================================================================
    // UI BUILDER: Upgraded for the Dark Theme
    // =====================================================================
    function appendFileToUiList(filename) {
        const li = document.createElement("li");
        
        // Tailwind styling for the list item container
        li.className = "flex items-center gap-3 p-4 bg-gray-900/40 rounded-xl border border-gray-700/50 hover:border-gray-600 transition-colors mt-2";

        // Add a clean SVG file icon to every list item
        const iconContainer = document.createElement("div");
        iconContainer.innerHTML = `<svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>`;
        li.appendChild(iconContainer);

        if (isSender) {
            // SENDER ROLE: Clean text + Emerald 'Uploaded' Badge
            const textSpan = document.createElement("span");
            textSpan.className = "text-gray-300 flex-grow font-medium truncate";
            textSpan.textContent = filename;

            const badge = document.createElement("span");
            badge.className = "text-[10px] font-black uppercase tracking-widest text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full border border-emerald-400/20";
            badge.textContent = "Uploaded";

            li.appendChild(textSpan);
            li.appendChild(badge);
        } else {
            // RECEIVER ROLE: Blue clickable download hyperlink
            const downloadLink = document.createElement("a");
            downloadLink.href = `/api/rooms/${activeRoomCode}/files/${filename}`;
            downloadLink.className = "text-blue-400 hover:text-blue-300 underline underline-offset-4 flex-grow font-medium transition-colors truncate";
            downloadLink.textContent = filename;
            downloadLink.setAttribute("download", filename);
            li.appendChild(downloadLink);
        }

        fileList.appendChild(li);
    }

    // =====================================================================
    // ROUTING & API CALLS
    // =====================================================================
    async function initializeApplicationRoute() {
        const urlPath = window.location.pathname;
        const pathSegments = urlPath.split("/");

        if (pathSegments[1] === "room" && pathSegments[2]) {
            const codeFromUrl = pathSegments[2].toUpperCase();

            try {
                const response = await fetch(`/api/rooms/${codeFromUrl}`);
                if (response.ok) {
                    const data = await response.json();
                    activeRoomCode = data.room_code;
                    roomCodeDisplay.textContent = activeRoomCode;
                    homeView.classList.add("hidden");
                    roomView.classList.remove("hidden");
                    fileList.innerHTML = "";
                    data.files.forEach(filename => appendFileToUiList(filename));
                } else {
                    alert("This sharing room link has expired or never existed.");
                    window.history.pushState({}, "", "/");
                }
            } catch (error) {
                console.error("Routing failure:", error);
            }
        }
    }

    await initializeApplicationRoute();

    createRoomBtn.addEventListener("click", async () => {
        try {
            const response = await fetch("/api/rooms/create", { method: "POST" });
            if (response.ok) {
                const data = await response.json();
                activeRoomCode = data.room_code;
                isSender = true;
                
                window.history.pushState({}, "", `/room/${activeRoomCode}`);
                roomCodeDisplay.textContent = activeRoomCode;
                homeView.classList.add("hidden");
                roomView.classList.remove("hidden");
                fileList.innerHTML = ""; 
            } else {
                // FIXED: Explicitly alert if the backend refuses to generate a code
                alert(`Server returned an error: ${response.status}. Check your Uvicorn terminal!`);
            }
        } catch (error) {
            console.error(error);
            alert("Could not connect to the backend server. Is Python Uvicorn currently running?");
        }
    });

    joinRoomBtn.addEventListener("click", async () => {
        const inputCode = joinRoomInput.value.trim().toUpperCase();
        if (inputCode.length !== 5) {
            alert("Please enter a valid 5-character room code.");
            return;
        }

        activeRoomCode = inputCode;
        isSender = false;
        window.history.pushState({}, "", `/room/${activeRoomCode}`);
        fileList.innerHTML = "";
        
        await initializeApplicationRoute();
        joinRoomInput.value = "";
    });

    uploadBtn.addEventListener("click", async () => {
        if (fileSelector.files.length === 0) {
            alert("Please select a file first.");
            return;
        }

        const targetedFile = fileSelector.files[0];
        const payload = new FormData();
        payload.append("file", targetedFile);

        try {
            uploadBtn.textContent = "Uploading...";
            uploadBtn.disabled = true;

            const response = await fetch(`/api/rooms/${activeRoomCode}/upload`, {
                method: "POST",
                body: payload
            });

            if (response.ok) {
                const data = await response.json();
                appendFileToUiList(data.filename);
                fileSelector.value = "";
            } else {
                alert(`Upload failed with status: ${response.status}`);
            }
        } catch (error) {
            console.error("Upload error:", error);
            alert("Network error during upload.");
        } finally {
            uploadBtn.textContent = "Upload File";
            uploadBtn.disabled = false;
        }
    });
});