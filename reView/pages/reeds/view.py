# -*- coding: utf-8 -*-
"""The scenario page html layout.

Created on Tue Jul  6 15:23:09 2021

@author: twillia2
"""
from dash import dcc, html

from reView.utils.functions import data_paths
from reView.components import (
    above_map_options_div,
    map_div,
    below_map_options_div,
)


PROJECT = str(list(data_paths()["reeds"].glob("*csv"))[0])


layout = html.Div(
    children=[
        # Path Name
        dcc.Location(id="/reeds_page", refresh=False),

        # Constant info block
        html.Div(
            [
                # Project Selection
                html.Div(
                    [
                        html.H4("Project"),
                        dcc.Dropdown(
                            id="project_reeds",
                            options=[
                                # pylint: disable=not-an-iterable
                                {
                                    "label": "Reference Advanced - 95% CO",
                                    "value": PROJECT,
                                }
                            ],
                            value=PROJECT,
                        ),
                    ],
                    className="three columns",
                ),
                # Print total capacity after all the filters are applied
                html.Div(
                    [
                        html.H5("Remaining Generation Capacity: "),
                        dcc.Loading(
                            children=[
                                html.H1(
                                    id="capacity_print_reeds", children=""
                                ),
                            ],
                            type="circle",
                        ),
                    ],
                    className="three columns",
                ),
                # Print total capacity after all the filters are applied
                html.Div(
                    [
                        html.H5("Number of Sites: "),
                        dcc.Loading(
                            children=[
                                html.H1(id="site_print_reeds", children=""),
                            ],
                            type="circle",
                        ),
                    ],
                    className="three columns",
                ),
            ],
            className="elevent columns",
            style={"margin-bottom": "35px"},
        ),

        # Year selection
        html.P(
            "Year: ",
            id="year_text",
            className="four columns",
            style={"text-align": "left"},
        ),
        html.Div(
            [
                dcc.Slider(
                    id="years_reeds",
                    step=2
                )
            ],
            className="nine columns",
            style={"text-align": "center", "margin-bottom": "55px"},
        ),


        # The map
        html.Div(
            style={
                "box-shadow": "0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)"
            },
            className="ten columns",
            children=[
                above_map_options_div(
                    id_prefix="map_reeds"
                ),
                map_div(
                    id="map_reeds"
                ),
                below_map_options_div(
                    id_prefix="map_reeds"
                ),
            ]
        ),

        # Capacity after make_map (avoiding duplicate calls)
        html.Div(id="mapcap_reeds", style={"display": "none"}),
    ]
)
