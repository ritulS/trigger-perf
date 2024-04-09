import etcd3
import os
import argparse
import threading
import time
import logging
import json
import traceback

import etcd3.exceptions

# Connecting to etcd cluster
etcd1_ip = '172.31.0.15'
etcd2_ip = '172.31.0.20'
etcd3_ip = '172.31.0.213'
etcd_hosts = ["http://{}:2379".format(etcd1_ip), "http://{}:2379".format(etcd2_ip), "http://{}:2379".format(etcd3_ip)]

try:
    etcd = etcd3.client(host='172.31.0.15', port=2379)
    print(f"Connection success!, etcd version: {etcd.status().version}")
except etcd3.exceptions.ConnectionFailedError as e:
    print(e)
    traceback.print_exc()
    print("connection failed!")


# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_file = 'etcd_logging.log'
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

def generate_rand_string(size: int):
    # size is in bytes
    random_bytes = os.urandom(size)
    random_string = random_bytes.decode('latin-1')  # Decode bytes to string
    return random_string

def get_size(input_string):
    # Calculate the size of the input string in bytes
    string_bytes = input_string.encode('latin-1')  # Encode string to bytes
    size_in_bytes = len(string_bytes)
    return size_in_bytes

'''
Etcd CRUD operations
'''
def etcd_put_kv(key: str, value: str):
    etcd.put(key, value)
    # print(f"\nKV pair inserted => {key}:{value}")

def etcd_get_kv(key: str):
    etcd.get(key)

def etcd_delete_kv(key: str):
    etcd.delete(key)
    print(f"Key deleted => {key}")

def etcd_update_kv(key: str, new_val):
    etcd.put(key, new_val, prev_kv=True)

'''
Function to set watch on given key 
'''
def watch_callback(event, key):
    # print(event.events)
    for e in event.events:
        recv_time = time.time()
        e_version = e.version
        check_key = e.key.decode("utf-8")
        
        key_size = get_size(key)
        log_data = {'Key': key, 'Event': 'TRIGGER', 'KeySize': key_size, 'KeyVersion': e_version, 'time_stamp': recv_time}
        print(log_data)
        logger.info(json.dumps(log_data))
        # print(f"Key {key} has been updated, new value is")

def set_watch_key(key: str):
    watch_id = etcd.add_watch_callback(key, lambda event: watch_callback(event, key))
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print(f"Stopped watching key: {key}")
        etcd.cancel_watch(watch_id)
    

def string_to_list(string):
    string = string.strip("[]").strip()
    elements = [int(element.strip()) for element in string.split(",")]
    return elements

def main():
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--ksizes', help='Key sizes to run exp on')
    parser.add_argument('--iters', help='Number of watch measurements')
    parser.add_argument('--val_size', help='Number of watch measurements')
    
    args = parser.parse_args()
    ksizes = string_to_list(args.ksizes)
    iters = int(args.iters)
    val_size = int(args.val_size)

    key_list = [] # list to store keys of given sizes
    for ksize in ksizes:
        temp_key = generate_rand_string(ksize)
        key_list.append(temp_key)

    print(key_list)

    # Setting watch on key
    watch_threads = []
    for key in key_list:
        try:
            thread = threading.Thread(target=set_watch_key, args=(key,))
            thread.start()
            watch_threads.append(thread)
        except Exception as e:
            print(f"Setting watch on key {key} failed with error {e}")

    # put keys and modify them n-1 times
    val = generate_rand_string(val_size)
    for key in key_list:
        for i in range(iters):
            send_time = time.time()
            if i == 0:
                etcd_put_kv(key, val)
            else:
                etcd_update_kv(key, val)
            key_size = get_size(key)
            log_data = {'Key': key, 'Event': 'PUT', 'KeySize': key_size, 'KeyVersion': i+1, 'time_stamp': send_time}
            print(log_data)
            logger.info(json.dumps(log_data))


'''
Sample run command:
python3.7 etcd_watch_script.py --ksizes [5,10] --iters 3 --val_size 10
'''

if __name__ == "__main__":
    main()
    # set_watch_key("key1")
    # etcd_put_kv("key1", "bsdk")