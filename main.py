import pandas as pd
import sqlalchemy.exc
from sqlalchemy import create_engine
import warnings
from yaml import load, Loader
from glob import glob
from sys import exit
from os.path import join
import argparse
import re
from geopy.geocoders import Nominatim, options
from geopy import distance
import certifi
import ssl
import datetime
import csv

ctx = ssl.create_default_context(cafile=certifi.where())
options.default_ssl_context = ctx
options.default_user_agent = 'myapp'
geolocator = Nominatim(scheme='http')
args = None

warnings.simplefilter(action='ignore', category=FutureWarning)


def get_secret(key: str, base_url='', token='', cert="root_ca.pem") -> tuple:
    """
    :param key: The ID of the secret to retrieve
    :param base_url: The base URL of the Vault server (default is VAULT_ADDR)
    :param token: The token to authenticate with the Vault server (default is TOKEN)
    :param cert: The path to the certificate file to verify the Vault server's SSL certificate (default is "root_ca.pem")
    :return: A tuple containing the key-value pairs of the secret (None, None) if the secret retrieval fails

    This method retrieves a secret from a Vault server using the provided ID. It sends a GET request to the Vault server with the necessary headers and authentication token. If the request is successful (status code 200), the method extracts the key-value pairs from the response JSON and returns them as a tuple. If the request fails, the method prints an HTTP error message and returns (None, None).
    """
    import requests
    try:
        secrets = load(open('secrets.yml', 'r'), Loader=Loader)
        token = secrets['db']['TOKEN']
        base_url = secrets['db']['VAULT_ADDR']
    except IOError:
        return None, None
    except KeyError:
        return None, None

    headers = {"X-Vault-Token": token}
    uri = "/v1/secret/data/"
    url = f"{base_url}{uri}{key}"
    resp = requests.get(url, headers=headers, verify=cert)
    if resp.status_code == 200:
        secret = resp.json()["data"]["data"]
        for username, password in secret.items():
            return username, password
    else:
        print(f"http error {resp.status_code}")
        return None, None


def get_config():
    # read config file
    try:
        return load(open('config.yml', 'r'), Loader=Loader)
    except IOError:
        print('Config file not found!')
        return None


# read config file
config = get_config()


def db_conn():
    user, pwd = get_secret('comptes')
    host = config['mysql']['host']
    port = config['mysql']['port']
    db = config['mysql']['db']
    return create_engine('mysql+pymysql://' + user + ':' + pwd + '@' + host + ':' + str(port) + '/' + db,
                         pool_recycle=3600)


def import_obs():
    # read input data
    d = pd.DataFrame()
    for f in glob(join(config['paths']['in'], '*.csv')):
        df = pd.read_csv(f, delimiter=',', engine='python', encoding='UTF_8').fillna('')
        d = pd.concat([d, df])

    # and save to mySQL db
    sqlEngine = db_conn()
    try:
        with sqlEngine.begin() as cnx:
            d.to_sql(name=config['mysql']['db'], con=cnx, if_exists='replace')
        # with sqlEngine.begin() as cnx:
        #     sql = f"REPLACE INTO {config['mysql']['db']} SELECT * FROM temp_table"
        #     cnx.execute(sql)

    except sqlalchemy.exc.OperationalError:
        print('Cannot connect to MySQL database - check if running')
        exit(-1)


def export_to_ebird(output_file, start_date, end_date):

    # CSV row's header
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

    # Read the database
    sqlEngine = db_conn()

    if end_date:
        query = f'select * from {config["mysql"]["db"]} where date >= "{start_date}"'
    else:
        query = f'select * from {config["mysql"]["db"]} where date between "{start_date}" and "{end_date}"'

    try:
        df = pd.read_sql(query, con=sqlEngine)
    except sqlalchemy.exc.OperationalError:
        print('Cannot connect to MySQL database - check if running')
        exit(-1)

    if len(df) == 0:
        print('Nothing to export')
        exit(0)

    # pivot data per date and location
    # simplify location to the city
    df['location'] = df.apply(lambda x: x['location'].split('-')[0], axis=1)
    # df['name'] = df['species name'] + ' - ' + df['scientific name']
    df['name'] = df['species name']
    grp = df.groupby(['date', 'location'])
    for g in grp:
        g_date, g_loc = g[0]
        g_df = g[1]
        g_df = g_df.sort_values(by=['time'])

        # convert date in mm/dd/yyy
        g_year, g_mm, g_dd = re.findall(r'(\d{4})-(\d{2})-(\d{2})', g_date, re.DOTALL)[0]
        g_date = f'{g_mm}/{g_dd}/{g_year}'
        # get info from first row to initiate the header
        row = g_df.iloc[0]
        ref = row['id']

        # Time & duration calculation
        start_time = row['time']
        last_time = g_df.iloc[-1]['time']
        s_time = datetime.datetime.strptime(start_time, "%H:%M:%S")
        l_time = datetime.datetime.strptime(last_time, "%H:%M:%S")
        delta = l_time - s_time
        duration = int(1 + delta.total_seconds() / 60)

        # Location, and distance measurement
        latitude = str(row['lat'])
        longitude = str(row['lng'])
        location = geolocator.reverse(latitude+","+longitude).raw['address']

        miles = 0
        p_lat = latitude
        p_lon = longitude
        for idx, r in g_df.iterrows():
            # skip first row, already initialized
            if r['id'] == ref:
                continue
            lat = str(r['lat'])
            lon = str(r['lng'])
            delta = distance.distance((lat, lon), (p_lat, p_lon)).miles
            miles += delta
            p_lat = lat
            p_lon = lon

        protocol = 'traveling' if (miles > 0) else 'stationary'

        # fill header
        header['Location'].append((g_loc))
        header['Latitude'].append(latitude)
        header['Longitude'].append(longitude)
        header['Date'].append(g_date)
        header['Start Time'].append(start_time)
        code = [c for c in location.keys() if 'ISO3166' in c][0]
        header['State'].append(location[code].split('-')[1])
        header['Country'].append(location['country_code'].upper())
        header['Protocol'].append(protocol)
        header['Num Observers'].append(1)
        header['Duration (min)'].append(duration)
        header['All Obs Reported (Y/N)'].append('Y')
        header['Dist Traveled (Miles)'].append(miles)
        header['Area Covered (Acres)'].append('')
        header['Notes'].append('')

        # fill observations
        grp_obs = g_df[['name', 'number']]
        obs.append(grp_obs)

    # Assemble output
    csv_file = open(output_file, 'w')
    wr = csv.writer(csv_file, delimiter=',')

    # generate header
    for k, v in header.items():
        row = []

        if k == 'Location':
            row.append('')
        else:
            row.append(k)
        row.append('')
        # for x in v:
        #    row.append(x)
        row += v
        wr.writerow(row)

    # generate observations list
    names = dict()

    for l in list(df['name'].unique()):
        names[l] = [l] + ['']*(len(obs)+1)

    for i, o in enumerate(obs):
        for x in o.iterrows():
            name = x[1]['name']
            nr = x[1]['number']
            names[name][i+2]=nr

    for r in names.values():
        wr.writerow(r)

    csv_file.close()


def main():
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
        import_obs()

    if args.ebird_output_file:
        export_to_ebird(args.ebird_output_file, args.from_date, args.to_date)


if __name__ == "__main__":
    main()
