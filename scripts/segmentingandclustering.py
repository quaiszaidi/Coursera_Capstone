#Step 1
#Importing necessary libraries
import requests
from bs4 import BeautifulSoup
import pandas as pd

%config IPCompleter.greedy = True

# Output multiple statements from one input cell
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"
#defining title and data set
table_from_top = 1
wikipedia_page = 'Toronto neighborhood dataset'
trace = True


#importing wikipedia link to be converted
wikipedia_url = 'https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M'.format(wikipedia_page)
page = requests.get(wikipedia_url)
soup = BeautifulSoup(page.content, 'lxml')
tables = soup.find_all('table', {'class': 'wikitable'})
table = tables[table_from_top - 1]

feature_names = []

header_row = table.find('tr')
for header in header_row.find_all('th'):
    feature_name = ' '.join(header.find_all(text=True))
    feature_name.replace('\n', '')
    feature_names.append(feature_name)

    def has_coords(tag):
    if tag.has_attr('class'):
        if tag['class'][0] == 'latitude' or tag['class'][0] == 'longitude':
            return True
    return False

def get_coords(child):
    coords = []
    for coord in child.find_all(has_coords):
        coords.append(coord.string)
    if coords:
        if trace:
            return '{}'.format(' '.join(coords))
        else:
            return ' '.join(coords)
    else:
        return ''

samples = []
sample_rows = table.find_all('tr')[1:]
for sample_row in sample_rows:
    features = []
    for feature_col in sample_row.find_all('td'):
        feature_value = ''
        text = feature_col.string
        if text:
            if trace:
                features.append('{}'.format(text))
            else:
                features.append(text)
            continue

        for child in feature_col.children:
            if child.name == 'span':
                if child.has_attr('class'):
                    if child['class'] == 'display:none':
                        continue
                if child.find_all(has_coords):
                    feature_value = get_coords(child)
                    if feature_value:
                        break
                    else:
                        continue
            if child.name == 'sup':
                continue
            if child.name == 'a':
                if child.string[0] == '[':
                    continue
            if child.name == 'a':
                if trace:
                    feature_value = '{}'.format(child.string)
                else:
                    feature_value = child.string
                break
            if child.name == 'font':
                if trace:
                    feature_value = '{}'.format(child.string)
                else:
                    feature_value = child.string
                break
            try:
                # feature_value = '' for any tags not covered above
                content = child.contents
            except AttributeError:
                # Handle whitespace between child tags, treated as a child string
                if child.isspace():
                    continue
                if trace:
                    feature_value = '{}'.format(child)
                else:
                    feature_value = child
                break
        features.append(feature_value)
    samples.append(dict(zip(feature_names, features)))

    #refining data

import numpy as np
df = pd.DataFrame(samples)
df.replace("Not assigned\n", np.nan, inplace = True)
df['Borough\n'] = df['Borough\n'].str.replace(r'\n', '')
df['Neighbourhood\n'] = df['Neighbourhood\n'].str.replace(r'\n', '')
df['Postal Code\n'] = df['Postal Code\n'].str.replace(r'\n', '')
df.dropna(subset=["Borough\n"], axis=0, inplace=True)
df.reset_index(drop=True, inplace=True)
columns=['Borough', 'Neighborhood', 'Latitude', 'Longitude']
df.rename(columns = {'Borough\n':'Borough', 'Neighbourhood\n':'Neighbourhood', 'Postal Code\n':'Postal Code'}, inplace = True)
df.shape

#step 2
url="http://cocl.us/Geospatial_data"
df2 = pd.read_csv(url, header=None)




df2.drop([0])
df2.columns = ['Postal Code','Latitude','Longitude']
df2.head(5)

df=pd.merge(df,df2)
df.head()

#step 3
df['Longitude']=df['Longitude'].astype(float)

df['Latitude']=df['Latitude'].astype(float)

lat = (list(df["Latitude"]))
lon = (list(df["Longitude"]))
latitude = []
longitude=[]

for la in lat:
    la = pd.to_numeric(df['Latitude'])
    latitude.append(la)
