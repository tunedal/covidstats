# https://plot.ly/python/map-configuration/
# https://plot.ly/python/choropleth-maps/

import sys, time, re
from pathlib import Path
from io import StringIO
from math import log10

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from pandas import DataFrame

import stats, readers


def write_map(outfile, data):
    names, codes, cases, densities = zip(*data)
    df = DataFrame(dict(iso_alpha=codes,
                        cases=cases,
                        density=densities,
                        country=names))

    #print(sorted(data, key=lambda r: r[3]))

    # For clarity, clip color values to 150% of the PRC value
    # and use a logarithmic scale.
    prc_density = next(density for name, code, case, density in data
                       if name == "China")
    min_density = min(density for name, code, case, density in data)
    clip_max = prc_density * 1.5
    color_data = np.log10(np.clip(df["density"], min_density, clip_max))

    # TODO: How can I use hovertemplate here?
    fig = px.choropleth(
        df,
        locations="iso_alpha",
        color=color_data,
        hover_name="country",
        hover_data=["cases", "density"],
        labels={"cases": "Confirmed cases",
                "density": "Cases per million",
                "iso_alpha": "Country code",
                "color": "Color value"},
        height=1000,
        color_continuous_scale=px.colors.sequential.YlOrRd,
    )

    tick_count = 10
    tick_step = (log10(clip_max) - log10(min_density)) / (tick_count - 1)
    ticks = [log10(min_density) + tick_step * i
             for i in range(tick_count)]

    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Cases/million",
            tickvals=ticks,
            ticktext=[f"{10**x:.2f}" for x in ticks],
        ))

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


def collect_data(data_source):
    excluded_countries=[     # extreme outliers throwing off the scale
        "San Marino",
    ]

    exclude_set = set(excluded_countries)
    data = list(r for r in stats.case_density(data_source)
                if r[0] not in excluded_countries)
    return data


def main():
    data_source = readers.ecdc_source

    args = iter(sys.argv[1:])
    rest_args = []
    for arg in args:
        if arg == "-s":
            data_source = getattr(readers, next(args) + "_source")
        else:
            rest_args.append(arg)


    map_data = make_map(collect_data(data_source))

    replacements = {
        "map": map_data,
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if len(rest_args) == 0:
        process_template(sys.stdin, sys.stdout, replacements)
    elif len(rest_args) == 1:
        with open(rest_args[0], "r") as f:
            process_template(f, sys.stdout, replacements)
    else:
        raise Exception("Bad argument count")


if __name__ == "__main__":
    main()
