import os 
import sys
sys.path.append('src')
import predict
import json

def handler(event, context):
    predict.main()

    if os.path.exists('pred.json'):
        with open('pred.json') as f_in:
            pred = json.load(f_in)
            return pred

if __name__ == "__main__":
    handler(None, None)