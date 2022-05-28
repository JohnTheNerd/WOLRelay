
function loadData() {
  let refreshButton = document.getElementById('refreshButton');
  if (refreshButton) {
      refreshButton.classList.add("fa-spin");
      refreshButton.parentElement.setAttribute('onclick','void()');
  }

  var xmlHTTP = new XMLHttpRequest();
  xmlHTTP.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        updateTable(xmlHTTP.responseText);
        setInterval(loadData, 60000);
    }
  };

  xmlHTTP.open("GET", "status", true);
  xmlHTTP.send();
}

function refreshData() {
    let refreshButton = document.getElementById('refreshButton');
    if (refreshButton) {
        refreshButton.classList.add("fa-spin");
        refreshButton.parentElement.setAttribute('onclick','void()');
    }

    var xmlHTTP = new XMLHttpRequest();
    xmlHTTP.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
          updateTable(xmlHTTP.responseText)
      }
    };

    xmlHTTP.open("POST", "update", true);
    xmlHTTP.send();
}

function updateTable(response) {
    let parsedResponse = JSON.parse(response);
    let table = document.createElement('table');
    let tableBody = document.createElement('tbody');
    let nameColumn = document.createElement('th');
    let macColumn = document.createElement('th');
    let ipColumn = document.createElement('th');
    let timestampColumn = document.createElement('th');
    let actionsColumn = document.createElement('th');
    nameColumn.innerHTML = 'Name';
    macColumn.innerHTML = 'MAC Address';
    ipColumn.innerHTML = 'IP Address';
    timestampColumn.innerHTML = 'Last Seen';
    actionsColumn.innerHTML = '<a href="#" onclick="refreshData()"><i class="fas fa-sync" id="refreshButton" title="Refresh list"></i></a>'
    actionsColumn.classList.add("tinyTD");
    // add fa-spin class to item with ID refreshButton
    tableBody.appendChild(nameColumn);
    tableBody.appendChild(macColumn);
    tableBody.appendChild(ipColumn);
    tableBody.appendChild(timestampColumn);
    tableBody.appendChild(actionsColumn);
    for (const id in parsedResponse) {
        let row = document.createElement('tr');

        let name = parsedResponse[id]['name'];
        if (name == null) name = "&mdash;";

        let mac = parsedResponse[id]['mac'];
        if (mac == null) mac = "&mdash;";

        let ip = parsedResponse[id]['ip'];
        if (ip == null) ip = "&mdash;";

        let lastSeen = parsedResponse[id]['lastSeen'];
        if (lastSeen == null) lastSeen = "&mdash;";
        else {

        parsedLastSeen = Date.parse(lastSeen);
        currentDate = Date.now();

        const msPerMinute = 60 * 1000;
        const msPerHour = msPerMinute * 60;
        const msPerDay = msPerHour * 24;
        const msPerMonth = msPerDay * 30;
        const msPerYear = msPerDay * 365;
    
        var elapsed = currentDate - parsedLastSeen;

        if (elapsed < msPerMinute) {
            lastSeen = 'Just now';
        }
    
        else if (elapsed < msPerHour) {
            if (Math.floor(elapsed/msPerMinute) == 1) {
                lastSeen = Math.floor(elapsed/msPerMinute) + ' minute ago';
            }
            else lastSeen = Math.floor(elapsed/msPerMinute) + ' minutes ago';
        }
    
        else if (elapsed < msPerDay ) {
            if (Math.floor(elapsed/msPerHour) == 1) {
                lastSeen = Math.floor(elapsed/msPerHour ) + ' hour ago';
            }
            else lastSeen = Math.floor(elapsed/msPerHour ) + ' hours ago';
        }
    
        else if (elapsed < msPerMonth) {
            if (Math.floor(elapsed/msPerDay) == 1) {
                lastSeen = 'approximately ' + Math.floor(elapsed/msPerDay) + ' day ago';
            }
            else lastSeen = 'approximately ' + Math.floor(elapsed/msPerDay) + ' days ago';
        }
    
        else if (elapsed < msPerYear) {
            if (Math.floor(elapsed/msPerMonth) == 1) {
                lastSeen = 'approximately ' + Math.floor(elapsed/msPerMonth) + ' month ago';
            }
            else lastSeen = 'approximately ' + Math.floor(elapsed/msPerMonth) + ' months ago';
        }
    
        else {
            if (Math.floor(elapsed/msPerYear) == 1) {
                lastSeen = 'approximately ' + Math.floor(elapsed/msPerYear) + ' year ago';
            }
            else lastSeen = 'approximately ' + Math.floor(elapsed/msPerYear ) + ' years ago';
        }
        }

        var cell = document.createElement('td');
        cell.innerHTML = name;
        row.appendChild(cell);
        var cell = document.createElement('td');
        cell.innerHTML = mac;
        row.appendChild(cell);
        var cell = document.createElement('td');
        cell.innerHTML = ip;
        row.appendChild(cell);
        var cell = document.createElement('td');
        cell.innerHTML = lastSeen;
        row.appendChild(cell);
        var cell = document.createElement('td');
        cell.innerHTML = '<a href="#" onclick="wakeDevice(\'' + mac + '\')"><i class="fas fa-power-off" title="Power on"></i></a>';
        cell.classList.add("tinyTD");
        row.appendChild(cell);

        tableBody.appendChild(row);
    }
    table.appendChild(tableBody);
    table.id = 'deviceTable';
    oldTable = document.getElementById('deviceTable');
    oldTable.parentNode.replaceChild(table, oldTable);
    document.getElementById('deviceSection').style.display = 'block';
}

function wakeDevice(mac) {
    if (!mac) {
        macField = document.getElementById('mac');
        mac = macField.value;
    }

    var xmlHTTP = new XMLHttpRequest();   // new HttpRequest instance 
    xmlHTTP.open("POST", "wake");
    xmlHTTP.setRequestHeader("Content-Type", "application/json");
    xmlHTTP.send(JSON.stringify({"mac": mac}));

}

function powerButtonPressed() {
    // this awful method was created because I cannot have FontAwesome icons in a submit button
    // we call reportValidity() because it will first trigger the form validation inside the browser
    // if it fails, it will tell the user why it failed
    // if it succeeds, it will return true and we can safely call wakeDevice()
    let result = document.forms['manualWakeForm'].reportValidity();
    if (result == true) {
        wakeDevice();
    }
}

loadData();