import boto3
import json
import random
import os

def invoker_function(key, data, r, e_id, run_id):
        client = boto3.client('lambda')
        payload = [key, data, e_id, run_id]
        response = client.invoke(
        FunctionName='write-lmd',
        InvocationType='Event',
        Payload=json.dumps(payload)
        )
        if response.get('FunctionError'):
            print(f"Error invoking write-lmd: {response.get('FunctionError')}")

def generate_rand_string(size):
    # size is in bytes
    random_bytes = os.urandom(size)
    random_string = random_bytes.decode('latin-1')  # Decode bytes to string
    return random_string

event_id_counter = 0
def gen_event_id():
    global event_id_counter
    event_id_counter += 1 
    return event_id_counter


def lambda_handler(event, context):
    
    # Get w-k-r input
    print('EVENT: ', event)
    run_id = event.get('run_id')
    data_store = event.get('data_store')
    num_keys = int(event.get('num_keys'))
    ksize_start = int(event.get('ksize_start'))
    ksize_end = int(event.get('ksize_end'))
    kjumps = int(event.get('kjumps'))
    vsize = int(event.get('vsize'))
    num_readers = int(event.get('num_readers'))
    
    
    # Get key sizes required
    key_sizes_to_write = []
    temp = ksize_start

    while temp < ksize_end:
         key_sizes_to_write.append(temp)
         temp += kjumps
        
    print(key_sizes_to_write)
    # Key and data generation
    for i in key_sizes_to_write: 
        key = generate_rand_string(i) # key size
        data = generate_rand_string(vsize) # data size
        e_id = gen_event_id()
        # Invoke send/write function
        print(f"INVOKING KEY SIZE: {i}\n")
        invoker_function(key,data, num_readers,e_id,run_id)
        

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

    