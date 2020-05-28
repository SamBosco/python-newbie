from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from pandas import pandas as pd
from pandas import DataFrame
import plotly as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)

def log_error(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything
    """
    print(e)

def scrape_html():
    """
    Scrape the html from worldometer site for COVID19 data
    """  
    raw_html = simple_get('https://www.worldometers.info/coronavirus/')
    html = BeautifulSoup(raw_html,'html.parser')
    list_of_countries =[]
    #locate the countries stats table
    countries_table  =   html.find('table',attrs={'id':'main_table_countries_today'})
    #print(countries_table)
    #get the rows of the table
    rows = countries_table.find_all('tr')
    #print(rows)
    #get the header of the table
    header = [th.text.rstrip() for th in rows[0].find_all('th')]
    #print(header)
    print('----------------')
    print(len(header))

    c1=[] #country name
    c2 =[] #total cases
    c3 =[] #new cases
    c4 = [] #total deaths
    c5=[] # new deaths
    c6=[] #Total recovered
    c7=[]#Active cases
    c8=[]#Serious,Critical
    c9=[]#Total cases per 1 M population
    c10 =[]#total deaths per 1 M population

    for row in countries_table.find_all('tr'):
        cells = row.find_all('td')
        if(len(cells)==15):
            c1.append(cells[1].find(text=True)) #fetch the text in the url of the td tag(country name)
            c2.append(cells[2].find(text=True)) #total cases
            c3.append(cells[3].find(text=True))#new cases
            c4.append(cells[4].find(text=True)) #total deaths
            c5.append(cells[5].find(text=True)) #New deaths
            c6.append(cells[6].find(text=True))#Total recovered
            c7.append(cells[7].find(text=True))#Active cases
            c8.append(cells[8].find(text=True))#Serious, critical
            c9.append(cells[9].find(text=True))#Total cases per 1 M population
            c10.append(cells[10].find(text=True))#Total deaths per 1 M population

    d = dict([(x,0) for x in header])

    #print(c1)

    d['Country,Other'] = c1
    d['TotalCases'] = c2
    d['NewCases'] = c3
    d['TotalDeaths'] = c4
    d['NewDeaths'] = c5
    d['TotalRecovered'] = c6
    d['ActiveCases']=c7
    d['Serious,Critical']=c8
    d['TotalCases/1M pop'] =c9
    d['Deaths/1M pop'] = c10
   
    #convert dictionary object to a dataframe

    df_table = pd.DataFrame(d)
    return df_table

def clean_data():
    """
    clean and export the data to read from a csv file
    """
    df_table = scrape_html()
    mod_df_table = df_table.drop(index=[0,1,2,3,4,5,6])
    #mod_df_table= df_table
    print(mod_df_table)

    #drop unwanted columns
    mod_df_table = mod_df_table.drop(columns=['Continent','TotalTests','Tests/\n1M pop'])
    #print(mod_df_table.tail())
    mod_df_table = mod_df_table.drop(mod_df_table.columns[-3],axis=1) #delete the extra column of total cases per 1 M which has a special character in its label

    #print(mod_df_table.head())

    mod_df_table = mod_df_table.rename(columns={"Country,Other":"Country"})

    #sort the file by country names in ascending order
    mod_df_table.sort_values(by=['Country'],inplace=True)

    #drop the row of total
    mod_df_table = mod_df_table[~mod_df_table['Country'].isin(['Total:'])]
 
    #drop cruise ship names

    mod_df_table = mod_df_table[~mod_df_table['Country'].isin(['Diamond Princess','MS Zaandam'])]

    #drop the row of world
    mod_df_table = mod_df_table[~mod_df_table['Country'].isin(['World'])]

    #replace all commas in numbers

    mod_df_table['TotalDeaths'] = mod_df_table['TotalDeaths'].str.replace(',', '')
    mod_df_table['TotalCases'] = mod_df_table['TotalCases'].str.replace(',', '')
    mod_df_table['NewCases'] = mod_df_table['NewCases'].str.replace(',', '')
    mod_df_table['TotalRecovered'] = mod_df_table['TotalRecovered'].str.replace(',', '')
    mod_df_table['NewDeaths'] = mod_df_table['NewDeaths'].str.replace(',', '')
    mod_df_table['TotalRecovered'] = mod_df_table['TotalRecovered'].str.replace(',', '')
    mod_df_table['ActiveCases'] = mod_df_table['ActiveCases'].str.replace(',', '')

# # #export dataframe to a csv file
    mod_df_table.to_csv('F:/Python/CSVcovid19latestdata.csv', index=False,header=True)

    datafile = 'F:/Python/CSVcovid19latestdata.csv'

    df = pd.read_csv(datafile)
    return df

def generate_maps():
    '''Generate the 2 world maps'''
    df = clean_data()
     #Plot the first map
    fig1 = go.Figure(data=go.Choropleth(
    locations = df['Country'],
    locationmode='country names',
    z = df['TotalDeaths'],
    text = df['Country'],
    colorscale = 'Viridis',
    autocolorscale=False,
    reversescale=True,
    marker_line_color='darkgray',
    marker_line_width=0.5,
    colorbar_tickprefix = ' ',
    colorbar_title = 'Total Deaths',
   
    ))

    fig1.update_layout(
    title_text='Choropleth World  Map representing COVID-19 deaths around the world today',
    #geo_scope='world',
    geo=dict(
        scope='world',
        showland = True,
        showlakes = True,
        showcountries = True,
        showocean = True,
        countrywidth = 0.5,
        landcolor = 'rgb(230, 145, 56)',
        lakecolor = 'rgb(207, 241, 255)',
        oceancolor = 'rgb(187, 235, 255)',
         projection = dict( 
                type = 'equirectangular'
                        
            )

    ),
    annotations = [dict(
        x=0.55,
        y=0.15,
        xref='paper',
        yref='paper',
        text='Source: <a href="https://www.worldometers.info/coronavirus/">\
             Worldometer COVID-19 CORONAVIRUS PANDEMIC</a>',
        showarrow = False
    )]
    )
    fig1.show()
    #plot the second map
    df['text'] = 'TotalCases: ' + df['TotalCases'].astype(str)
    scale = 1000
    data=[go.Scattergeo(
            lat=[45.5017, 51.509865, 52.520008],
            lon=[-73.5673, -0.118092, 13.404954 ],
            locationmode='country names',
            locations=df['Country'],
            text=df['text'],
            
            marker = dict(
            size = df['TotalCases']/scale,
            sizemode = 'area',
            opacity = 0.8,
            reversescale = True,
            autocolorscale = False,
            symbol = 'circle',
            line = dict(
                width=1,
                color='rgba(102, 102, 102)'
            ),
            colorscale = 'Viridis',
            cmin = 0,
            color = df['TotalCases'],
            cmax = df['TotalCases'].max(),
            colorbar_title="Covid19 cases"
        )
            ),
            
            ]

    layout =go.Layout(
     #title_text='Covid 19 cases around the world today',
        title='Covid 19 cases around the world today<br>Source: <a href="https://www.worldometers.info/coronavirus/">Worldometers </a>',
        title_x=0.5,
        geo=go.layout.Geo(
            projection_type='orthographic',
            center_lon=-180,
            center_lat=0,
            projection_rotation_lon=-180,
            showland=True,
            showcountries=True,
            countrycolor='rgb(204, 204, 204)',
            scope='world',
            showlakes = True,
            showocean = True,
            countrywidth = 0.5,
            #landcolor = 'rgb(230, 145, 56)',
            lakecolor = 'rgb(207, 241, 255)',
            oceancolor = 'rgb(187, 235, 255)',
             lonaxis = dict( 
                showgrid = True,
                gridcolor = 'rgb(102, 102, 102)',
                gridwidth = 0.5
            ),
            lataxis = dict( 
                showgrid = True,
                gridcolor = 'rgb(102, 102, 102)',
                gridwidth = 0.5
            ),

        ),
       
       updatemenus=[dict(type='buttons', showactive=False,
                                y=1,
                                x=1.2,
                                xanchor='right',
                                yanchor='top',
                                pad=dict(t=0, r=10),
                                buttons=[dict(label='Play',
                                              method='animate',
                                              args=[None, 
                                                    dict(frame=dict(duration=400, 
                                                                    redraw=True),
                                                         transition=dict(duration=200),
                                                         fromcurrent=True,
                                                         mode='immediate')
                                                   ]),

                                         ],
                                         
                                        )
            ]
    )
    lon_range = np.arange(-180, 180, 2)

    frames = [dict(layout=dict(geo_center_lon=lon,
                           geo_projection_rotation_lon =lon
                           )) for lon in lon_range]
    
    fig2 = go.Figure(data=data, layout=layout, frames=frames)
    fig2.show()
generate_maps()



