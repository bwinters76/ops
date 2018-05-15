from app import db
from datetime import datetime



class Outage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    oservice = db.Column(db.String(10), index=True)
    odate = db.Column(db.DateTime, default=datetime.utcnow)
    ohour = db.Column(db.Integer)
    ominute = db.Column(db.Integer)
    oampm = db.Column(db.String(1))
    olength = db.Column(db.Integer)
    ocategory = db.Column(db.String(1), index=True, default='U')
    oreason = db.Column(db.String(1024))

    def __repr__(self):
        return '<oservice {}>'.format(self.oservice)

class IPinfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ipaddress = db.Column(db.String(15), index=True)
    countryname = db.Column(db.String(128), index=True)
    countrycode = db.Column(db.String(3), index=True)

    def __repr__(self):
        return '<ipaddress {}>'.format(self.ipaddress)
