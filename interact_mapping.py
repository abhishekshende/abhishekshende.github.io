import pandas as pd
import math
from ast import literal_eval
from bokeh.io import curdoc
from bokeh.plotting import figure, show, output_file, ColumnDataSource
from bokeh.models import ColorBar, Select,HoverTool
from bokeh.palettes import RdYlGn
from bokeh.transform import linear_cmap,log_cmap
from bokeh.models.widgets import Slider,Tabs,Panel,RangeSlider
from bokeh.layouts import row, column,widgetbox


model_dataset = pd.read_csv('flask_data.csv')


def merc(coords):
    coordinates = literal_eval(coords)
    lat = coordinates[0]
    lon = coordinates[1]
    r_major = 6378137.000
    x = r_major * math.radians(lon)
    scale = x/lon
    y = 180.0/math.pi * math.log(math.tan(math.pi/4.0 + lat * (math.pi/180.0)/2.0)) * scale
    return x, y


def make_tuple_str(x, y):
    t = (x, y)
    return str(t)


range0 = merc('(32.5, -116)')
range1 = merc('(33.5, -118)')
x_range = (range0[0], range1[0])
y_range = (range0[1], range1[1])


def display_data(selected_year, df=model_dataset, low_price=10000, high_price=100000000):
    yr = selected_year
    df = df[df['Tx_Year'] == yr]
    df = df[(df['TransferAmount'] >= low_price) & (df['TransferAmount'] < high_price)]

    df['coords'] = df.apply(lambda x: make_tuple_str(x['PropertyLatitude'], x['PropertyLongitude']), axis=1)
    df['coords_latitude'] = df['coords'].apply(lambda x: merc(x)[0])
    df['coords_longitude'] = df['coords'].apply(lambda x: merc(x)[1])

    return ColumnDataSource(data=df)


def make_plot(source):
    pal = RdYlGn[10]

    mapper = log_cmap(field_name="TransferAmount", palette=pal, low=10000, high=50000000)
    tooltips = [("Price", "@TransferAmount"), ("SaleYear", "@Tx_Year")]
    # slider = Slider(start=2000, end=2019, step=1, value=2015, title = 'Year')

    from bokeh.tile_providers import get_provider, Vendors
    fig = figure(x_range=x_range, y_range=y_range, x_axis_type='mercator', y_axis_type='mercator', tooltips=tooltips,
                 title='San Diego Residential Housing Prices')
    fig.add_tile(get_provider(Vendors.CARTODBPOSITRON))
    fig.circle(x='coords_latitude', y='coords_longitude', line_color=mapper, color=mapper, source=source)

    # Defines color bar attributes and location
    color_bar = ColorBar(color_mapper=mapper['transform'], width=8, location=(0, 0))
    fig.add_layout(color_bar, 'right')

    # Defines layout of graph and widgets

    return fig


def update_plot(attr, old, new):
    yr = slider.value
    range_start = range_select.value[0]
    range_end = range_select.value[1]
    new_data = display_data(selected_year=yr, low_price=range_start, high_price=range_end)
    source.data.update(new_data.data)
    fig.title.text = 'San Diego Housing Prices,' + str(yr) + 'Price Range - (' + str(range_start/1000000)+'M, ' + \
                     str(range_end/1000000)+'M'


# Make a slider object: slider
slider = Slider(title='Year', start=2000, end=2019, step=1, value=2015)
#price_min = Select(value=10000, title='Min Sale Price', options=)
#price_max = Select(value=1000000, title='Max Sale Price', options=)

range_select = RangeSlider(start=50000, end=20000000, value=(1000000, 5000000), step=50000, title='Price Range ($)')

# Update the plot when the value is changed

source = display_data(selected_year=2015)
fig = make_plot(source)

slider.on_change('value', update_plot)
range_select.on_change('value', update_plot)
# Make a column layout of widgetbox(slider) and plot, and add it to the current document
layout = column(fig, widgetbox(slider, range_select))
curdoc().add_root(layout)
curdoc().title = 'San Deigo Housing Prices'

output_file('viz.html')

show(layout)
# Calls figure