from app import app
import json, requests
from flask import flash, session


def load_file():
    infile = open('wsushealth.txt', 'r', encoding='latin-1')
    raw_file_data = infile.read()
    windows_update_data = json.loads(raw_file_data)
    return windows_update_data

def servers_needing_updates():
    count = 0
    windows_update_data = load_file()
    for server in windows_update_data:
        if server['NeededCount'] > 0:
            count += 1
    return count

def servers_failed_updates():
    count = 0
    windows_update_data = load_file()
    for server in windows_update_data:
        if server['FailedCount'] > 0:
            count += 1
    return count
