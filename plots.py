# https://plot.ly/python/map-configuration/
# https://plot.ly/python/choropleth-maps/

import sys, time, re
from pathlib import Path
from io import StringIO

import plotly.graph_objects as go
import plotly.express as px
from pandas import DataFrame

import stats


def write_map(outfile, data):
    names, codes, cases, densities = zip(*data)
    df = DataFrame(dict(iso_alpha=codes,
                        cases=cases,
                        density=densities,
                        country=names))

    #print(sorted(data, key=lambda r: r[3]))

    fig = px.choropleth(
        df,
        locations="iso_alpha",
        color="density",
        hover_name="country",
        height=1000,
        color_continuous_scale=px.colors.sequential.YlOrRd)

    fig.write_html(file=outfile, full_html=False, auto_open=False)


def make_map(data):
    # outfile = Path(__file__).parent / "map.html"
    # with outfile.open("w") as f:
    #     write_map(f, data)

    buf = StringIO()
    write_map(buf, data)
    return buf.getvalue()


def process_template(template, outfile, replacements):
    if isinstance(replacements, dict):
        replacements = replacements.items()
    line_map = {f"<!-- INSERT {rid.upper()} -->\n": data
                for rid, data in replacements}
    for line in template:
        if line in line_map:
            outfile.write(line_map[line])
        else:
            outfile.write(line)


def collect_data():
    excluded_countries=[     # extreme outliers throwing off the scale
        "San Marino",
    ]

    exclude_set = set(excluded_countries)
    data = list(r for r in stats.case_density()
                if r[0] not in excluded_countries)
    return data


def main():
    map_data = make_map(collect_data())

    replacements = {
        "map": map_data,
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if len(sys.argv) == 1:
        process_template(sys.stdin, sys.stdout, replacements)
    elif len(sys.argv) == 2:
        with open(sys.argv[1], "r") as f:
            process_template(f, sys.stdout, replacements)
    else:
        raise Exception("Bad argument count")


if __name__ == "__main__":
    main()
