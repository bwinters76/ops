from app import app,db
from app.models import IPinfo
from urllib.request import urlopen
from bs4 import BeautifulSoup
from flask import jsonify
from time import sleep
import os
import json
import time
import requests


def kscnetattackscrape():
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
                attackerIP = attackRow['attackerIP']
                print(attackerIP)
                IPinDbCheck = IPinfo.query.filter_by(ipaddress=attackerIP).first()
                if IPinDbCheck is None:
                    print('none found')
                    attacker = IPinfo(ipaddress=attackerIP)
                    print(attacker)
                    db.session.add(attacker)
                    db.session.commit()
                else:
                    print(IPinDbCheck)
                    print('skipping')
            attackCount += 1
    finally:
        print(attackCount)
        attackDetailJSON = json.dumps(attackDetail)
        with open('netattacks.txt', 'w') as outfile:
            outfile.write(attackDetailJSON)
        return attackCount

def ip_to_country(ip):
    url = 'http://api.ipinfodb.com/v3/ip-country/?key=' + app.config['IPINFODB_API_KEY'] + '&ip=' + ip + '&format=json'
    response =requests.get(url)
    print(response)
    json_data = response.json()
    country = json_data['countryName']
    return json_data

def populate_ip_country():
    unknown_ip_origin = IPinfo.query.filter_by(countryname=None)
    for ip in unknown_ip_origin:
        json_data = ip_to_country(ip.ipaddress)
        print('writing'+json_data['countryName']+json_data['countryCode'])
        ip.countryname = json_data['countryName']
        ip.countrycode = json_data['countryCode']
        db.session.commit()
        print('sleeping')
        sleep(1)
        print('waking')
