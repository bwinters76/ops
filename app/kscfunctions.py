from app import app
from urllib.request import urlopen
from bs4 import BeautifulSoup
from flask import jsonify
import os
import json


def kscnetattackreport():
    html = urlopen('http://ohucsvcenter.realtracs.net/_netattacks.html')
    bsObj = BeautifulSoup(html.read(),'html.parser')
    table = bsObj.find_all('table',{'id':'Details'})[0]
    rows = table.find_all('tr')
    attackCount = 0
    attackRowHeader = ['group','device','attackerIP','attackTime','attack','protocol','port','lastVisibleTime','lastConnectionToAdminServer','ipAddress','netbiosName','windowsDomain']
    attackDetail = []

    try:
        for row in rows:
            attackCount += 1
            attackRow = dict()
            cellIndex = 0
            for cell in row.find_all('td'):
                attackRow[attackRowHeader[cellIndex]] = cell.get_text()
                cellIndex += 1
            if cellIndex > 0:
                attackDetail.append(attackRow)
    finally:
        print(attackCount)
        attackDetailJSON = json.dumps(attackDetail)
        with open('netattacks.txt', 'w') as outfile:
            outfile.write(attackDetailJSON)
        return attackCount
