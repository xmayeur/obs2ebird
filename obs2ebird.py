import pandas as pd
import sqlalchemy.exc
from sqlalchemy import create_engine, text

import warnings

from glob import glob
from sys import exit
from os.path import basename, dirname, join

import argparse
import re
from geopy.geocoders import Nominatim, options
from geopy import distance
import certifi
import ssl
import datetime
import csv
import sqlite3

from get_config import get_config

config = get_config()
error = None

__dir__ = dirname(__file__)

ctx = ssl.create_default_context(cafile=certifi.where())
options.default_ssl_context = ctx
options.default_user_agent = 'obs2ebird'
geolocator = Nominatim(scheme='http')
args = None

warnings.simplefilter(action='ignore', category=FutureWarning)
is_sqlite = (config['default']['db_dialect'] == 'sqlite')


def db_conn():
    """
    Connects to a MySQL database using the provided credentials and returns a SQLAlchemy engine.

    :return: A SQLAlchemy engine connected to the MySQL database.
    """
    db = None

    if is_sqlite:
        try:
            db = config['sqlite']['db']
            return sqlite3.connect(db), basename(db).split('.')[0]
        except sqlite3.OperationalError:
            print(f'Cannot open database "{db}"')
            return None, None
    else:
        try:
            from get_secrets import get_secret
            user, pwd = get_secret('comptes')
            host = config['mysql']['host']
            port = config['mysql']['port']
            db = config['mysql']['db']
            return create_engine(f'mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}', pool_recycle=3600), db
        except:
            return None, None


def import_obs(input_file, folder='.'):
    """
    Import OBS Method

    Imports observation data from given input file(s) into a SQL database.

    :param input_file: A string representing the path or paths to the input files.
                       Multiple files can be specified by separating them with commas.
                       Wildcards are allowed (unix style)
    :param folder:     file directory if not part of the input_file path
    :return: None|str  A status string is return in case of error
    """
    # read input data
    d = pd.DataFrame()
    for in_file in input_file.split(','):
        in_file = in_file.strip()
        if dirname(in_file) == '':
            in_file = join(folder, basename(in_file))
        for f in glob(in_file):
            df = pd.read_csv(f, delimiter=',', engine='python', encoding='UTF_8').fillna('')
            d = pd.concat([d, df])

    # and save to mySQL db
    sqlEngine, db = db_conn()
    if db is None:
        return "Error in creating the database connection"
    try:
        if is_sqlite:
            d.to_sql(name=db, con=sqlEngine, if_exists='replace')
            sqlEngine.commit()
        else:
            with sqlEngine.begin() as cnx:
                cnx.execute(text(f"CREATE TABLE `{config['mysql']['db']}` IF NOT EXISTS"))
                cnx.execute(text(f"DROP TABLE `temp_table`IF EXISTS"))

                if 'local x' not in d:
                    d['local x'] = ''
                    d['local y'] = ''
                d.to_sql(name=config['mysql']['db'], con=cnx, if_exists='replace')
            # with sqlEngine.begin() as cnx:
            #    sql = f"REPLACE INTO `{config['mysql']['db']}` SELECT * FROM `temp_table`"
            #    cnx.execute(text(sql))
        return None

    except sqlalchemy.exc.OperationalError:
        return 'Cannot connect to database - check if running'


def query_database(start_date, end_date, sqlEngine, dbname):
    """
    Query the database for data between two dates.

    :param start_date: The start date of the data to query.
    :param end_date: The end date of the data to query. If None, only data on start_date will be queried.
    :param sqlEngine: The SQLAlchemy engine object to use for the database connection.
    :param dbname: The name of the database table to query.
    :return: A Pandas DataFrame containing the queried data.

    """
    quote = '"' if is_sqlite else '`'
    query = (
        f'select * from {quote}{dbname}{quote} where {quote}date{quote} >= "{start_date}"'
        if end_date is None
        else f'select * from {quote}{dbname}{quote} where {quote}date{quote} between "{start_date}" '
             f'and "{end_date}"'
    )
    try:
        return pd.read_sql(query, con=sqlEngine)
    except sqlalchemy.exc.OperationalError:
        print('Cannot connect to MySQL database - check if running or cannot run query')
        return pd.DataFrame()


def prepare_data(df):
    """
    Prepares the data by modifying the given DataFrame.

    :param df: The DataFrame containing the data to be prepared.
    :return: The prepared DataFrame grouped by 'date' and 'location'.

    """
    df['location'] = df.apply(lambda x: x['location'].split('-')[0], axis=1)
    df['name'] = df['species name']
    grp = df.groupby(['date', 'location'])
    return grp


def get_location_info(lat, lon):
    """
    :param lat: float representing the latitude of the location
    :param lon: float representing the longitude of the location
    :return: dictionary containing the state and country information of the given location

    This method takes latitude and longitude as input parameters and returns a dictionary with the state and
    country information of the given location.

    Example usage:

    >>> get_location_info(37.7749, -122.4194)
    {'state': 'California', 'country': 'US'}
    """
    location = geolocator.reverse(f"{lat},{lon}").raw['address']
    code = [c for c in location.keys() if 'ISO3166' in c][0]
    return {'state': location[code].split('-')[1], 'country': location['country_code'].upper()}


def get_distance_and_protocol(data):
    """
    :param data: Pandas DataFrame containing latitude and longitude coordinates for each location.
    :return: Dictionary with keys 'distance' and 'protocol'. 'distance' is the total distance traveled between
    locations in miles, and 'protocol' is either 'traveling' if there was any distance traveled, or 'stationary'
    if there was no distance traveled.

    """
    miles = 0
    p_lat = data.iloc[0]['lat']
    p_lon = data.iloc[0]['lng']
    for idx, r in data.iterrows():
        if r['id'] == data.iloc[0]['id']:
            continue
        lat = str(r['lat'])
        lon = str(r['lng'])
        miles += distance.distance((lat, lon), (p_lat, p_lon)).miles
        p_lat = lat
        p_lon = lon
    return {'distance': miles, 'protocol': 'traveling' if (miles > 0) else 'stationary'}


