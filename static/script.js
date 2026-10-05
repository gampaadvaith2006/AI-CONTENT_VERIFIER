// ============================================
// VERITAS AI - FRONTEND SCRIPT
// ============================================

document.addEventListener("DOMContentLoaded", () => {

    const newsInput = document.getElementById("news");
    const result = document.getElementById("result");
    const checkButton = document.getElementById("checkButton");

    // Check that required HTML elements exist
    if (!newsInput || !result || !checkButton) {
        console.error("VERITAS AI: Required HTML elements were not found.");
        return;
    }


    // ============================================
    // HTML ESCAPE FUNCTION
    // ============================================

    function escapeHTML(value) {
        if (value === null || value === undefined) {
            return "";
        }

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    // ============================================
    // CHECK NEWS
    // ============================================

    async function checkNews() {

        const news = newsInput.value.trim();

        // Empty input
        if (!news) {
            result.innerHTML = `
                <div class="result-card error-card">
                    <div class="prediction">
                        Please enter some news text.
                    </div>
                </div>
            `;
            return;
        }


        // Disable button while checking
        checkButton.disabled = true;
        checkButton.textContent = "Analyzing...";


        // Loading message
        result.innerHTML = `
            <div class="result-card loading-card">
                <div class="prediction">
                    ANALYZING
                </div>

                <div class="explanation">
                    Verifying this claim with AI...
                    <br><br>
                    Please wait.
                </div>
            </div>
        `;


        try {

            console.log("Sending news to /predict...");


            const response = await fetch("/predict", {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    news: news
                })
            });


            console.log("Server response:", response.status);


            // Try to read JSON
            let data;

            try {
                data = await response.json();
            } catch (jsonError) {

                console.error("Could not read JSON response:", jsonError);

                result.innerHTML = `
                    <div class="result-card error-card">
                        <div class="prediction">
                            ERROR
                        </div>

                        <div class="explanation">
                            The server returned an invalid response.
                        </div>
                    </div>
                `;

                return;
            }


            console.log("VERITAS AI result:", data);


            // Server error
            if (!response.ok || data.error) {

                result.innerHTML = `
                    <div class="result-card error-card">

                        <div class="prediction">
                            ERROR
                        </div>

                        <div class="explanation">
                            ${escapeHTML(
                                data.error || "An unexpected server error occurred."
                            )}
                        </div>

                    </div>
                `;

                return;
            }


            // ============================================
            // GET RESULT DATA
            // ============================================

            const prediction =
                data.prediction || "UNCERTAIN";

            const confidence =
                data.confidence !== undefined &&
                data.confidence !== null
                    ? data.confidence
                    : 0;

            const explanation =
                data.explanation ||
                data.message ||
                "No explanation was provided.";


            const sourceName =
                data.source_name ||
                data.sourceName ||
                "";

            const sourceURL =
                data.source_url ||
                data.sourceURL ||
                "";


            // ============================================
            // PREDICTION CLASS
            // ============================================

            let predictionClass = "uncertain";

            const predictionUpper =
                String(prediction).toUpperCase();


            if (predictionUpper.includes("REAL")) {
                predictionClass = "real";
            }

            else if (predictionUpper.includes("FAKE")) {
                predictionClass = "fake";
            }

            else {
                predictionClass = "uncertain";
            }


            // ============================================
            // SOURCE SECTION
            // ============================================

            let sourceHTML = "";


            if (sourceURL) {

                sourceHTML = `
                    <div class="source-box">

                        <h3>Verified Source</h3>

                        ${
                            sourceName
                                ? `<p><strong>${escapeHTML(sourceName)}</strong></p>`
                                : ""
                        }

                        <a
                            href="${escapeHTML(sourceURL)}"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="source-link"
                        >
                            🔗 View Source
                        </a>

                    </div>
                `;

            } else {

                sourceHTML = `
                    <div class="source-box">

                        <h3>Source</h3>

                        <p>
                            No source link was provided by the AI.
                        </p>

                    </div>
                `;
            }


            // ============================================
            // DISPLAY RESULT
            // ============================================

            result.innerHTML = `

                <div class="result-card">

                    <div class="prediction ${predictionClass}">
                        ${escapeHTML(prediction)}
                    </div>


                    <div class="confidence">

                        Confidence:
                        <strong>
                            ${escapeHTML(confidence)}%
                        </strong>

                    </div>


                    <div class="explanation">

                        <h3>AI Explanation</h3>

                        <p>
                            ${escapeHTML(explanation)}
                        </p>

                    </div>


                    ${sourceHTML}

                </div>

            `;


        } catch (error) {

            console.error("VERITAS AI error:", error);


            result.innerHTML = `
                <div class="result-card error-card">

                    <div class="prediction">
                        ERROR
                    </div>

                    <div class="explanation">
                        Could not connect to the AI server.
                        <br><br>
                        Make sure <strong>python app.py</strong>
                        is running.
                    </div>

                </div>
            `;

        } finally {

            // Enable button again
            checkButton.disabled = false;
            checkButton.textContent = "Analyze With AI";

        }

    }


    // ============================================
    // BUTTON
    // ============================================

    checkButton.addEventListener("click", checkNews);


    // ============================================
    // CTRL + ENTER
    // ============================================

    newsInput.addEventListener("keydown", (event) => {

        if (event.ctrlKey && event.key === "Enter") {
            checkNews();
        }

    });


    console.log("VERITAS AI frontend loaded successfully.");

});