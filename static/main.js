
const addbutton = document.getElementById("create-task");
const loginbutton = document.getElementById("login");
const logoutbutton = document.getElementById("logout")
const protocol = window.location.protocol;
const host = window.location.host;
const base_url = `${protocol}//${host}`;
const url = `${base_url}/tasks`;

function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    let expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

async function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
}

function delete_cookie( name ) {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

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
    var token = get_token();
    token.then(token => {
        fetch(`${base_url}/user/me`,{
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(json => {
            if (json.username){
                var username = json.username;
            } else {
                var username = "anonymous"
            }
            document.getElementById("username_label").innerHTML = `Username: ${username}`;
        })
    });
    
    document.getElementById("tasks").innerHTML += table_rows;
    document.querySelectorAll(".edit-task").forEach(item => {
        item.addEventListener("click", editTask)
    })
    document.querySelectorAll(".delete-task").forEach(item => {
        item.addEventListener("click", deleteTask)
    })
}

logoutbutton.addEventListener("click", () => {
    delete_cookie("todo_token")
    document.getElementById("username_label").innerHTML = "Username: anonymous";
    // hack to "refresh" and thus clear the cookie
    fetch(url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
    })
})

async function get_token() {
    var token = await getCookie("todo_token")
    if (token == "") {
        const data = new URLSearchParams({
            "username": "anonymous",
            "password": "12345"
        });
        const response = await fetch(`${base_url}/token`, {
            method: "POST",
            body: data,
        })
        const json = await response.json();
        token = json.access_token;
        return token
    } else {
        return token
    }
}

addbutton.addEventListener("click", () => {
    const formText = document.getElementById("task-description").value;
    token = get_token();
    token.then(token => {
        fetch(`${base_url}/user/me`,{
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(json => {
            if (json.username){
                var user = json.username;
            } else {
                var user = "anonymous"
            }
            var data = { "description": formText, "status": "Draft", "created_by": user}
            fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(json => renderPage([json]));
        })
    })
});

loginbutton.addEventListener("click", () => {
    const username = document.getElementsByName("uname")[0].value;
    const password = document.getElementsByName("psw")[0].value;
    const data = new URLSearchParams({
        "username": username,
        "password": password
    });
    fetch(`${base_url}/token`, {
        method: "POST",
        body: data,
    })
    .then(response => response.json())
    .then(json => {
        const token = json.access_token;
        setCookie("todo_token", token, 30);
        document.getElementById('id01').style.display='none';
        document.getElementById("username_label").innerHTML = `Username: ${username}`;
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
    .then(json => renderPage(json))
})

function deleteTask(event) {
    const taskId = event.currentTarget.id
    const taskUrl = `${url}/${taskId}`
    token = get_token();
    token.then(token => {
        fetch(taskUrl, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
        })
        .then(response => {
            if (!response.ok) {
                return ""
            }
            response.json()
        })
        .then(json => {
            console.log(json)
            if (json != ""){
                var rows = document.getElementsByTagName("tr");
                for (const row in rows){
                    if (rows[row].id == taskId) {
                        document.getElementById("tasks").deleteRow(row)
                    }
                    
                }
            }
        });
    })
}

function editTask (event) {

    const taskId = event.currentTarget.id
    let taskDescription = event.currentTarget.getAttribute("description")
    const taskUrl = `${url}/${taskId}`
    
    let description = window.prompt("Edit the task",taskDescription)
    // TODO handle canceling on the prompt
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