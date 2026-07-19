"use strict";

let lastEventCount = 0;

function setStatus(elementId, text, className){
    const element = document.getElementById(elementId);

    element.textContent = text;
    element.className = className;
}

function getEventClass(type){
    switch(type){
        case "ALLOW":
            return "status-green";

        case "BLOCK":
            return "status-red";

        case "REDIS_LOST":
            return "status-red";

        case "REDIS_RESTORED":
            return "status-green";

        case "FALLBACK_ENABLED":
            return "status-yellow";

        case "FALLBACK_DISABLED":
            return "status-green";

        default:
            return "status-muted";
    }
}

async function loadHealth() {
    try{
        const response = await fetch("/api/rate-limit/health");
        const data = await response.json();

        setStatus(
            "status",
            data.status.toUpperCase(),
            data.status === "healthy" ? "status-green" : "status-red"
        );

        setStatus(
            "redis-status",
            data.redis_available ? "ONLINE" : "OFFLINE",
            data.redis_available ? "status-green" : "status-red"
        );

        setStatus(
            "fallback-status",
            data.fallback_active ? "ENABLED" : "DISABLED",
            data.fallback_active ? "status-yellow" : "status-green"
        );

        setStatus(
            "active-limiter",
            data.active_limiter.toUpperCase(),
            data.active_limiter === "redis" ? "status-cyan" : "status-yellow"
        );

        setStatus(
            "algorithm",
            data.algorithm.toUpperCase(),
            "status-muted"
        );
    }

    catch(error){
        console.error("unable to fetch health data.", error);
    }
}

function formatUptime(seconds){
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return `${hours}h ${minutes}m ${secs}s`;

}

function loadStats(data){
    try{
        document.getElementById("total-requests").textContent = data.total_requests;
        
        document.getElementById("allowed-requests").textContent = data.allowed_requests;
        
        document.getElementById("blocked-requests").textContent = data.blocked_requests;
        
        document.getElementById("redis-requests").textContent = data.redis_requests;
        
        document.getElementById("memory-requests").textContent = data.memory_requests;

        document.getElementById("uptime").textContent = formatUptime(data.uptime);        
        
    }
    catch(error){
        console.error("unable to fetch stats", error);
    }
}

function loadEndpoints(data){
    try{
        const container = document.getElementById("endpoint-container");

        container.innerHTML = "";

        const endpoints = Object.entries(data.endpoint_requests);
        endpoints.sort((a, b) => b[1] - a[1]);
        for (const [path, count] of endpoints) {
            const row = document.createElement("div");

            row.className = "endpoint-row";
            row.innerHTML = `
                <span class="endpoint-path">${path}</span>
                <span class="endpoint-count">${count}</span>
            `;
            container.appendChild(row);
        }
    }

    catch(error){
        console.error("Unable to load endpoint statistics.", error);
    }
}

function loadTraffic(data){

    const grid = document.getElementById("traffic-grid");

    grid.innerHTML = "";

    const MAX_HISTORY = 100;
    const history = data.request_history.slice(-MAX_HISTORY);

    //fill cells as per teh request.
    history.forEach((request,index) => {
        const cell = document.createElement("div");

        if(request.allowed){
            cell.className = "traffic-cell allowed";
        }
        else{
            cell.className = "traffic-cell blocked"
        }

        const opacity = 
            history.length === 0 ? 1 : 0.5 + (0.65 * (index + 1) / history.length);
        cell.style.opacity = opacity;

        cell.title = `
            ${request.allowed ? "Allowed" : "Blocked"}
            ${request.path}
            ${request.timestamp}        
        `;
        grid.appendChild(cell);
    });

    const remaining = MAX_HISTORY - history.length;
    
     for(let i = 0; i < remaining; i++){
        const cell = document.createElement("div");
        cell.className = "traffic-cell";
        grid.appendChild(cell);
    }
}

async function loadEvents() {
    try{
        const response = await fetch("/api/rate-limit/events");
        const data = await response.json();
        if (data.events.length === lastEventCount) {
            return;
        }
        lastEventCount = data.events.length;

        const container = document.getElementById("events-container");

        container.innerHTML = "";

        data.events.slice().reverse().forEach(event => {

            const eventElement = document.createElement("div");
            eventElement.className = "event";
            eventElement.innerHTML = `
                <span class="event-time">${event.timestamp}</span>
                <span class="event-type ${getEventClass(event.type)}">${event.type}</span>
                <span class="event-path">${event.path ?? "-"}</span>
            `
            container.appendChild(eventElement);
        });
    }
    catch(error){
        console.error("unable to fetch stats", error);
    }
}

async function loadConfig() {
    const response = await fetch("/api/rate-limit/config/");
    const data = await response.json();

    const container = document.getElementById("config-container");

    let html = `
        <table>
            <thead>
                <tr>
                    <th> Routes </th>
                    <th> Capacity </th>
                    <th> Refill Rate </th>
                </tr>
            </thead>
            <tbody>
    `;

    for(const [route, config] of Object.entries(data.routes)){
        html +=  `
        <tr>
            <td> ${route} </td>
            <td> ${config.capacity} </td>
            <td> ${config.refill_rate} </td>
        `;
    }

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

async function refreshDashboard() {
    await loadHealth();
    
    const response = await fetch("/api/rate-limit/stats/");
    const stats = await response.json();

    loadStats(stats);
    loadEndpoints(stats);
    loadTraffic(stats);
    await loadEvents();
    await loadConfig();
}

refreshDashboard();

setInterval(refreshDashboard, 2000);