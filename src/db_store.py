#!/usr/bin/env python
# coding: utf-8
import os
import hydra
import requests
from datetime import datetime

from dotenv import load_dotenv

import psycopg2
from psycopg2 import extras
from psycopg2.errors import OperationalError


class URLParser(object):
    def __init__(self, config):
        self.config = config
        
        self.subba = config.data.api.query.SUBBA
        self.start_date = config.data.api.query.START_DATE
        self.end_date = config.data.api.query.END_DATE
        self.offset = config.data.api.query.OFFSET
        self.chunk_len = config.data.api.query.CHUNK_LEN
        self.api_key = os.getenv('API_KEY')

    def construct_url(self, tab_name):
        replacements = {
            "<SUBBA_CODE>": str(self.subba),
            "<START_DATE>": str(self.start_date),
            "<OFFSET>": str(self.offset),
            "<CHUNK_LEN>": str(self.chunk_len),
            "<API_KEY>": str(self.api_key)
        }

        url = eval('self.config.data.api.urls.' + tab_name.upper())
        url = url.replace("\n", "")

        if self.end_date == 'today':
            today = datetime.today()
            url = url.replace("<END_DATE>", str(today.strftime('%Y-%m-%d')))
        else:
            url = url.replace(
                "<END_DATE>", str(self.end_date))

        for old, new in replacements.items():
            url = url.replace(old, new)
        return url
        
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

    def table_exists(self, table_name):
        """
        Check if the given table already exists in the database.
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (table_name,))
        exists = cur.fetchone()[0]
        cur.close()
        return exists
    
    def create_table(self, tab_name, tab_schema):
        if self.conn is not None:
            if self.table_exists(tab_name):
                print(f"Table {tab_name} already exists. Using existing table.")

            else:
                cur = self.conn.cursor()
                cur.execute(tab_schema)
                self.conn.commit()
                cur.close()
        else:
            print("Not connected to a db.")
    
    def request_data(self, url):
        response = requests.get(url)

        if response.status_code == 200:  # Success
            return response.json()
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return None


    def insert(self,
        data: list,
        schema: list,
        tab_name: str,
    ) -> None:

        cur = self.conn.cursor()

        # Insert data
        extras.execute_values(
            cur,
            f"""INSERT INTO {tab_name} ({schema}) 
            VALUES %s
            ON CONFLICT ({schema})
            DO NOTHING;""",
            data
        )

        self.conn.commit()
        cur.close()

@hydra.main(config_path='conf', config_name='config.yaml')
def main(config):
    load_dotenv()
    # Connect to db
    db_store = DatabaseHandler(config)
    db_store.connect()

    # Create a table
    tab_name = config.data.tab_params.tabname
    tab_schema = eval(
        f'config.data.tab_params.tab_schema.{tab_name}'
    )

    db_store.create_table(tab_name, tab_schema)

    urlparser = URLParser(config)
    url = urlparser.construct_url(tab_name)

    data = db_store.request_data(url)

    if data:
        if tab_name == 'demand':
            total_rows = data['response']['total']
            print("Total rows:", total_rows)
            chunk_len = urlparser.chunk_len
            total_chunks = int(total_rows / chunk_len) + 1
            print("Total chunks to download:", total_chunks)            

            for i in range(total_chunks):
                url = urlparser.construct_url(tab_name)
                data = db_store.request_data(url)
                data_list = data['response']['data']
                data_tuples = [tuple(d.values()) for d in data_list]
                schema = ", ".join(data_list[0].keys()).replace("-", "_")

                try:
                    db_store.insert(
                        data=data_tuples,
                        schema=schema,
                        tab_name=tab_name
                    )
                except Exception as e:
                    print(str(e))
                
                urlparser.offset += chunk_len

    # Close the connection
    db_store.close()
if __name__ == "__main__":
    main()