from app import app
from urllib.request import urlopen
from bs4 import BeautifulSoup
from flask import jsonify
import os
import json
import time
import requests

def ksc_load_file():
    infile = open('netattacks.txt', 'r', encoding='utf-8')
    raw_file_data = infile.read()
    attack_data = json.loads(raw_file_data)
    return attack_data

def kscnetattackcount():
    attack_count = 0
    attack_data = ksc_load_file()
    for attack in attack_data:
        attack_count += 1
    return attack_count

def kscnetattackreport():
    t = time.process_time()
    html = urlopen('http://ohucsvcenter.realtracs.net/_netattacks.html')
    bsObj = BeautifulSoup(html.read(),'html.parser')
    table = bsObj.find_all('table',{'id':'Details'})[0]
    rows = table.find_all('tr')
    attackCount = 0
    attackRowHeader = ['group','device','attackerIP','attackTime','attack','protocol','port','lastVisibleTime','lastConnectionToAdminServer','ipAddress','netbiosName','windowsDomain']
    attackDetail = []

    try:
        for row in rows:
            attackRow = dict()
            cellIndex = 0
            for cell in row.find_all('td'):
                attackRow[attackRowHeader[cellIndex]] = cell.get_text()
                cellIndex += 1
            if attackCount > 0:
                attackDetail.append(attackRow)
            attackCount += 1
    finally:
        print(attackCount)
        attackDetailJSON = json.dumps(attackDetail)
        with open('netattacks.txt', 'w') as outfile:
            outfile.write(attackDetailJSON)
        tt = time.process_time() - t
        print(tt)
        return attackCount

def kscattakerip():
    infile = open('netattacks.txt','r',encoding='utf-8')
    attacksList = jsonloads(infile.read())
    pass

def ip_to_country(ip):
    url = 'http://api.ipinfodb.com/v3/ip-country/?key=' + app.config('IPINFODB_API_KEY') + '&ip=' + ip
    pass
