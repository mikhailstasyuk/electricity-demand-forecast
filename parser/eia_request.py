#!/usr/bin/env python
# coding: utf-8

import requests
import pickle
import os
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-k', '--api_key', type=str, help="API key to use", required=True)
    parser.add_argument('-sd', '--start', type=str, help="Start date y-m-d", required=True)
    parser.add_argument('-ed', '--end', type=str, help="End date y-m-d", required=True)
    parser.add_argument('-p', '--save_to', type=str, help="Folder to save the data", default=".")
    parser.add_argument('-l', '--chunk_len', type=int, help="Number of rows in downloaded chunk", default=5000)

    # Parse the arguments
    args = parser.parse_args()
    return args 

def get_json_data(url):
    response = requests.get(url)

    if response.status_code == 200:  # Success
        return response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

def save_to_pickle(data, fname):
    with open(fname, 'wb') as f_out:
        pickle.dump(data['response'], f_out)

def main():
    args = parse_arguments()
    api_key = args.api_key
    start_date = args.start
    end_date = args.end
    output_path = args.save_to
    chunk_len = args.chunk_len

    # Build a request
    url = "https://api.eia.gov/v2/electricity/rto/daily-region-sub-ba-data/data/?frequency=daily&data[0]=value&start={}&end={}&sort[0][column]=period&sort[0][direction]=desc&offset=0&length={}&api_key={}".format(start_date, end_date, chunk_len, api_key)
    
    print("Getting data...")
    data = get_json_data(url)

    fname = output_path + '/' + '{}-{}.bin'.format(start_date, end_date)
    if data:
        total_rows = data['response']['total']
        print("Total rows:", total_rows)

        print("Saving to {}...".format(fname))
        try:
            save_to_pickle(data, fname)
            print('Saved.')

        except FileNotFoundError:
            print('Saving failed. No such folder {}.'.format(output_path))

if __name__ == "__main__":
    main()