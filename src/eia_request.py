#!/usr/bin/env python
# coding: utf-8

import requests
import pickle
import os
import argparse
import pandas as pd

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
    parser.add_argument('-to', '--save_to', type=str, help="Folder to save the data", default=".")
    parser.add_argument('-l', '--chunk_len', type=int, help="Number of rows in downloaded chunk", default=5000)

    # Parse the arguments
    args = parser.parse_args()
    return args 

def get_json_data(url):
    """Fetch the data from the provided url.
    
    Args:
        url (str)  : a request url
    Returns:
        data (str) : json formatted data
    """
    response = requests.get(url)

    if response.status_code == 200:  # Success
        data = response.json()
        return data
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

def generate_url(start_date, end_date, offset, chunk_len, api_key):
    """Create a url list of each chunk of data to be fetched.
    
    Args:
        total_chunks 
        start_date
        end_date
        offset
        chunk_len 
        api_key
    Returns:
        urls (list) : A list of data chunk urls to be downloaded
    """
    url = 'https://api.eia.gov/v2/electricity/rto/daily-region-sub-ba-data/data/?frequency=daily&data[0]=value&start={}&end={}&sort[0][column]=period&sort[0][direction]=desc&offset={}&length={}&api_key={}'.format(start_date, end_date, offset, chunk_len, api_key)
    return url

def save_to_pickle(data, fname):
    """Save the fetched data to a pickle file.
    
    Args:
        data ()  : A Pandas DataFrame containing data
        fname () : A file path to save the data to
    Returns:
        None
    """
    with open(fname, 'wb') as f_out:
        pickle.dump(data, f_out)

def main():
    args = parse_arguments()
    api_key = args.api_key
    start_date = args.start
    end_date = args.end
    output_path = args.save_to
    chunk_len = args.chunk_len
    offset = 0

    print("Getting data...")
    
    # Here we're just obtaining the total number of rows to download
    url = generate_url(start_date, end_date, offset, chunk_len, api_key)
    
    data = get_json_data(url)

    if data:
        total_rows = data['response']['total']
        print("Total rows:", total_rows)
        total_chunks = int(total_rows / chunk_len)
        print("Total chunks to download:", total_chunks)
        
        # Now get the available data in mini-batches
        frames = []
        for i in range(total_chunks):
            url = generate_url(start_date, end_date, offset, chunk_len, api_key)
            print("Obtaining chunk # {} from url {}".format((i + 1), url))
            resp = get_json_data(url)
            if resp:
                try:
                    chunk_json = resp['response']['data']
                    chunk_df = pd.DataFrame.from_dict(chunk_json)
                    frames.append(chunk_df)
                except:
                    print(resp)
            else:
                print("Failed to fetch chunk {}".format(i))
            offset += chunk_len

        fname = os.path.join(output_path, '{}-{}.bin'.format(start_date, end_date))
    
        if len(frames) > 0:
            print(len(frames))
            df = pd.concat(frames, axis=0)
            
            print("Saving to {}...".format(fname))
    
            try:
                save_to_pickle(df, fname)
                print('Saved.')
    
            except FileNotFoundError:
                print("Saving failed. No such folder {}.".format(output_path))

if __name__ == "__main__":
    main()