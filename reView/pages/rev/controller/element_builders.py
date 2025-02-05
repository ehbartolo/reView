# -*- coding: utf-8 -*-
# pylint: disable=consider-using-generator
"""Element builders.

Methods for building html and core component elements given user inputs in
scenario callbacks.

Created on Fri May 20 12:07:29 2022

@author: twillia2
"""
import copy
import datetime as dt
import json
from collections import Counter
from itertools import cycle

import pandas as pd
import numpy as np
import plotly.express as px

from reView.utils.classes import DiffUnitOptions
from reView.utils.config import Config
from reView.utils.constants import DEFAULT_POINT_SIZE, DEFAULT_LAYOUT
from reView.utils.functions import convert_to_title


CHART_LAYOUT = copy.deepcopy(DEFAULT_LAYOUT)
CHART_LAYOUT.update({"legend_title_font_color": "black"})


def _fix_doubles(df):
    """Check and/or fix columns names when they match."""
    if not isinstance(df, pd.core.frame.Series):
        cols = np.array(df.columns)
        counts = Counter(cols)
        for col, count in counts.items():
            if count > 1:
                idx = np.where(cols == col)[0]
                cols[idx[1]] = col + "_2"
        df.columns = cols
    return df


def _is_integer(val):
    """Check if an input value is an integer."""
    try:
        int(val)
        return True
    except ValueError:
        return False


