import argparse
import datetime
import json
import typing as t

import jinja2
from psnawp_api import PSNAWP

TEMPLATE = """<!DOCTYPE html>
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
  <h1>Top PlayStation Games by Play Duration - {{ total_time }}</h1>
  <div class="chart-container">
    <svg style="width: 100%; height: auto;"></svg>
  </div>
  <script>
    let data = {{ data }};
    data = data.map(x => ({title: x.title, count: x.count, duration: x.duration / 3600}));

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
      .domain([0, d3.max(data, d => d.duration)])
      .range([0, width]);

    const color = d3.scaleLinear()
      .domain([
        0,
        d3.max(data, d => d.duration) * 0.33,
        d3.max(data, d => d.duration) * 0.66,
        d3.max(data, d => d.duration)
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

    chart.selectAll(".bar").data(data).enter()
      .append("rect")
      .attr("class", "bar")
      .attr("y", d => y(d.title))
      .attr("height", y.bandwidth())
      .attr("x", 0)
      .attr("width", 0)
      .attr("fill", d => color(d.duration))
      .transition()
      .duration(800)
      .attr("width", d => x(d.duration));

    chart.selectAll(".label").data(data).enter()
      .append("text")
      .attr("x", 0)
      .transition()
      .duration(800)
      .attr("x", d => x(d.duration) + 5)
      .attr("y", d => y(d.title) + y.bandwidth() / 2)
      .attr("dy", ".35em")
      .text(d => `${d.duration.toFixed(1)}h (${d.count}×)`);
  </script>
</body>
</html>"""  # noqa:E501


class Stat(t.NamedTuple):
    title: str
    count: int
    duration: int


def make_stat(source=None):
    if not source:
        return Stat(title="", count=0, duration=0)

    return Stat(
        title=source.name,
        count=source.play_count,
        duration=source.play_duration.total_seconds(),
    )


def load_stats(psn: PSNAWP, limit=None) -> list[Stat]:
    user, stats_merge = psn.me(), {}
    for stat_obj in user.title_stats():
        stat = make_stat(stat_obj)
        stat_merge = stats_merge.get(stat.title, make_stat())
        stats_merge[stat.title] = Stat(
            title=stat.title,
            count=stat.count + stat_merge.count,
            duration=stat.duration + stat_merge.duration,
        )

    stats = list(stats_merge.values())
    stats.sort(key=lambda s: s.duration, reverse=True)

    if limit:
        return stats[:limit]

    return stats


def aggregate_total(stats: list[Stat]) -> tuple[int, int]:
    count, time = 0, 0
    for stat in stats:
        count += stat.count
        time += stat.duration

    return count, time


def main():
    parser = argparse.ArgumentParser(description="PSN Game stats")
    parser.add_argument(
        "token",
        help="PSN API token, you can take it there http://ca.account.sony.com/api/v1/ssocookie",
    )
    parser.add_argument("-l", "--limit", help="Takes top X games", default=100)
    parser.add_argument(
        "-o", "--output", help="Output file name", default="./index.html"
    )
    args = parser.parse_args()

    psn = PSNAWP(args.token)
    stats = load_stats(psn, args.limit)
    total_count, total_sec = aggregate_total(stats)

    with open(args.output, "w", encoding="utf-8") as f:
        context = {
            "data": json.dumps(tuple(x._asdict() for x in stats)),
            "total_count": total_count,
            "total_time": datetime.timedelta(seconds=total_sec),
        }
        f.write(jinja2.Template(TEMPLATE).render(context))


if __name__ == "__main__":
    main()
