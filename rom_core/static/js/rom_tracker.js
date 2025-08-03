// --- Utility functions for localStorage state ---
function saveAngleResult(type, value) {
    let results = JSON.parse(localStorage.getItem("rom_results") || '{}');
    results[type] = value;
    localStorage.setItem("rom_results", JSON.stringify(results));
}

function getAllAngleResults() {
    return JSON.parse(localStorage.getItem("rom_results") || '{}');
}

function clearAllAngleResults() {
    localStorage.removeItem("rom_results");
}

// --- Main tracking logic ---
function calculateAngle(a, b, c) {
    const AB = { x: b.x - a.x, y: b.y - a.y };
    const CB = { x: b.x - c.x, y: b.y - c.y };
    const dot = AB.x * CB.x + AB.y * CB.y;
    const magAB = Math.sqrt(AB.x ** 2 + AB.y ** 2);
    const magCB = Math.sqrt(CB.x ** 2 + CB.y ** 2);
    const angle = Math.acos(dot / (magAB * magCB));
    return Math.round(angle * (180 / Math.PI));
}

function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}

function startROMTracking(romType, onComplete) {
    const videoElement = document.getElementById('pose-video');
    const countdownElement = document.getElementById('countdown');
    const resultElement = document.getElementById('result');

    let countdown = 10;
    let finalAngle = null;
    let countdownInterval = null;

    function onResults(results) {
        if (!results.poseLandmarks) return;

        const landmarks = results.poseLandmarks;
        const shoulder = landmarks[11]; // Left shoulder
        const elbow = landmarks[13];    // Left elbow
        const hip = landmarks[23];      // Left hip

        const angle = calculateAngle(hip, shoulder, elbow);

        if (countdown <= 0 && finalAngle === null) {
            finalAngle = angle;
            resultElement.innerText = `Measured ${romType.toUpperCase()} Angle: ${finalAngle}°`;
            saveAngleResult(romType, finalAngle);

            setTimeout(() => {
                if (onComplete) onComplete();
            }, 2000);
        } else if (finalAngle === null) {
            resultElement.innerText = `Live ${romType.toUpperCase()} Angle: ${angle}°`;
        }
    }

    // MediaPipe Pose setup
    const pose = new Pose({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
    });
    pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        enableSegmentation: false,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });
    pose.onResults(onResults);

    const camera = new Camera(videoElement, {
        onFrame: async () => {
            await pose.send({ image: videoElement });
        },
        width: 640,
        height: 480
    });
    camera.start();

    function startCountdown() {
        countdownElement.innerText = `Get Ready: ${countdown}s`;
        countdownInterval = setInterval(() => {
            countdown--;
            if (countdown > 0) {
                countdownElement.innerText = `Get Ready: ${countdown}s`;
            } else {
                clearInterval(countdownInterval);
                countdownElement.innerText = "Hold Position... Measuring!";
            }
        }, 1000);
    }

    startCountdown();
}

// --- Saving results after all 4 tests ---
function saveAllROMResults() {
    let allResults = getAllAngleResults();
    fetch('/save-rom-test/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(allResults)
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert("ROM test saved!");
            clearAllAngleResults();
            window.location.href = "/patient/";
        } else {
            alert("Error saving data.");
        }
    });
}

// --- For Cancel button ---
function cancelROMTest() {
    clearAllAngleResults();
    window.location.href = "/patient/";
}

// --- Make accessible globally ---
window.startROMTracking = startROMTracking;
window.saveAllROMResults = saveAllROMResults;
window.cancelROMTest = cancelROMTest;
window.getAllAngleResults = getAllAngleResults;
