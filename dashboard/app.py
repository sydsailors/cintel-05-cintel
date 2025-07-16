# --------------------------------------------
# Imports at the top - PyShiny EXPRESS VERSION
# --------------------------------------------

# From shiny, import just reactive and render 
from shiny import reactive, render

# From shiny.express, import just ui and inputs if needed
from shiny.express import ui, input

# Add more imports as needed
import random
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly
from scipy import stats
from faicons import icon_svg

# --------------------------------------------
# Set a constant UPDATE INTERVAL for all live data
# Initialize a REACTIVE VALUE with a common data structure
# This reactive value is used to store state (information)
# This reactive value is a wrapper around a DEQUE of readings
# --------------------------------------------

UPDATE_INTERVAL_SECS: int = 5
DEQUE_SIZE: int = 7
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

# --------------------------------------------
# Initialize a REACTIVE CALC that all display components can call 
# to get the latest data and display it. 
# The calculation is invalidated every UPDATE_INTERVAL_SECS 
# to trigger updates.
# It returns to a tuple with everything needed to display the data.
# Very easy to expand or modify. 
# --------------------------------------------

@reactive.calc()
def reactive_calc_combined():
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)
    # Data generation logic
    temperature = round(random.uniform(-18, -16), 1)
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_dictionary_entry = {"temp": temperature, "timestamp": time}
    
    # Get the deque and append the new entry
    reactive_value_wrapper.get().append(new_dictionary_entry)

    # Get a snapshot of the current deque for any further processing
    deque_snapshot = reactive_value_wrapper.get()

    # For Display: convert deque to DataFrame for display
    df = pd.DataFrame(deque_snapshot)

    # For Display: get the latest dictionary entry
    latest_dictionary_entry = new_dictionary_entry 

    # Return a tuple with everything we need 
    return deque_snapshot, df, latest_dictionary_entry

# --------------------------------------------
# Define the Shiny UI Page layout
# Call the ui.page_opts() function
# --------------------------------------------

ui.page_opts(title="PyShiny Express: Live Data Example", fillable=True)

# Sidebar is typically used for user interaction/information
with ui.sidebar(open="open"):
    ui.h2("Antarctic Explorer", class_="text-center")
    ui.p("A demonstration of real-time temperature readings in Antarctica.", class_="text-center")
    ui.hr()
    ui.h6("Links:")
    ui.a("GitHub Source", href="https://github.com/sydsailors/cintel-05-cintel", target="_blank")
    ui.a("GitHub App", href="https://sydsailors.github.io/cintel-05-cintel/", target="_blank")
    ui.a("PyShiny", href="https://shiny.posit.co/py/", target="_blank")
    ui.a("PyShiny Express", href="https://shiny.posit.co/blog/posts/shiny-express/", target="_blank")

    # Add a unit toggle switch to display either Fehrenheit or Celsius
    ui.input_switch("use_fahrenheit", "Display in Fahrenheit", value=False)

# --------------------------------------------
# Main UI Panels
# --------------------------------------------

with ui.layout_columns():
    with ui.value_box(
        showcase=icon_svg("sun"),
        theme="bg-gradient-purple-blue",
    ):
        "Current Temperature"

        @render.text
        def display_temp():
            # Get the latest reading and return a temperature string
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
            temp_c = latest_dictionary_entry["temp"]
            if input.use_fahrenheit():
                temp_f = round(temp_c * 9 / 5 + 32, 1)
                return f"{temp_f} °F"
            else:
                return f"{temp_c} °C"
        "Live temperature reading"

    with ui.card(full_screen=True):
        ui.card_header("Current Date and Time")

        @render.text
        def display_time():
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
            return f"{latest_dictionary_entry['timestamp']}"

with ui.card(full_screen=True):
    ui.card_header("Most Recent Readings")

    @render.data_frame
    def display_df():
        _, df, _ = reactive_calc_combined()
        
        # Create funtion to change display to show temperatures in Fahrenheit or Celsius
        if input.use_fahrenheit():
            df["Temperature (°F)"] = df["temp"] * 9 / 5 + 32
            df_display = df[["Temperature (°F)", "timestamp"]].rename(columns={"timestamp": "Timestamp"})
        else:
            df_display = df.rename(columns={"temp": "Temperature (°C)", "timestamp": "Timestamp"})

        # Use maximum width
        return render.DataGrid(df_display, width="100%")

with ui.card():
    ui.card_header("Chart with Current Trend")

    @render_plotly
    def display_plot():

        # Fetch from the reactive calc function 
        deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
        
        # Ensure the DataFrame is not empty before plotting
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            if input.use_fahrenheit():
                df["temp_display"] = df["temp"] * 9 / 5 + 32
                y_label = "Temperature (°F)"
            else:
                df["temp_display"] = df["temp"]
                y_label = "Temperature (°C)"

            # Create scatter plot for readings 
            # Pass in the df, the name of the x column, the name of the y column, and more
            fig = px.scatter(
                df,
                x="timestamp",
                y="temp_display",
                title="Temperature Readings with Regression Line",
                labels={"temp_display": y_label, "timestamp": "Time"},
                color_discrete_sequence=["blue"]
            )

            # Linear regression line
            x_vals = list(range(len(df)))
            y_vals = df["temp_display"]
            slope, intercept, _, _, _ = stats.linregress(x_vals, y_vals)
            df["best_fit_line"] = [slope * x + intercept for x in x_vals]

            fig.add_scatter(
                x=df["timestamp"],
                y=df["best_fit_line"],
                mode="lines",
                name="Regression Line"
            )

            fig.update_layout(xaxis_title="Time", yaxis_title=y_label)
            
            return fig
