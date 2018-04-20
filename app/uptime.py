import json, requests
from datetime import datetime
from calendar import monthrange
from flask import flash
from app import app, db
from app.models import Outage



def PrivateUptime(service):
    today = datetime.today()
    current_year = today.year
    yday = today.timetuple().tm_yday
    ytd_total_minutes = yday * 24 * 60
    ytd_crit_minutes = yday * 13 * 60

    current_month = today.month
    current_month_days = monthrange(current_year,current_month)[1]
    current_month_minutes = current_month_days * 24 * 60
    current_month_crit_minutes = current_month_days * 13 *60

    prior_year = current_year - 1
    prior_year_end = datetime(prior_year,12,31)
    prior_year_days = prior_year_end.timetuple().tm_yday
    prior_year_minutes = prior_year_days * 24 * 60
    prior_year_crit_minutes = prior_year_days * 13 * 60

    if current_month == 1:
        prior_month = 12
        prior_month_days = monthrange(prior_year,prior_month)[1]
    else:
        prior_month = current_month - 1
        prior_month_days = monthrange(current_year,prior_month)[1]

    prior_month_minutes = prior_month_days * 24 * 60
    prior_month_crit_minutes = prior_month_days * 13 * 60

    ytd_downtime = 0
    ytd_crit_downtime = 0
    mtd_downtime = 0
    mtd_crit_downtime = 0
    pmtd_downtime = 0
    pmtd_crit_downtime = 0
    prior_ytd_downtime = 0
    prior_ytd_crit_downtime = 0

    outages = Outage.query.filter_by(oservice = service)
    for incident in outages:

        incident_year = incident.odate.year
        incident_month = incident.odate.month
        incident_hour = incident.odate.hour

        if incident_year == current_year:
            ytd_downtime += incident.olength
            if incident_hour > 7 and incident_hour < 21:
                ytd_crit_downtime += incident.olength
        elif incident_year == prior_year:
            prior_ytd_downtime += incident.olength
            if incident_hour > 7 and incident_hour < 21:
                prior_ytd_crit_downtime += incident.olength
        if incident_month == current_month and incident_year == current_year:
            mtd_downtime += incident.olength
            if incident_hour > 7 and incident_hour < 21:
                mtd_crit_downtime += incident.olength
        if prior_month == 12:
            if incident_month == prior_month and incident_year == prior_year:
                pmtd_downtime += incident.olength
                if incident_hour > 7 and incident_hour < 21:
                    pmtd_crit_downtime += incident.olength
        else:
            if incident_month == prior_month and incident_year == current_year:
                pmtd_downtime += incident.olength
                if incident_hour > 7 and incident_hour < 21:
                    pmtd_crit_downtime += incident.olength

    if ytd_downtime > 0:
        ytd_up_percent = round((100.0000 - ((ytd_downtime * 100) / ytd_total_minutes)), 4)
    else:
        ytd_up_percent = 100

    if mtd_downtime > 0:
        mtd_up_percent = round((100.0000 - ((mtd_downtime * 100) / current_month_minutes)), 4)
    else:
        mtd_up_percent = 100

    if pmtd_downtime > 0:
        pmtd_up_percent = round((100.0000 - ((pmtd_downtime * 100) / prior_month_minutes)), 4)
    else:
        pmtd_up_percent = 100

    if pmtd_crit_downtime > 0:
        pmtd_crit_up_percent = round((100.0000 - ((pmtd_crit_downtime * 100) / prior_month_crit_minutes)), 4)
    else:
        pmtd_crit_up_percent = 100

    if prior_ytd_downtime > 0:
        pytd_up_percent = round((100.0000 - ((prior_ytd_downtime * 100) / prior_year_minutes)), 4)
    else:
        pytd_up_percent = 100

    if ytd_crit_downtime > 0:
        ytd_crit_up_percent = round((100.0000 - ((ytd_crit_downtime * 100) / ytd_crit_minutes)), 4)
    else:
        ytd_crit_up_percent = 100

    if mtd_crit_downtime > 0:
        mtd_crit_up_percent = round((100.0000 - ((mtd_crit_downtime * 100) / current_month_crit_minutes)), 4)
    else:
        mtd_crit_up_percent = 100

    if prior_ytd_crit_downtime > 0:
        pytd_crit_up_percent = round((100.0000 - ((prior_ytd_crit_downtime * 100) / prior_year_crit_minutes)), 4)
    else:
        pytd_crit_up_percent = 100

    uptimes = dict()
    uptimes['mtd'] = mtd_up_percent
    uptimes['c_mtd'] = mtd_crit_up_percent
    uptimes['ytd'] = ytd_up_percent
    uptimes['c_ytd'] = ytd_crit_up_percent
    uptimes['pytd'] = pytd_up_percent
    uptimes['c_pytd'] = pytd_crit_up_percent
    uptimes['pmtd'] = pmtd_up_percent
    uptimes['c_pmtd'] = pmtd_crit_up_percent

    return uptimes

def UptimeReport(year, month, service):
    selected_month_days = monthrange(year,month)[1]
    selected_month_minutes = selected_month_days * 24 * 60
    selected_month_crit_minutes = selected_month_days * 13 * 60

    mtd_downtime = 0
    mtd_crit_downtime = 0

    outages = Outage.query.filter_by(oservice = service)
    for incident in outages:
        incident_year = incident.odate.year
        incident_month = incident.odate.month
        incident_hour = incident.odate.hour

        if incident_month == month and incident_year == year:
            mtd_downtime += incident.olength
            if incident_hour > 7 and incident_hour < 21:
                mtd_crit_downtime += incident.olength

    if mtd_downtime > 0:
        mtd_up_percent = round((100.0000 - ((mtd_downtime * 100) / selected_month_minutes)), 4)
    else:
        mtd_up_percent = 100
    if mtd_crit_downtime > 0:
        mtd_crit_up_percent = round((100.0000 - ((mtd_crit_downtime * 100) / selected_month_crit_minutes)), 4)
    else:
        mtd_crit_up_percent = 100

    uptimes = dict()
    uptimes['mtd'] = mtd_up_percent
    uptimes['c_mtd'] = mtd_crit_up_percent

    return uptimes

def UptimeReportList(year, month, service):
    outages = Outage.query.order_by(Outage.odate.asc()).filter_by(oservice = service)
    outage_list = []
    for incident in outages:
        incident_year = incident.odate.year
        incident_month = incident.odate.month
        incident_date = incident.odate.strftime("%A, %B %d %Y")
        incident_time = incident.odate.strftime("%I:%M %p")
        incident_list= dict()
        if incident_month == month and incident_year == year:
            incident_list['date'] = incident_date
            incident_list['time'] = incident_time
            incident_list['length'] = incident.olength
            incident_list['reason'] = incident.oreason
            outage_list.append(incident_list)
    return outage_list