def parse_group(g, header):
    """
    The `parse_group` method takes two parameters and returns two values.

    :param g: A tuple containing the date and location information of a group.
    :param header: A dictionary representing the header information.

    :return: A tuple containing the observation data and the updated header information.
    """
    g_date, g_loc = g[0]
    g_df = g[1].sort_values(by=['time'])
    g_year, g_mm, g_dd = re.findall(r'(\d{4})-(\d{2})-(\d{2})', g_date, re.DOTALL)[0]
    g_date = f'{g_mm}/{g_dd}/{g_year}'
    row = g_df.iloc[0]
    start_time = row['time']
    last_time = g_df.iloc[-1]['time']
    s_time = datetime.datetime.strptime(start_time, "%H:%M:%S")
    l_time = datetime.datetime.strptime(last_time, "%H:%M:%S")
    duration = int(1 + (l_time - s_time).total_seconds() / 60)
    coords_info = get_location_info(str(row['lat']), str(row['lng']))
    dist_protocol_info = get_distance_and_protocol(g_df)

    header['Location'].append(g_loc)
    header['Latitude'].append(str(row['lat']))
    header['Longitude'].append(str(row['lng']))
    header['Date'].append(g_date)
    header['Start Time'].append(start_time)
    header['State'].append(coords_info['state'])
    header['Country'].append(coords_info['country'])
    header['Protocol'].append(dist_protocol_info['protocol'])
    header['Num Observers'].append(1)
    header['Duration (min)'].append(duration)
    header['All Obs Reported (Y/N)'].append('Y')
    header['Dist Traveled (Miles)'].append(dist_protocol_info['distance'])
    header['Area Covered (Acres)'].append('')
    header['Notes'].append('')
    obs = g_df[['name', 'number']]

    return obs, header


def write_csv(output_file, header, obs, df):
    """
    Write data to a CSV file.

    :param output_file: str, the path to the output CSV file.
    :param header: dict, a dictionary containing header information for the CSV file.
    :param obs: list, a list of data objects.
    :param df: pandas.DataFrame, a DataFrame containing data.
    :return: None
    """
    with open(output_file, 'w') as csv_file:
        wr = csv.writer(csv_file, delimiter=',')
        for k, v in header.items():
            row = ['' if k == 'Location' else k, ''] + v
            wr.writerow(row)
        names = {species: [species] + [''] * (len(obs) + 1) for species in df['name'].unique()}
        for i, o in enumerate(obs):
            for x in o.iterrows():
                name, nr = x[1]['name'], x[1]['number']
                names[name][i + 2] = nr
        for r in names.values():
            wr.writerow(r)


def export_to_ebird(output_file, start_date, end_date):
    """
    :param output_file: The path to the output file where the eBird data will be exported.
    :param start_date: The start date for querying the database.
    :param end_date: The end date for querying the database.
    :return: None|str None if OK, else a status message

    This method exports bird observation data from a MySQL database to eBird format.
    The exported data will be written to the specified output file.

    The method first initializes a dictionary called `header` that represents the eBird data header.
    It contains keys for various fields like `Location`, `Latitude`, `Longitude`, etc.
    The values for these keys will be populated later during the data parsing process.

    The method then establishes a connection to the MySQL database and queries the data for the specified date range.
    If no data is found, a message is printed and the method exits.

    Next, the method prepares the data for export by grouping it based on location.
    Each group is then parsed to extract relevant information and append it to the `obs` list.
    Additionally, the `header` dictionary is updated with the appropriate values.

    Finally, the method writes the CSV file using the `write_csv` function, passing the output file path,
    the `header` dictionary, the `obs` list, and the original data DataFrame.
    """
    header = {
        'Location': [],
        'Latitude': [],
        'Longitude': [],
        'Date': [],
        'Start Time': [],
        'State': [],
        'Country': [],
        'Protocol': [],
        'Num Observers': [],
        'Duration (min)': [],
        'All Obs Reported (Y/N)': [],
        'Dist Traveled (Miles)': [],
        'Area Covered (Acres)': [],
        'Notes': []
    }
    obs = []

    sqlEngine, db = db_conn()
    df = query_database(start_date, end_date, sqlEngine, db)
    if len(df) == 0:
        return 'Nothing to export, check if database is running!'

    grp = prepare_data(df)
    for g in grp:
        o, header = parse_group(g, header)
        obs.append(o)

    write_csv(output_file, header, obs, df)


def main():
    """
    Main method for executing the program.

    :return: None
    """
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i',
        '--import_obs',
        required=False,
        help='Import a .CSV file from observations.be and store it in MySQL db'
    )

    parser.add_argument(
        '-o',
        '--ebird_output_file',
        required=False,
        help='Export observation as ebird .CSV file path'
    )

    parser.add_argument(
        '-f',
        '--from_date',
        required=False,
        help='Export observation as ebird .CSV file as from ISO date (yyyy-mm-dd)'
    )

    parser.add_argument(
        '-t',
        '--to_date',
        required=False,
        help='Export observation up to this ISO date (yyy-mm-dd)'
    )

    args = parser.parse_args()

    if args.import_obs:
        import_obs(args.import_obs)

    if args.ebird_output_file:
        export_to_ebird(args.ebird_output_file, args.from_date, args.to_date)


if __name__ == "__main__":
    main()
