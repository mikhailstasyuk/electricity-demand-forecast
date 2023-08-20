import sys
sys.path.append('src')
import predict

def handler(event, context):
    predict.main()

if __name__ == "__main__":
    handler(None, None)