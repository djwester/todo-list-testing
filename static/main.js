
const addbutton = document.getElementById("create-task");
const url = "http://127.0.0.1:8000/tasks";

addbutton.addEventListener("click", () => {
    const formText = document.getElementById("task-description").value;
    var data = { "description": formText, "status": "Draft" }
    fetch(url, {
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
        li +=`<tr>`;
        li += `<td>${json.description} </td>`;
        li += `<td>${json.status}</td>`;
        li +=`<td>
            <small>
                <button id="${json.id}" type="button" class=".edit-task">Edit</button>
                <a href="${url}/tasks/${json.id}">Edit</a>
                <a href="delete/${json.id}">Delete</a>
            </small>
        </td>`;
        li += `</tr>`;

        // Display result
        document.getElementById("tasks").innerHTML += li;
    });
    
});

document.addEventListener("DOMContentLoaded", () => {
    fetch(url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(response => response.json())
    .then(json => {
        let table_rows = ``;
        for (var i = 0; i < json.length; i++) {
            // Create a variable to store HTML
            task = json[i]
            let li = ``;
            li +=`<tr>`;
            li += `<td name="description_${task.id}">${task.description} </td>`;
            li += `<td>${task.status}</td>`;
            li +=`<td>
                <small>
                    <button id="${task.id}" type="button" class="edit-task" description="${task.description}">Edit</button>
                    <button id="${task.id}" type="button" class="delete-task">Delete</button>
                </small>
            </td>`;
            li += `</tr>`;
            table_rows += li;
        }

        // Display result
        document.getElementById("tasks").innerHTML += table_rows;
    })
    .then( () => {
        document.querySelectorAll(".edit-task").forEach(item => {
            item.addEventListener("click", editTask)
        })
        document.querySelectorAll(".delete-task").forEach(item => {
            item.addEventListener("click", deleteTask)
        })
    });
});

function deleteTask(event) {
    const taskId = event.currentTarget.id
    const taskUrl = `${url}/${taskId}`
    fetch(taskUrl, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json"
        },
    });
}
function editTask (event) {

    const taskId = event.currentTarget.id
    let taskDescription = event.currentTarget.getAttribute("description")
    const taskUrl = `${url}/${taskId}`
    
    let description = window.prompt("Edit the task",taskDescription)
    console.log(description)
    const data = {"description": description, "status": "Draft" }
    fetch(taskUrl, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
    })
    .then(description => {
        taskDescription = description
        description_element = document.getElementsByName(`description_${taskId}`)
        description_element.value = description;
    })
}