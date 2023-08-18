#!/usr/bin/env python
# coding: utf-8
import hydra
import argparse
import requests
from datetime import datetime, timedelta

import psycopg2
from psycopg2 import extras
from psycopg2.errors import DuplicateTable, OperationalError, UniqueViolation

class DatabaseHandler(object):
    def __init__(self, config):
        self.config = config
        self.conn = None
        
    def connect(self):
        # Connection logic
        conn_params = {
        'dbname': self.config.data.conn_params.dbname,
        'user': self.config.data.conn_params.user,
        'password': self.config.data.conn_params.password,
        'host': self.config.data.conn_params.host,
        'port': self.config.data.conn_params.port,
        'connect_timeout': self.config.data.conn_params.connect_timeout
      }
        
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(**conn_params)

            except OperationalError as e:
                raise OperationalError(f"Error connecting to the database: {e}")
        else:
            print("Already connected.")
    
    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def create_table(self, tab_name, tab_schema):
        if self.conn is not None:
            cur = self.conn.cursor()

            try:
                # Execute the query
                cur.execute(tab_schema)

                # Commit the changes
                self.conn.commit()
            
            except DuplicateTable as e:
                cur.close()
                self.conn.close()
                raise DuplicateTable(f"The table {tab_name} already exists.")
            
            # Close the cursor and connection
            cur.close()
        else:
            print("Not connected to a db.")
    
    def parse_api_url(self, url):
        replacements = {
                "<SUBBA_CODE>": str(self.config.data.api.query.SUBBA),
                "<START_DATE>": str(self.config.data.api.query.START_DATE),
                "<OFFSET>": str(self.config.data.api.query.OFFSET),
                "<CHUNK_LEN>": str(self.config.data.api.query.CHUNK_LEN),
                "<API_KEY>": str(self.config.data.api.query.API_KEY)
            }
        url = url.replace("\n", "")
        if self.config.data.api.query.END_DATE == 'today':
            yesterday = datetime.today() - timedelta(1)
            url = url.replace("<END_DATE>", yesterday.strftime('%Y-%m-%d'))
        else:
            url = url.replace(
                "<END_DATE>", str(self.config.data.api.query.END_DATE)
            )

        for old, new in replacements.items():
            url = url.replace(old, new)
        return url
    
    def request_data(self, url):
        response = requests.get(url)

        if response.status_code == 200:  # Success
            return response.json()
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return None


    def insert(self, data):
        # Insert logic
        pass

    def query(self, query):
        # Query logic
        pass
    
    def close(self):
        # Close connection logic
        pass

@hydra.main(config_path='conf', config_name='config.yaml')
def main(config):
    # Connect to db
    db_store = DatabaseHandler(config)
    db_store.connect()
    
    # Create a table
    tab_name = config.data.tab_params.tabname
    tab_schema = eval(
        f'config.data.tab_params.tab_schema.{tab_name}'
    )
    print(f'Creating tab {tab_name}\n{tab_schema}')
    try:
        db_store.create_table(tab_name, tab_schema)
    except:
        print("Exists")      

    url = config.data.api.urls.DEMAND
    url_query = db_store.parse_api_url(url)
    
    # Close the connection
    db_store.close()
if __name__ == "__main__":
    main()

# def parse_arguments():
#     """Parse command line arguments.

#     Args:
#         None
#     Returns:
#         args (argparse.Namespace) : Arguments object
#     """
#     parser = argparse.ArgumentParser()

#     parser.add_argument('-k', '--api_key', type=str, help="API key to use", required=True)
#     parser.add_argument('-sd', '--start', type=str, help="Start date y-m-d", required=True)
#     parser.add_argument('-ed', '--end', type=str, help="End date y-m-d", required=True)

#     # Parse the arguments
#     args = parser.parse_args()
#     return args 

# def request_data(url):
#     response = requests.get(url)
    
#     if response.status_code == 200:  # Success
#         return response.json()
#     else:
#         print(f"Failed to fetch data. Status code: {response.status_code}")
#         return None

# def create_table(
#     tab_name: str,
#     tab_schema: str,
#     dbname: str,
#     user: str,
#     password: str,
#     host: int,
#     port: int,
#     connect_timeout: int
# ) -> None:
    
#     conn_params = {
#         'dbname': dbname,
#         'user': user,
#         'password': password,
#         'host': host,
#         'port': port,
#         'connect_timeout': connect_timeout
#     }
    
#     # Connect to your postgres DB
#     try:
#         conn = psycopg2.connect(**conn_params)
    
#     except OperationalError as e:
#         raise OperationalError(f"Error connecting to the database: {e}")

#     cur = conn.cursor()

#     # Define the CREATE TABLE statement
#     create_table_query = f'''
#     CREATE TABLE {tab_name} (
#         id SERIAL PRIMARY KEY, 
#         {tab_schema}
#     );
#     '''
    
#     try:
#         # Execute the query
#         cur.execute(create_table_query)

#         # Commit the changes
#         conn.commit()
    