class Plots:
    """Class for handling grouped plots."""

    GROUP = "Scenarios"

    def __init__(
        self,
        project,
        datasets,
        plot_title,
        point_size=DEFAULT_POINT_SIZE,
        user_scale=(None, None),
        alpha=1,
    ):
        """Initialize plotting object for a reV project."""
        self.datasets = datasets
        self.plot_title = plot_title
        self.point_size = point_size
        self.user_scale = user_scale
        self.alpha = alpha
        self.config = Config(project)

    def __repr__(self):
        """Print representation string."""
        return f"<Plots object: project={self.config.project}>"

    # noqa: R0914
    def binned(self, x_var, y_var, bins=100):
        """Return a line plot."""
        # The clustered scatter plot part
        main_df = None
        for key, df in self.datasets.items():
            df = _fix_doubles(df)
            if main_df is None:
                df = df.sort_values(x_var)
                main_df = df.copy()
                main_df[self.GROUP] = key
            else:
                df[self.GROUP] = key
                df = df.sort_values(x_var)
                main_df = pd.concat([main_df, df])

        # Assign bins as max bin value
        main_df = self._assign_bins(main_df, y_var, x_var, bins)

        # The simpler line plot part
        main_df = main_df.sort_values([x_var, self.GROUP])
        grouped_by_x = main_df.groupby(["xbin", self.GROUP])
        main_df["yagg"] = grouped_by_x[y_var].transform("mean")
        line_df = main_df.copy()
        line_df = line_df[["xbin", "yagg", self.GROUP]].drop_duplicates()

        xtitle, ytitle = self._axis_title(x_var), self._axis_title(y_var)

        # Points
        fig = px.scatter(
            main_df,
            x="xbin",
            y="yagg",  # Plot all y's so we can share selections with map
            custom_data=["sc_point_gid", "capacity"],
            labels={x_var: xtitle, y_var: ytitle},
            color=self.GROUP,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )

        # Lines
        for color, group in zip(
            cycle(px.colors.qualitative.Safe), line_df[self.GROUP].unique()
        ):
            df = line_df[line_df[self.GROUP] == group]
            lines = px.line(
                df,
                x="xbin",
                y="yagg",
                color=self.GROUP,
                color_discrete_sequence=[color],
            )
            fig.add_trace(lines.data[0])

        fig.layout["xaxis"]["title"]["text"] = xtitle
        fig.layout["yaxis"]["title"]["text"] = ytitle

        fig.update_traces(
            marker={"size": self.point_size, "line": {"width": 0}},
            unselected={"marker": {"color": "grey"}},
        )

        return self._update_fig_layout(fig, y_var)

    def box(self, y_var):
        """Return a box plot."""

        units = self.config.units.get(
            DiffUnitOptions.remove_from_variable_name(y_var), ""
        )

        def fix_key(key):
            """Display numbers and strings together."""
            if _is_integer(key):
                key = str(key) + units
            return key

        # Infer the y variable and units
        dfs = self.datasets
        df = dfs[list(dfs.keys())[0]]

        main_df = None
        for key, df in dfs.items():
            df = _fix_doubles(df)
            if main_df is None:
                main_df = df.copy()
                main_df[self.GROUP] = key
            else:
                df[self.GROUP] = key
                main_df = pd.concat([main_df, df])

        y_title = self._axis_title(y_var)

        if all(main_df[self.GROUP].apply(_is_integer)):
            main_df[self.GROUP] = main_df[self.GROUP].astype(int)
        main_df = main_df.sort_values(self.GROUP)
        main_df[self.GROUP] = main_df[self.GROUP].apply(fix_key)

        fig = px.box(
            main_df,
            x=self.GROUP,
            y=y_var,
            custom_data=["sc_point_gid", "capacity"],
            labels={y_var: y_title},
            color=self.GROUP,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )

        fig.update_traces(
            marker={
                "size": self.point_size,
                "opacity": 1,
                "line": {'width': 0}
            },
            unselected={"marker": {"color": 'grey'}},
        )

        return self._update_fig_layout(fig, y_var)

    def char_hist(self, x_var):
        """Make a histogram of the characterization column."""
        main_df = list(self.datasets.values())[0]
        counts = {}
        for str_dict in main_df[x_var]:
            if not isinstance(str_dict, str):
                continue
            counts_for_sc_point = json.loads(str_dict)
            for label, count in counts_for_sc_point.items():
                counts[label] = counts.get(label, 0) + count

        labels = sorted(counts, key=lambda k: -counts[k])
        areas = [(counts[label] * 90 * 90) / 1_000_000 for label in labels]
        labels = [str(int(float(label))) for label in labels]

        lookup = None
        if "lookup" in self.config.characterization_cols[x_var]:
            lookup = self.config.characterization_cols[x_var]["lookup"]
            new_labels = []
            for label in labels:
                if label in lookup:
                    new_labels.append(lookup[label])
                else:
                    new_labels.append(label)
            labels = new_labels

        colormap = None
        if "colormap" in self.config.characterization_cols[x_var]:
            colormap = self.config.characterization_cols[x_var]["colormap"]
            if lookup:
                colormap = {lookup[k]: color for k, color in colormap.items()}

        data = pd.DataFrame({"Category": labels, "Area sq km": areas})

        if colormap:
            fig = px.bar(
                data,
                x="Category",
                y="Area sq km",
                color="Category",
                labels={
                    "Category": self.config.titles.get(
                        x_var, convert_to_title(x_var)
                    )
                },
                opacity=self.alpha,
                color_discrete_map=colormap,
                barmode="overlay",
            )
        else:
            fig = px.bar(
                data,
                x="Category",
                y="Area sq km",
                labels={
                    "Category": self.config.titles.get(
                        x_var, convert_to_title(x_var)
                    )
                },
                opacity=self.alpha,
                color_discrete_sequence=px.colors.qualitative.Safe,
                barmode="overlay",
            )

        return self._update_fig_layout(fig)

    def cumulative_sum(self, x_var, y_var):
        """Return a cumulative capacity scatter plot."""
        main_df = None
        for key, df in self.datasets.items():
            df = _fix_doubles(df)
            if main_df is None:
                main_df = df.copy()
                main_df = main_df.sort_values(y_var)
                main_df["cumsum"] = main_df[x_var].cumsum()
                main_df[self.GROUP] = key
            else:
                df = df.sort_values(y_var)
                df["cumsum"] = df[x_var].cumsum()
                df[self.GROUP] = key
                main_df = pd.concat([main_df, df])

        x_title, y_title = self._axis_title(x_var), self._axis_title(y_var)
        main_df = main_df.sort_values(self.GROUP)
        fig = px.scatter(
            main_df,
            x="cumsum",
            y=y_var,
            custom_data=["sc_point_gid", "capacity"],
            labels={
                "cumsum": f"Cumulative {x_title}",
                y_var: y_title,
            },
            color=self.GROUP,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )

        fig.update_traces(
            marker={"size": self.point_size, "line": {"width": 0}},
            unselected={"marker": {"color": 'grey'}},
        )

        return self._update_fig_layout(fig, y_var)

    def figure(self, chart_type="cumsum", x_var=None, y_var=None, bins=None, 
               trace_type="bar", time_period="original"):
        """Return plotly figure for requested chart type."""
        if chart_type == "cumsum":
            print(x_var)
            fig = self.cumulative_sum(x_var, y_var)
        elif chart_type == "scatter":
            fig = self.scatter(x_var, y_var)
        elif chart_type == "binned":
            fig = self.binned(x_var, y_var, bins=bins)
        elif chart_type == "histogram":
            fig = self.histogram(y_var, bins=bins)
        elif chart_type == "char_histogram":
            fig = self.char_hist(x_var)
        elif chart_type == "box":
            fig = self.box(y_var)
        elif chart_type == "timeseries":
            fig = self.timeseries(y_var, trace_type, time_period)
        return fig

    def histogram(self, y_var, bins=100):
        """Return a histogram."""
        main_df = None
        for key, df in self.datasets.items():
            df = _fix_doubles(df)
            if main_df is None:
                main_df = df.copy()
                main_df[self.GROUP] = key
            else:
                df[self.GROUP] = key
                main_df = pd.concat([main_df, df])

        y_title = self._axis_title(y_var)
        main_df = main_df.sort_values(self.GROUP)
        main_df = main_df.dropna(subset=y_var)

        # Use numpy since plotly calculates counts in browser
        main_df = self._histogram(main_df, y_var, bins)

        fig = px.bar(
            main_df,
            x=y_var,
            y="count",
            labels={y_var: y_title},
            color="group",
            custom_data=["bin_size"],
            opacity=self.alpha,
            color_discrete_sequence=px.colors.qualitative.Safe,
            barmode="group"
        )

        fig.update_traces(
            marker={"line": {"width": 0}},
            unselected={"marker": {"color": 'grey'}},
        )

        return self._update_fig_layout(fig, y_var)

    def scatter(self, x_var, y_var):
        """Return a regular scatter plot."""
        main_df = None
        for key, df in self.datasets.items():
            df = _fix_doubles(df)
            if main_df is None:
                main_df = df.copy()
                main_df[self.GROUP] = key
            else:
                df[self.GROUP] = key
                main_df = pd.concat([main_df, df])

        x_title, y_title = self._axis_title(x_var), self._axis_title(y_var)

        main_df = main_df.sort_values(self.GROUP)
        fig = px.scatter(
            main_df,
            x=x_var,
            y=y_var,
            opacity=self.alpha,
            custom_data=["sc_point_gid", "capacity"],
            labels={x_var: x_title, y_var: y_title},
            color=self.GROUP,
            color_discrete_sequence=px.colors.qualitative.Safe,
        )

        fig.update_traces(
            marker_line={"width": 0},
            marker={"size": self.point_size, "line": {"width": 0}},
            unselected={"marker": {"color": 'grey'}},
        )

        return self._update_fig_layout(fig, y_var)

    def timeseries(self, y_var="capacity factor", trace_type="bar",
                   time_period="original"):
        """Render time series."""
        # Check for valid options
        try:
            assert trace_type in ["bar", "line"]
        except:
            raise AssertionError(f"{trace_type} traces not available for this "
                                 "graph.")

        # Create the plottable dataframe
        main_df = None
        for key, df in self.datasets.items():
            if main_df is None:
                key1 = key
                main_df = df.copy()
                if time_period != "original":
                    main_df = self._aggregate_timeseries(main_df, y_var,
                                                         time_period)
                main_df[self.GROUP] = key
            else:
                if time_period != "original":
                    df = self._aggregate_timeseries(df, y_var, time_period)
                df[self.GROUP] = key
                main_df = pd.concat([main_df, df])

        # Get the right x-axis
        if time_period in ["cdf", "pdf"]:
            x = y_var
            y = "Probability"
        else:
            x = "time"
            y = y_var

        # Aggregate time series if needed
        if trace_type == "bar":
            df = main_df[main_df[self.GROUP] == key1]
            fig = px.bar(
                data_frame=df,  # Single dataset for now
                x=x,
                y=y,
                color=y,
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig.update_layout(hovermode="x unified")
        else:
            fig = px.line(
                data_frame=main_df,
                line_group=self.GROUP,
                color=self.GROUP,
                x=x,
                y=y
            )

            fig.update_layout(hovermode="x")

        # Update the layout and axes
        ymin = main_df[y].min()
        ymax = main_df[y].max()
        # fig.update_layout(yaxis_range=[ymin, ymax * 1.1])
        fig.update_xaxes(showspikes=True)
        fig.update_yaxes(showspikes=True)

        if time_period == "original":
            fig.update_layout(
                xaxis_range=[
                    main_df["time"].iloc[0],
                    main_df["time"].iloc[500]
                ]
            )

        return self._update_fig_layout(fig, y_var)

    def _aggregate_timeseries(self, data, y_var="capacity factor",
                              time_period="daily"):
        """Aggregate timeseries to a given time period."""
        # Check inputs
        try:
            assert time_period in ["daily", "hour", "weekly", "monthly", "cdf",
                                   "pdf"]
        except:
            raise AssertionError("Cannot aggregate timeseries to "
                                 f"{time_period} steps.")

        # Aggregate temporally, or via a distribution
        if time_period not in ["cdf", "pdf"]:
            # Aggregate data
            grouped = data.groupby(time_period)
            if y_var == "capacity factor":
                out = grouped[y_var].mean()
            else:
                out = grouped[y_var].sum()
    
            # Reset time stamp
            t1 = data["time"].iloc[0]
            t2 = data["time"].iloc[-1]

            if time_period == "daily":
                time = pd.date_range(t1, t2, freq="1D")
            elif time_period == "hour":
                hours = range(0, 24)
                time = [dt.datetime(1, 1, 1, h) for h in hours]
                time = [t.strftime("%H:%M") for t in time]
            elif time_period == "weekly":
                time = pd.date_range(t1, t2, freq="1W")
            elif time_period == "monthly":
                time = pd.date_range(t1, t2, freq="MS")
                time = [t + pd.offsets.MonthEnd() for t in time]
            time = [str(t) for t in time]
    
            # Rebuild data
            data = pd.DataFrame({y_var: out, "time": time})

        else:
            data = self._distributions(data, y_var)
            if time_period == "cdf":
                data = data[[y_var, "cdf"]]     
            elif time_period == "pdf":
                data = data[[y_var, "pdf"]]
            data.columns = [y_var, "Probability"]

        return data

    def _assign_bins(self, main_df, y_var, x_var, bins):
        """Assign bin values to variable in dataframe."""
        main_df = main_df.dropna(subset=x_var)
        main_df = main_df.sort_values(x_var)
        minx, maxx = main_df[x_var].min(), main_df[x_var].max()
        xrange = maxx - minx
        bin_size = np.ceil(xrange / bins)
        bins = np.arange(minx, maxx + bin_size, bin_size)
        main_df["xbin"] = bins[-1]
        for xbin in bins[::-1]:
            main_df["xbin"][main_df[x_var] <= xbin] = xbin
        grouper = main_df.groupby(["xbin", self.GROUP])
        main_df["ybin"] = grouper[y_var].transform("mean")
        return main_df

    def _axis_title(self, var):
        """Make a title out of variable name and units."""
        diff = DiffUnitOptions.from_variable_name(var)
        is_difference = diff is not None
        is_percent_difference = diff == DiffUnitOptions.PERCENTAGE
        var = DiffUnitOptions.remove_from_variable_name(var)
        var = var.removesuffix("_2")
        title = [self.config.titles.get(var, convert_to_title(var))]

        if is_percent_difference:
            title += ["(%)"]
        elif units := self.config.units.get(var):
            title += [f"({units})"]

        if is_difference:
            # this is a limitation (bug?) of dash...
            # can only have "$" at start and end of string
            title = [t.replace("$", "dollars") for t in title]
            title = ["$", r"\Delta", r"\text{"] + title + ["}$"]

        return " ".join(title)

    def _distributions(self, data, y_var, nbins=100):
        """Build a data frame with CDF and PDF curves."""
        data = data.sort_values(y_var)
        count, bins = np.histogram(data[y_var], bins=nbins)
        cbins = bins + (np.diff(bins)[0] / 2)
        cbins = cbins[:-1]
        pdf = count / sum(count)
        cdf = np.cumsum(pdf)
        df = pd.DataFrame({y_var: cbins, "cdf": cdf, "pdf": pdf})
        df = df.reset_index()
        return df

    def _histogram(self, main_df, y_var, bins):
        """Build grouped bin count dataframe for histogram."""
        # Get bin ranges for full value range
        main_df = main_df.dropna(subset=y_var)
        _, xbins = np.histogram(main_df[y_var], bins=bins)
        bin_size = np.diff(xbins)[0]

        # Build grouped binned counts
        df = pd.DataFrame(columns=["count", y_var, "group"])
        for group, values in main_df.groupby(self.GROUP)[y_var]:
            sdf = pd.DataFrame({"y": values})
            sdf[y_var] = sdf["y"].apply(
                lambda y: [xbin for xbin in xbins[:-1] if y >= xbin][-1]
            )
            sdf["count"] = sdf.groupby(y_var)[y_var].transform("count")
            sdf = sdf[[y_var, "count"]].drop_duplicates()
            sdf["group"] = group
            df = pd.concat([df, sdf])

        # Add bin size for chart selection filtering later
        df["bin_size"] = bin_size

        return df

    def _plot_range(self, var):
        """Get plot range."""
        user_ymin, user_ymax = self.user_scale
        scale = self.config.scales.get(
            DiffUnitOptions.remove_from_variable_name(var), {}
        )
        ymin = user_ymin or scale.get("min")
        ymax = user_ymax or scale.get("max")

        if ymin and not ymax:
            ymax = max([df[var].max() for df in self.datasets.values()])
        if ymax and not ymin:
            ymin = min([df[var].min() for df in self.datasets.values()])
        return [ymin, ymax]

    def _update_fig_layout(self, fig, y_var=None):
        """Update the figure layout with title, etc."""
        layout = copy.deepcopy(CHART_LAYOUT)
        layout["title"]["text"] = self.plot_title
        layout["legend_title_text"] = self.GROUP
        fig.update_layout(**layout)
        if y_var:
            fig.update_layout(yaxis={"range": self._plot_range(y_var)})
        return fig