for lo in lon:
    lo=pd.to_numeric(df['Longitude'])
    longitude.append(lo)

CLIENT_ID = 'MHZCRRAKH30M1J2OV02H3H0ERBFT5IWCBPDOZU2HBTNXSDNK' # Foursquare ID
CLIENT_SECRET = 'Z2BYCKDFBD1J4JLJ20GWAUAU2U0TEWK3T1MTGAYXCQDLJA1I' #Foursquare Secret
VERSION = '20180605' # Foursquare API version
radius=500
limit=100

def getNearbyVenues(names, latitudes, longitudes, radius=500):

    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)

        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID,
            CLIENT_SECRET,
            VERSION,
            lat,
            lng,
            radius,
            limit)

        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']




        venues_list.append([(
            name,
            lat,
            lng,
            v['venue']['name'],
            v['venue']['location']['lat'],
            v['venue']['location']['lng'],
            v['venue']['categories'][0]['name']) for v in results])


    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood',
                  'Neighborhood Latitude',
                  'Neighborhood Longitude',
                  'Venue',
                  'Venue Latitude',
                  'Venue Longitude',
                  'Venue Category']

    return(nearby_venues)


toronto_venues = getNearbyVenues(names=df['Neighbourhood'],
                                   latitudes=df['Latitude'],
                                   longitudes=df['Longitude']
                                  )


toronto_venues.head()
toronto_venues.groupby('Neighborhood').count()
print('There are {} uniques categories.'.format(len(toronto_venues['Venue Category'].unique())))

#one hot encoding
toronto_onehot = pd.get_dummies(toronto_venues[['Venue Category']], prefix="", prefix_sep="")


toronto_onehot['Neighborhood'] = toronto_venues['Neighborhood']

fixed_columns = [toronto_onehot.columns[-1]] + list(toronto_onehot.columns[:-1])
toronto_onehot = toronto_onehot[fixed_columns]

toronto_onehot.head()


toronto_grouped = toronto_onehot.groupby('Neighborhood').mean().reset_index()
num_top_venues = 5

for hood in toronto_grouped['Neighborhood']:
    print(hood,':')
    temp = toronto_grouped[toronto_grouped['Neighborhood'] == hood].T.reset_index()
    temp.columns = ['venue','freq']
    temp = temp.iloc[1:]
    temp['freq'] = temp['freq'].astype(float)
    temp = temp.round({'freq': 2})
    print(temp.sort_values('freq', ascending=False).reset_index(drop=True).head(num_top_venues))
    print('\n')


#fucntion for most common value
def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)

    return row_categories_sorted.index.values[0:num_top_venues]

#identifying most popular venues in the neighbourhood
num_top_venues = 10

indicators = ['st', 'nd', 'rd']


columns = ['Neighborhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

neighborhoods_venues_sorted = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted['Neighborhood'] = toronto_grouped['Neighborhood']

for ind in np.arange(toronto_grouped.shape[0]):
    neighborhoods_venues_sorted.iloc[ind, 1:] = return_most_common_venues(toronto_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted.head()

#creating clusters
kclusters = 5

toronto_grouped_clustering = toronto_grouped.drop('Neighborhood', 1)
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(toronto_grouped_clustering)
kmeans.labels_[0:10]

df= df.reset_index(drop=True)
df.head()


neighborhoods_venues_sorted.insert(0, 'Cluster Labels', kmeans.labels_)

toronto_merged = df

# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
toronto_merged = toronto_merged.join(neighborhoods_venues_sorted.set_index('Neighborhood'), on='Neighborhood')

df.head()

map_clusters = folium.Map(location=[latitude, longitude], zoom_start=11)

# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# visulization of the data
markers_colors = []
for lat, lon, poi, cluster in zip(toronto_merged['Latitude'], toronto_merged['Longitude'], toronto_merged['Neighborhood'], toronto_merged['Cluster Labels']):
    label = folium.Popup(str(poi) + ' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[cluster-1],
        fill=True,
        fill_color=rainbow[cluster-1],
        fill_opacity=0.7).add_to(map_clusters)

map_clusters