#     except DuplicateTable as e:
#         cur.close()
#         conn.close()
#         raise DuplicateTable(f"The table {tab_name} already exists.")
    
#     # Close the cursor and connection
#     cur.close()
#     conn.close()

# def setup_and_create_table(params, key, tab_schemas):
#     try:
#         tab_name, tab_schema = key, tab_schemas.get(key, -1)
#         params['tab_name'] = tab_name
#         params['tab_schema'] = tab_schema

#         create_table(**params)
#     except DuplicateTable as e:
#         print(str(e))

# def populate_table(
#     data: list,
#     schema: list,
#     tab_name: str,
#     dbname: str,
#     user: str,
#     password: str,
#     host: int,
#     port: int,
#     connect_timeout: int
# ) -> None:
    
#     conn_params = {
#         'dbname': dbname,
#         'user': user,
#         'password': password,
#         'host': host,
#         'port': port,
#         'connect_timeout': connect_timeout
#     }
    
#     # Connect to your postgres DB
#     try:
#         conn = psycopg2.connect(**conn_params)
    
#     except OperationalError as e:
#         raise OperationalError(f"Error connecting to the database: {e}")

#     cur = conn.cursor()

#     # Insert data
#     extras.execute_values(
#         cur,
#         f"""INSERT INTO {tab_name} ({schema}) 
#         VALUES %s
#         ON CONFLICT ({schema})
#         DO NOTHING;""",
#         data
#     )

#     conn.commit()
#     cur.close()
#     conn.close()

# tab_schemas = {
#     'demand': 
#         '''
#         period VARCHAR(100),
#         subba VARCHAR(100),
#         subba_name VARCHAR(100),	
#         parent VARCHAR(100),	
#         parent_name VARCHAR(100),	
#         timezone VARCHAR(100),	
#         value INTEGER,	
#         value_units VARCHAR(100),
#         UNIQUE (period, subba, subba_name, parent, parent_name, timezone, value, value_units)
#         ''',
# }

# def construct_url(api, params):
#     start_date = params.get('start_date', None)
#     end_date = params.get('end_date', None)
#     offset = params.get('offset', None)
#     chunk_len = params.get('chunk_len', None)
#     api_key = params.get('api_key', None)

#     if api == 'demand':
#         url = f'https://api.eia.gov/v2/electricity/rto/' +\
#         f'daily-region-sub-ba-data/data/?frequency=daily&data[0]=value' + \
#         f'&facets[subba][]=ZONJ&start={start_date}&end={end_date}' + \
#         f'&sort[0][column]=period&sort[0][direction]=asc&offset={offset}' + \
#         f'&length={chunk_len}&api_key={api_key}'
#     return url

# # Python script
# args = parse_arguments()
# api_key = args.api_key
# start_date = args.start
# end_date = args.end

# general_params = {
#     'dbname': 'db_demand',
#     'user': 'dbuser',
#     'password': '123',
#     'host': 'localhost',
#     'port': '5432',
#     'connect_timeout': 5
# } 

# create_params = {
#     'tab_name': None,
#     'tab_schema': None,
#     'dbname': general_params['dbname'],
#     'user':  general_params['user'],
#     'password':  general_params['password'],
#     'host':  general_params['host'],
#     'port':  general_params['port'],
#     'connect_timeout': general_params['connect_timeout']
# }

# populate_params = {
#     'data': None,
#     'schema': None,
#     'tab_name': None,
#     'dbname': general_params['dbname'],
#     'user':  general_params['user'],
#     'password':  general_params['password'],
#     'host':  general_params['host'],
#     'port':  general_params['port'],
#     'connect_timeout': general_params['connect_timeout']
# }

# request_params = {
#     'api_key': api_key,
#     'start_date': start_date,
#     'end_date': end_date,
#     'chunk_len': 5000,
#     'offset': 0
# }
# apis = ['demand']

# duplicates_msg = 'Error: Data already exists during storage attempt.'

# def main():
#     for api in apis:
#         url = construct_url(api, request_params)
#         data = request_data(url)
#         if data:
#             if api == 'demand':
#                 total_rows = data['response']['total']
#                 print("Total rows:", total_rows)
#                 chunk_len = request_params.get('chunk_len', None)
#                 total_chunks = int(total_rows / chunk_len) + 1
#                 print("Total chunks to download:", total_chunks)            

#                 setup_and_create_table(create_params, api, tab_schemas)
#                 params = request_params.copy()
#                 for i in range(total_chunks):
#                     url = construct_url(api, params)
#                     data = request_data(url)
#                     data_list = data['response']['data']
#                     data_tuples = [tuple(d.values()) for d in data_list]
#                     schema = ", ".join(data_list[0].keys()).replace("-", "_")

#                     populate_params['data'] = data_tuples
#                     populate_params['tab_name'] = api
#                     populate_params['schema'] = schema

#                     try:
#                         populate_table(**populate_params)

#                     except UniqueViolation as e:
#                         print(duplicates_msg)
#                     params['offset'] += chunk_len

# if __name__ == "__main__":
#     main()

