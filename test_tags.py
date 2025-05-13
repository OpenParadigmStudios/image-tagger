#!/usr/bin/env python
"""
Test script for adding tags to an image
"""

import requests
import time
import os
import sys

def wait_for_server(max_attempts=10):
    attempts = 0
    while attempts < max_attempts:
        try:
            response = requests.get('http://127.0.0.1:8000/api/tags/')
            if response.status_code == 200:
                print('Server is ready')
                return True
        except requests.exceptions.ConnectionError:
            pass

        attempts += 1
        print(f'Waiting for server... attempt {attempts}')
        time.sleep(1)

    print('Server did not start in time')
    return False

def add_tags_to_image():
    # First add some tags to the global tag list
    tags_to_add = ['test1', 'test2', 'test3']

    for tag in tags_to_add:
        response = requests.post('http://127.0.0.1:8000/api/tags/',
                              json={'tags': [tag]})
        print(f'Added tag {tag}: {response.status_code}')

    # Add tags to image 0
    response = requests.put('http://127.0.0.1:8000/api/images/0/tags',
                          json={'image_id': '0', 'tags': tags_to_add})
    print(f'Added tags to image 0: {response.status_code}')

if __name__ == "__main__":
    if wait_for_server():
        add_tags_to_image()
        print('Script completed')
    else:
        print('Failed to connect to server')
        sys.exit(1)
