document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('data.json');
        const data = await response.json();
        
        initStats(data.nodes);
        initViz(data);
    } catch (e) {
        console.error("Failed to load data:", e);
    }
});

function initStats(nodes) {
    // Calculate averages
    const bachelors = nodes.filter(n => n.education === "Bachelor's" && n.exposure !== undefined);
    const noDegree = nodes.filter(n => n.education === "No Credential" && n.exposure !== undefined);

    const bAvg = bachelors.length ? (bachelors.reduce((acc, n) => acc + n.exposure, 0) / bachelors.length).toFixed(1) : '--';
    const nAvg = noDegree.length ? (noDegree.reduce((acc, n) => acc + n.exposure, 0) / noDegree.length).toFixed(1) : '--';

    document.getElementById('stat-bachelors').innerText = `${bAvg} Avg Exposure`;
    document.getElementById('stat-nodegree').innerText = `${nAvg} Avg Exposure`;
}

function initViz(data) {
    const container = document.getElementById('chart-container');
    let width = container.clientWidth;
    let height = container.clientHeight;

    const margin = { top: 80, right: 40, bottom: 60, left: 160 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const svg = d3.select("#chart-container")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // X Scale (AI Exposure 0-10)
    const xScale = d3.scaleLinear()
        .domain([0, 10])
        .range([0, innerWidth]);

    // Y Scale (Education Levels)
    // Reverse levels so highest education is at top
    const levels = data.education_levels.map(l => l.label).reverse();
    const yScale = d3.scaleBand()
        .domain(levels)
        .range([0, innerHeight])
        .padding(0.1);

    // Draw background bands
    g.selectAll(".axis-level-bg")
        .data(levels)
        .enter().append("rect")
        .attr("class", "axis-level-bg")
        .attr("y", d => yScale(d))
        .attr("x", -margin.left)
        .attr("width", width)
        .attr("height", yScale.bandwidth());

    // Y Axis (Education)
    g.append("g")
        .call(d3.axisLeft(yScale).tickSize(0).tickPadding(15))
        .selectAll("text")
        .attr("class", "axis-text")
        .style("text-anchor", "end")
        .style("font-weight", "600");
    
    g.select(".domain").remove();

    // X Axis (Exposure)
    const xAxis = g.append("g")
        .attr("transform", `translate(0, ${innerHeight + 20})`)
        .call(d3.axisBottom(xScale).ticks(11));
    
    xAxis.select(".domain").attr("class", "axis-line");
    xAxis.selectAll(".tick line").attr("class", "axis-line");
    xAxis.selectAll("text").attr("class", "axis-text");

    // X Axis Label
    g.append("text")
        .attr("class", "axis-text")
        .attr("x", innerWidth / 2)
        .attr("y", innerHeight + 50)
        .style("text-anchor", "middle")
        .style("font-weight", "600")
        .text("AI Exposure (0 = Safe, 10 = Maximum Risk)");

    // Define simulation forces
    const simulation = d3.forceSimulation(data.nodes)
        .force("x", d3.forceX(d => xScale(d.exposure)).strength(0.8))
        .force("y", d3.forceY(d => {
            const y = yScale(d.education);
            return y !== undefined ? y + yScale.bandwidth()/2 : innerHeight/2;
        }).strength(0.8))
        .force("collide", d3.forceCollide(d => d.radius + 1).iterations(3)); // Prevent overlap

    // Nodes
    const node = g.selectAll(".node")
        .data(data.nodes)
        .enter().append("circle")
        .attr("class", "node")
        .attr("r", d => d.radius)
        .attr("fill", d => d.color)
        .on("mouseenter", showTooltip)
        .on("mouseleave", hideTooltip);

    simulation.on("tick", () => {
        node
            .attr("cx", d => {
                // Keep inside bounds
                d.x = Math.max(d.radius, Math.min(innerWidth - d.radius, d.x));
                return d.x;
            })
            .attr("cy", d => {
                const bandTop = yScale(d.education) || 0;
                const bandBottom = bandTop + yScale.bandwidth();
                d.y = Math.max(bandTop + d.radius, Math.min(bandBottom - d.radius, d.y));
                return d.y;
            });
    });

    // Handle Window Resize
    window.addEventListener('resize', () => {
        width = container.clientWidth;
        height = container.clientHeight;
        svg.attr("width", width).attr("height", height);
        
        const newInnerWidth = width - margin.left - margin.right;
        const newInnerHeight = height - margin.top - margin.bottom;

        xScale.range([0, newInnerWidth]);
        yScale.range([0, newInnerHeight]);

        simulation.force("x", d3.forceX(d => xScale(d.exposure)).strength(0.8))
            .force("y", d3.forceY(d => {
                const y = yScale(d.education);
                return y !== undefined ? y + yScale.bandwidth()/2 : newInnerHeight/2;
            }).strength(0.8));
        
        simulation.alpha(0.3).restart();
    });
}

function showTooltip(event, d) {
    document.getElementById('info-placeholder').style.display = 'none';
    const card = document.getElementById('info-card');
    card.style.display = 'block';

    document.getElementById('info-title').innerText = d.title;
    document.getElementById('info-category').innerText = d.category;
    document.getElementById('info-education').innerText = d.education;
    
    // Format jobs
    let jobsStr = d.jobs.toLocaleString();
    if (d.jobs >= 1000000) {
        jobsStr = (d.jobs / 1000000).toFixed(1) + "M";
    } else if (d.jobs >= 1000) {
        jobsStr = (d.jobs / 1000).toFixed(0) + "K";
    }
    document.getElementById('info-jobs').innerText = jobsStr;
    
    // Format pay
    const payStr = d.pay ? `$${d.pay.toLocaleString()}` : 'N/A';
    document.getElementById('info-pay').innerText = payStr;
    
    document.getElementById('info-rationale-text').innerText = d.rationale;
    
    const exposureBadge = document.getElementById('info-exposure');
    exposureBadge.innerText = `Exposure: ${d.exposure}/10`;
    exposureBadge.style.backgroundColor = d.color;
    // Darken text if bg is bright
    exposureBadge.style.color = d.exposure <= 6 ? '#000' : '#fff';
}

function hideTooltip() {
    // Optionally keep it visible to let users read, or hide.
    // Let's keep it visible so it acts like a sticky sidepanel view.
}
