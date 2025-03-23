from psnawp_api import PSNAWP
import os
from jinja2 import Template
import json
from collections import defaultdict

# Initialize PSNAWP with your authentication token
# Use an environment variable or secure method instead of hardcoding the token
# http://ca.account.sony.com/api/v1/ssocookie

auth_token = os.getenv("PSN_AUTH_TOKEN", "YOUR_TOKEN_HERE")
psnawp = PSNAWP(auth_token)

def load_title_stats():
    bg_user = psnawp.me()
    stasian_user = psnawp.user(online_id='stasian88')

    bg_stats = list(bg_user.title_stats())
    stasian_stats = list(stasian_user.title_stats())

    filtered_stasian = [
        title for title in stasian_stats
        if title.title_id not in ['CUSA01116_00', 'CUSA02012_00', 'PPSA01651_00']
    ]

    bg_stats.sort(key=lambda title: title.play_duration, reverse=True)
    filtered_stasian.sort(key=lambda title: title.play_duration, reverse=True)

    return filtered_stasian, bg_stats

def prepare_aggregated_data(stasian_stats, bg_stats):
    aggregated_stats = defaultdict(lambda: {'play_count': 0, 'play_duration': 0.0})
    collect_stats(stasian_stats[:1000], aggregated_stats)
    collect_stats(bg_stats, aggregated_stats)
    return aggregated_stats

def collect_stats(titles, aggregated_stats):
    for title in titles:
        game_name = getattr(title, 'name', f"Unknown ({title.title_id})")
        hours = title.play_duration.total_seconds() / 3600
        aggregated_stats[game_name]['play_count'] += title.play_count
        aggregated_stats[game_name]['play_duration'] += hours

stasian_titles, bg_titles = load_title_stats()
aggregated_stats = prepare_aggregated_data(stasian_titles, bg_titles)

total_hours = sum(stats['play_duration'] for stats in aggregated_stats.values())
total_days = total_hours / 24
header_text = f"Top Games by Play Duration — {total_hours:.1f} hours ({total_days:.1f} days)"

merged_title_data = [
    {'title': name, 'play_count': stats['play_count'], 'play_duration': stats['play_duration']}
    for name, stats in aggregated_stats.items()
]
merged_title_data.sort(key=lambda x: x['play_duration'], reverse=True)

html_template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Top PlayStation Games</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    body {
      font-family: 'Inter', sans-serif;
      padding: 40px;
      background: linear-gradient(to bottom, #f0f2f5, #ffffff);
      color: #333;
    }
    h2 {
      text-align: center;
      margin-bottom: 40px;
      color: #222;
      font-size: 24px;
    }
    svg {
      font: 11px 'Inter', sans-serif;
    }
    .bar {
      rx: 5;
      ry: 5;
      transition: all 0.25s ease;
    }
    .bar:hover {
      opacity: 0.8;
      cursor: pointer;
    }
    .label {
      font-size: 11px;
      fill: #222;
      font-weight: 600;
    }
    .axis-label {
      font-weight: 500;
    }
    .chart-container {
      background: white;
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      max-width: 1000px;
      margin: 0 auto;
    }
  </style>
</head>
<body>
  <h2>{{ header }}</h2>
  <div class="chart-container">
    <svg style="width: 100%; height: auto;"></svg>
  </div>
  <script>
    const data = {{ data|safe }}.sort((a, b) => b.play_duration - a.play_duration).slice(0, 1000);

    const margin = { top: 20, right: 200, bottom: 10, left: 300 },
          containerWidth = document.querySelector(".chart-container").clientWidth;
    const width = containerWidth - margin.left - margin.right,
          barHeight = 20,
          height = barHeight * data.length;

    const svg = d3.select("svg")
      .attr("height", height + margin.top + margin.bottom);

    const chart = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.play_duration)])
      .range([0, width]);

    const color = d3.scaleLinear()
      .domain([
        0,
        d3.max(data, d => d.play_duration) * 0.33,
        d3.max(data, d => d.play_duration) * 0.66,
        d3.max(data, d => d.play_duration)
      ])
      .range(["green", "yellow", "orange", "red"]);

    const y = d3.scaleBand()
      .domain(data.map(d => d.title))
      .range([0, height])
      .padding(0.1);

    chart.append("g")
      .call(d3.axisLeft(y).tickSize(0))
      .selectAll("text")
      .style("font-size", "11px")
      .style("text-anchor", "end");

    chart.append("g")
      .attr("transform", `translate(0,0)`)
      .call(d3.axisTop(x).ticks(10));

    chart.selectAll(".bar")
      .data(data)
      .enter().append("rect")
      .attr("class", "bar")
      .attr("y", d => y(d.title))
      .attr("height", y.bandwidth())
      .attr("x", 0)
      .attr("width", 0)
      .attr("fill", d => color(d.play_duration))
      .transition()
      .duration(800)
      .attr("width", d => x(d.play_duration));

    chart.selectAll(".label")
      .data(data)
      .enter().append("text")
      .attr("x", 0)
      .transition()
      .duration(800)
      .attr("x", d => x(d.play_duration) + 5)
      .attr("y", d => y(d.title) + y.bandwidth() / 2)
      .attr("dy", ".35em")
      .text(d => `${d.play_duration.toFixed(1)}h (${d.play_count}×)`);
  </script>
</body>
</html>
""")

with open("stasian_titles.html", "w", encoding="utf-8") as f:
    f.write(html_template.render(data=json.dumps(merged_title_data), header=header_text))
