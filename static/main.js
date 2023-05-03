
const button = document.getElementById("create-task");
button.addEventListener("click", () => {
    const formText = document.getElementById("task-description").value;
    var data = { "description": formText, "status": "Draft" }
    fetch("http://127.0.0.1:8000/tasks", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
    })
        .then(response => response.json())
        .then(json => {

            // Create a variable to store HTML
            let li = ``;
            li += `<td>${json.description} </td>
<td>${json.status}</td>`;

            // Display result
            document.getElementById("tasks").innerHTML = li;
        });
});

// 