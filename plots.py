# https://plot.ly/python/map-configuration/
# https://plot.ly/python/choropleth-maps/

import plotly.graph_objects as go
import plotly.express as px
from pandas import DataFrame

import stats


def plot_stats_on_map(excluded_countries=[]):
    excluded_countries = set(excluded_countries)

    data = list(r for r in stats.case_density()
                if r[0] not in excluded_countries)
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
        color_continuous_scale=px.colors.sequential.YlOrRd)
    fig.show()


if __name__ == "__main__":
    excluded_countries=[     # extreme outliers throwing off the scale
        "San Marino",
    ]
    plot_stats_on_map(excluded_countries)

