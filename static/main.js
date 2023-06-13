
const addbutton = document.getElementById("create-task");
const url = "http://127.0.0.1:8000/tasks";

function renderPage(json) {
        let table_rows = ``;
        for (var i = 0; i < json.length; i++) {
            // Create a variable to store HTML
            var task = json[i]
            let li = ``;
            li +=`<tr id="${task.id}">`;
            li += `<td name="description_${task.id}">${task.description} </td>`;
            li += `<td>
                <div class="dropdown">
                    <button id="statusButton_${task.id}" onclick="getDropdown(${task.id})" class="dropbtn">${task.status}</button>
                    <div id="statusDropdown_${task.id}" class="dropdown-content">
                    <a onclick="setDraft(${task.id})" href="#">Draft</a>
                    <a onclick="setInProgress(${task.id})" href="#">In Progress</a>
                    <a onclick="setComplete(${task.id})" href="#">Complete</a>
                    </div>
                </div>
            </td>`;
            li +=`<td>
                <small>
                    <button name="edit_${task.id}" id="${task.id}" type="button" class="edit-task" description="${task.description}">Edit</button>
                    <button name="delete_${task.id}" id="${task.id}" type="button" class="delete-task">Delete</button>
                </small>
            </td>`;
            li += `</tr>`;
            table_rows += li;
        }

        // Display result
        document.getElementById("tasks").innerHTML += table_rows;
        document.querySelectorAll(".edit-task").forEach(item => {
            item.addEventListener("click", editTask)
        })
        document.querySelectorAll(".delete-task").forEach(item => {
            item.addEventListener("click", deleteTask)
        })
}

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
    .then(json => renderPage([json]));    
});

document.addEventListener("DOMContentLoaded", () => {
    fetch(url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(response => response.json())
    .then(json => renderPage(json))
})

function deleteTask(event) {
    const taskId = event.currentTarget.id
    const taskUrl = `${url}/${taskId}`
    fetch(taskUrl, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json"
        },
    })
    .then(() => {
        var rows = document.getElementsByTagName("tr");
        for (const row in rows){
            if (rows[row].id == taskId) {
                document.getElementById("tasks").deleteRow(row)
            }
            
        }
    });
}

function editTask (event) {

    const taskId = event.currentTarget.id
    let taskDescription = event.currentTarget.getAttribute("description")
    const taskUrl = `${url}/${taskId}`
    
    let description = window.prompt("Edit the task",taskDescription)
    const data = {"description": description, "status": "Draft" }
    fetch(taskUrl, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(json => {
        element_name = `description_${json.id}`
        elem = document.getElementsByName(element_name)[0]
        elem.innerHTML = json.description

        edit_button_name = `edit_${json.id}`
        edit_elem = document.getElementsByName(edit_button_name)[0]
        edit_elem.setAttribute("description", json.description)
       
    });
}

function setInProgress (task_id) {
    taskUrl = `${url}/${task_id}/in-progress`
    data = {}
    fetch(taskUrl, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(json => {
        document.getElementById(`statusButton_${json.id}`).innerHTML="In Progress"
    })
}

function setDraft (task_id) {
    taskUrl = `${url}/${task_id}/draft`
    data = {}
    fetch(taskUrl, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(json => {
        document.getElementById(`statusButton_${json.id}`).innerHTML="Draft"
    })
}

function setComplete (task_id) {
    taskUrl = `${url}/${task_id}/complete`
    data = {}
    fetch(taskUrl, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(json => {
        document.getElementById(`statusButton_${json.id}`).innerHTML="Complete"
    })
}

function getDropdown(task_id) {
    document.getElementById(`statusDropdown_${task_id}`).classList.toggle("show");
  }
  
  // Close the dropdown menu if the user clicks outside of it
  window.onclick = function(event) {
    if (!event.target.matches('.dropbtn')) {
      var dropdowns = document.getElementsByClassName("dropdown-content");
      var i;
      for (i = 0; i < dropdowns.length; i++) {
        var openDropdown = dropdowns[i];
        if (openDropdown.classList.contains('show')) {
          openDropdown.classList.remove('show');
        }
      }
    }
  }