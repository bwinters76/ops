from app import app
import json
from flask import session

def load_file():
    infile = open('nahealth.txt', 'r', encoding='latin-1')
    raw_file_data = infile.read()
    controller_data = json.loads(raw_file_data)
    return controller_data


def volume_count_over_90(toReturn):
    volume_count = 0
    infile = open('volumes.txt', 'r', encoding='latin-1')
    volume_list = infile.read()
    volumes = json.loads(volume_list)
    if toReturn == 'count':
        for volume in volumes:
            volume_count += 1
        return volume_count
    else:
        return volumes

def warning_volumes_count():
    warning_volume_count = 0
    controller_data = load_file()
    for controller in controller_data:
        for count in controller['Counts']:
            warning_volume_count += count['WarningVolumeCount']

    return warning_volume_count

def total_volumes_count():
    total_volume_count = 0
    controller_data = load_file()
    for controller in controller_data:
        for count in controller['Counts']:
            total_volume_count += count['AllVolumeCount']

    return total_volume_count

def warning_cluster_peer_counts():
    warning_cluster_peer_count = 0
    controller_data = load_file()
    for controller in controller_data:
        for count in controller['Counts']:
            warning_cluster_peer_count += count['UnhealthyClusterPeerCount']
    return warning_cluster_peer_count

def warning_snapmirror_counts():
    warning_snapmirror_count = 0
    controller_data = load_file()
    for controller in controller_data:
        for count in controller['Counts']:
            warning_snapmirror_count += count['FailedMirrors']
    return warning_snapmirror_count

def healthy_snapmirror_counts():
    healthy_snapmirror_count = 0
    controller_data = load_file()
    for controller in controller_data:
        for count in controller['Counts']:
            healthy_snapmirror_count += count['HealthyMirrors']
    return healthy_snapmirror_count
