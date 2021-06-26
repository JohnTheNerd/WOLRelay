
function loadData() {
  let refreshButton = document.getElementById('refreshButton');
  if (refreshButton) {
      refreshButton.classList.add("fa-spin");
      refreshButton.parentElement.setAttribute('onclick','void()');
  }


  var xmlHTTP = new XMLHttpRequest();
  xmlHTTP.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
    let table = document.createElement('table');
    let tableBody = document.createElement('tbody');
    let response = JSON.parse(xmlHTTP.responseText);
    let macColumn = document.createElement('th');
    let ipColumn = document.createElement('th');
    let timestampColumn = document.createElement('th');
    let actionsColumn = document.createElement('th');
    nameColumn.innerHTML = 'Name';
    macColumn.innerHTML = 'MAC Address';
    ipColumn.innerHTML = 'IP Address';
    timestampColumn.innerHTML = 'Last Seen';
    actionsColumn.innerHTML = '<a href="#" onclick="loadData()"><i class="fas fa-sync" id="refreshButton" title="Refresh list"></i></a>'
    actionsColumn.classList.add("tinyTD");
    // add fa-spin class to item with ID refreshButton
    tableBody.appendChild(nameColumn);
    tableBody.appendChild(macColumn);
    tableBody.appendChild(ipColumn);
    tableBody.appendChild(timestampColumn);
    tableBody.appendChild(actionsColumn);
    for (const id in response) {
      let row = document.createElement('tr');

      let name = response[id]['name'];
      if (name == null) name = "&mdash;";

      let mac = response[id]['mac'];
      if (mac == null) mac = "&mdash;";

      let ip = response[id]['ip'];
      if (ip == null) ip = "&mdash;";

      let lastSeen = response[id]['lastSeen'];
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
            lastSeen = Math.floor(elapsed/1000) + ' seconds ago';   
        }
    
        else if (elapsed < msPerHour) {
            lastSeen = Math.floor(elapsed/msPerMinute) + ' minutes ago';   
        }
    
        else if (elapsed < msPerDay ) {
            lastSeen = Math.floor(elapsed/msPerHour ) + ' hours ago';   
        }
    
        else if (elapsed < msPerMonth) {
            lastSeen = 'approximately ' + Math.floor(elapsed/msPerDay) + ' days ago';   
        }
    
        else if (elapsed < msPerYear) {
            lastSeen = 'approximately ' + Math.floor(elapsed/msPerMonth) + ' months ago';   
        }
    
        else {
            lastSeen = 'approximately ' + Math.floor(elapsed/msPerYear ) + ' years ago';   
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
  };

  xmlHTTP.open("GET", "/status", true);
  xmlHTTP.send();
}

function wakeDevice(mac) {
    if (!mac) {
        macField = document.getElementById('mac');
        mac = macField.value;
    }

    var xmlHTTP = new XMLHttpRequest();   // new HttpRequest instance 
    xmlHTTP.open("POST", "/wake");
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