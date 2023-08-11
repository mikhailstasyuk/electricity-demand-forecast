#!/usr/bin/env python
# coding: utf-8

# In[118]:


import argparse
import requests

import psycopg2
from psycopg2 import extras
from psycopg2.errors import DuplicateTable, OperationalError, UniqueViolation


# In[119]:


def parse_arguments():
    """Parse command line arguments.

    Args:
        None
    Returns:
        args (argparse.Namespace) : Arguments object
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-k', '--api_key', type=str, help="API key to use", required=True)
    parser.add_argument('-sd', '--start', type=str, help="Start date y-m-d", required=True)
    parser.add_argument('-ed', '--end', type=str, help="End date y-m-d", required=True)

    # Parse the arguments
    args = parser.parse_args()
    return args 


# In[120]:


def request_data(url):
    response = requests.get(url)
    
    if response.status_code == 200:  # Success
        return response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None


# In[121]:


def create_table(
    tab_name: str,
    tab_schema: str,
    dbname: str,
    user: str,
    password: str,
    host: int,
    port: int,
    connect_timeout: int
) -> None:
    
    conn_params = {
        'dbname': dbname,
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'connect_timeout': connect_timeout
    }
    
    # Connect to your postgres DB
    try:
        conn = psycopg2.connect(**conn_params)
    
    except OperationalError as e:
        raise OperationalError(f"Error connecting to the database: {e}")

    cur = conn.cursor()

    # Define the CREATE TABLE statement
    create_table_query = f'''
    CREATE TABLE {tab_name} (
        id SERIAL PRIMARY KEY, 
        {tab_schema}
    );
    '''
    
    try:
        # Execute the query
        cur.execute(create_table_query)

        # Commit the changes
        conn.commit()
    
    except DuplicateTable as e:
        cur.close()
        conn.close()
        raise DuplicateTable(f"The table {tab_name} already exists.")
    
    # Close the cursor and connection
    cur.close()
    conn.close()


# In[122]:


def setup_and_create_table(params, key, tab_schemas):
    try:
        tab_name, tab_schema = key, tab_schemas.get(key, -1)
        params['tab_name'] = tab_name
        params['tab_schema'] = tab_schema

        create_table(**params)
    except DuplicateTable as e:
        print(str(e))


# In[123]:


def populate_table(
    data: list,
    schema: list,
    tab_name: str,
    dbname: str,
    user: str,
    password: str,
    host: int,
    port: int,
    connect_timeout: int
) -> None:
    
    conn_params = {
        'dbname': dbname,
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'connect_timeout': connect_timeout
    }
    
    # Connect to your postgres DB
    try:
        conn = psycopg2.connect(**conn_params)
    
    except OperationalError as e:
        raise OperationalError(f"Error connecting to the database: {e}")

    cur = conn.cursor()

    # Insert data
    extras.execute_values(
        cur,
        f"""INSERT INTO {tab_name} ({schema}) 
        VALUES %s
        ON CONFLICT ({schema})
        DO NOTHING;""",
        data
    )

    conn.commit()
    cur.close()
    conn.close()


# In[124]:


tab_schemas = {
    'demand': 
        '''
        period VARCHAR(100),
        subba VARCHAR(100),
        subba_name VARCHAR(100),	
        parent VARCHAR(100),	
        parent_name VARCHAR(100),	
        timezone VARCHAR(100),	
        value INTEGER,	
        value_units VARCHAR(100),
        UNIQUE (period, subba, subba_name, parent, parent_name, timezone, value, value_units)
        ''',

    'weather_hist':
        '''
        time VARCHAR(100) UNIQUE,
        weathercode INTEGER,
        temperature_2m_max	REAL,
        temperature_2m_min	REAL,
        temperature_2m_mean REAL,
        UNIQUE (time, weathercode, temperature_2m_max, temperature_2m_min, temperature_2m_mean)
        ''',

    'weather_latest':
        '''
        time VARCHAR(100) UNIQUE, 
        temperature_2m_max REAL, 
        temperature_2m_min REAL, 
        UNIQUE (time,  temperature_2m_max, temperature_2m_min)
        '''
}


# In[125]:


def construct_url(api, params):
    start_date = params.get('start_date', None)
    end_date = params.get('end_date', None)
    offset = params.get('offset', None)
    chunk_len = params.get('chunk_len', None)
    api_key = params.get('api_key', None)

    if api == 'demand':
        url = f'https://api.eia.gov/v2/electricity/rto/' +\
        f'daily-region-sub-ba-data/data/?frequency=daily&data[0]=value' + \
        f'&facets[subba][]=ZONJ&start={start_date}&end={end_date}' + \
        f'&sort[0][column]=period&sort[0][direction]=asc&offset={offset}' + \
        f'&length={chunk_len}&api_key={api_key}'

    elif api == 'weather_hist':
        url = f'https://archive-api.open-meteo.com/v1' + \
        f'/archive?latitude=52.52&longitude=13.41&start_date={start_date}' + \
        f'&end_date={end_date}&daily=weathercode,temperature_2m_max,' + \
        f'temperature_2m_min,temperature_2m_mean' + \
        f'&timezone=America%2FNew_York'

    elif api == 'weather_latest':
        url = f'https://api.open-meteo.com/v1/forecast?' + \
        f'latitude=52.52&longitude=13.41&hourly=temperature_2m&daily=' + \
        f'temperature_2m_max,temperature_2m_min&timezone=America%2F' + \
        f'New_York&past_days=7'
    return url


# In[126]:


# Python script
# args = parse_arguments()
# api_key = args.api_key
# start_date = args.start
# end_date = args.end

# Notebook
api_key = ''
start_date = '2018-06-01'
end_date = '2023-07-30'

general_params = {
    'dbname': 'db_demand',
    'user': 'dbuser',
    'password': '123',
    'host': 'localhost',
    'port': '5432',
    'connect_timeout': 5
} 

create_params = {
    'tab_name': None,
    'tab_schema': None,
    'dbname': general_params['dbname'],
    'user':  general_params['user'],
    'password':  general_params['password'],
    'host':  general_params['host'],
    'port':  general_params['port'],
    'connect_timeout': general_params['connect_timeout']
}

populate_params = {
    'data': None,
    'schema': None,
    'tab_name': None,
    'dbname': general_params['dbname'],
    'user':  general_params['user'],
    'password':  general_params['password'],
    'host':  general_params['host'],
    'port':  general_params['port'],
    'connect_timeout': general_params['connect_timeout']
}

request_params = {
    'api_key': api_key,
    'start_date': start_date,
    'end_date': end_date,
    'chunk_len': 5000,
    'offset': 0
}
apis = ['demand', 'weather_hist', 'weather_latest']

duplicates_msg = 'Error: Data already exists during storage attempt.'

def main():
    for api in apis:
        url = construct_url(api, request_params)
        data = request_data(url)
        if data:
            if api == 'demand':
                total_rows = data['response']['total']
                print("Total rows:", total_rows)
                chunk_len = request_params.get('chunk_len', None)
                total_chunks = int(total_rows / chunk_len) + 1
                print("Total chunks to download:", total_chunks)            

                setup_and_create_table(create_params, api, tab_schemas)
                params = request_params.copy()
                for i in range(total_chunks):
                    url = construct_url(api, params)
                    data = request_data(url)
                    data_list = data['response']['data']
                    data_tuples = [tuple(d.values()) for d in data_list]
                    schema = ", ".join(data_list[0].keys()).replace("-", "_")

                    populate_params['data'] = data_tuples
                    populate_params['tab_name'] = api
                    populate_params['schema'] = schema

                    try:
                        populate_table(**populate_params)
                        # print(f"Successfuly stored {len(data_tuples)} rows.")

                    except UniqueViolation as e:
                        print(duplicates_msg)
                    params['offset'] += chunk_len

            if api == 'weather_hist':
                data_dict = data['daily']
                data_tuples = [values for values in zip(*data_dict.values())]
                schema = ", ".join(data_dict.keys())

                setup_and_create_table(create_params, api, tab_schemas)

                populate_params['data'] = data_tuples
                populate_params['tab_name'] = api
                populate_params['schema'] = schema
                try:
                    populate_table(**populate_params)
                    # print(f"Successfuly stored {len(data_tuples)} rows.")

                except UniqueViolation as e:
                    print(duplicates_msg)

            if api == 'weather_latest':
                data_dict = data['daily']
                data_tuples = [values for values in zip(*data_dict.values())]
                schema = ", ".join(data_dict.keys())
                setup_and_create_table(create_params, api, tab_schemas)

                populate_params['data'] = data_tuples
                populate_params['tab_name'] = api
                populate_params['schema'] = schema

                try:
                    populate_table(**populate_params)
                    # print(f"Successfuly stored {len(data_tuples)} rows.")

                except UniqueViolation as e:
                    print(duplicates_msg)


# In[127]:


if __name__ == "__main__":
    main()

