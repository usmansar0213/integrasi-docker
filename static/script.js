// Navigation
document.querySelectorAll(".next").forEach((button) => {
    button.addEventListener("click", () => {
        const currentStep = document.querySelector(".step.active");
        currentStep.classList.remove("active");

        const nextStep = document.getElementById(button.dataset.next);
        nextStep.classList.add("active");
    });
});

document.getElementById("upload-form").addEventListener("submit", (e) => {
    e.preventDefault();

    const fileInput = document.getElementById("file");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a file to upload.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    fetch("/upload", {
        method: "POST",
        body: formData,
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                // Show variable selection section
                document.getElementById("variable-selection").style.display = "block";

                // Populate dropdown for Dependent Variable
                const dependentDropdown = document.getElementById("dependent-variable");
                dependentDropdown.innerHTML = ""; // Clear previous options
                data.columns.forEach((col) => {
                    const option = document.createElement("option");
                    option.value = col;
                    option.textContent = col;
                    dependentDropdown.appendChild(option);
                });

                // Populate checkboxes for Independent Variables
                const independentContainer = document.getElementById("independent-variables-container");
                independentContainer.innerHTML = ""; // Clear previous checkboxes

                data.columns.forEach((col) => {
                    const checkboxHTML = `
                        <div>
                            <input type="checkbox" id="${col}" name="independent-variables" value="${col}">
                            <label for="${col}">${col}</label>
                        </div>
                    `;
                    independentContainer.insertAdjacentHTML("beforeend", checkboxHTML);
                });
            }
        })
        .catch((error) => {
            console.error("Fetch error:", error);
            alert("An error occurred during the upload.");
        });
});

// Handle Next Step Button Click
document.getElementById("next-step").addEventListener("click", () => {
    const dependentVariable = document.getElementById("dependent-variable").value;
    const independentVariables = Array.from(
        document.querySelectorAll("input[name='independent-variables']:checked")
    ).map((checkbox) => checkbox.value);

    if (!dependentVariable) {
        alert("Please select a dependent variable.");
        return;
    }

    if (independentVariables.length === 0) {
        alert("Please select at least one independent variable.");
        return;
    }

    console.log("Dependent Variable:", dependentVariable);
    console.log("Independent Variables:", independentVariables);

    // Proceed to next step or send data to server
});




// Run simulation
document.getElementById("run-simulation").addEventListener("click", () => {
    const dependent = document.getElementById("dependent-variable").value;
    const independents = Array.from(
        document.getElementById("independent-variables").selectedOptions
    ).map((opt) => opt.value);

    fetch("/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dependent_variable: dependent, independent_variables: independents }),
    })
        .then((response) => response.json())
        .then((data) => {
            document.getElementById("simulation-results").innerText = `Mean: ${data.mean_prediction}, Std Dev: ${data.std_dev}`;
        });
});
