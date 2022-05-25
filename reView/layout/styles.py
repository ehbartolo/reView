"""reView style specifications."""
import copy


# Move to CSS
BUTTON_STYLES = {
    "on": {
        "height": "35px",
        "width": "175px",
        "padding": "0px",
        "background-color": "#FCCD34",
        "border-radius": "4px",
        "border-color": "#1663b5",
        "font-family": "Times New Roman",
        "font-size": "12px",
        "margin-top": "-2px",
    },
    "off": {
        "height": "35px",
        "width": "175px",
        "text-align": "center",
        "padding": "0px",
        "border-color": "#1663b5",
        "background-color": "#b89627",
        "border-radius": "4px",
        "font-family": "Times New Roman",
        "font-size": "12px",
        "margin-top": "-2px",
    },
    "navbar": {
        "height": "55px",
        "width": "215px",
        "padding": "0px",
        "background-color": "#FCCD34",
        "border-radius": "4px",
        "border-color": "#1663b5",
        "font-family": "Times New Roman",
        "font-size": "14px",
        "margin-top": "-2px",
    },
}
BOTTOM_DIV_STYLE = {
    # "height": "65px",
    "float": "left",
    "margin-top": "-2px",
    "margin-left": -1,
    "border": "3px solid #1663b5",
    "border-radius": "4px",
    "border-width": "3px",
    "border-top-width": "0px",
    "border-radius-top-left": "0px",
    "border-radius-top-right": "0px",
}
STYLESHEET = "https://codepen.io/chriddyp/pen/bWLwgP.css"
TAB_STYLE = {"height": "25px", "padding": "0"}
TABLET_STYLE = {"line-height": "25px", "padding": "0"}
# Everything below goes into a css
TABLET_STYLE_CLOSED = {
    **TABLET_STYLE,
    **{"border-bottom": "1px solid #d6d6d6"},
}
TAB_BOTTOM_SELECTED_STYLE = {
    "borderBottom": "1px solid #1975FA",
    "borderTop": "1px solid #d6d6d6",
    "line-height": "25px",
    "padding": "0px",
}
RC_STYLES = copy.deepcopy(BUTTON_STYLES)
RC_STYLES["off"]["border-color"] = RC_STYLES["on"]["border-color"] = "#1663b5"
RC_STYLES["off"]["border-width"] = RC_STYLES["on"]["border-width"] = "3px"
RC_STYLES["off"]["border-top-width"] = "0px"
RC_STYLES["on"]["border-top-width"] = "0px"
RC_STYLES["off"]["border-radius-top-left"] = "0px"
RC_STYLES["on"]["border-radius-top-right"] = "0px"
RC_STYLES["off"]["float"] = RC_STYLES["on"]["float"] = "right"
# Everything above goes into css