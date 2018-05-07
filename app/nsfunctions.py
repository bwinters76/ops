from app import app
import json, requests
from flask import flash, session
from app import slackfunctions as slack


def nslogin(nsname, user, pwd):
    url = 'https://' + nsname + '/nitro/v1/config/login'
    headers = {'Content-type':'application/vnd.com.citrix.netscaler.login+json'}
    data = {"login":{"username":user,"password":pwd}}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response

def nslbcount(nsname, AuthToken):
    token = 'NITRO_AUTH_TOKEN=' + AuthToken
    url = 'https://' + nsname + '/nitro/v1/config/lbvserver?count=yes'
    headers = {'Cookie':token, 'Content-type':'application/vnd.com.citrix.netscaler.lbvserver+json'}
    response = requests.get(url, headers=headers)
    return response.status_code

def nslogout(nsname, AuthToken):
    token = 'NITRO_AUTH_TOKEN=' + AuthToken
    url = 'https://' + nsname + '/nitro/v1/config/logout'
    headers = {'Cookie':token, 'Content-type':'application/vnd.com.citrix.netscaler.logout+json'}
    data = {"logout":{}}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response

def nssaveconfig(nsname, AuthToken):
    token = 'NITRO_AUTH_TOKEN=' + AuthToken
    url = 'https://' + nsname + '/nitro/v1/config/nsconfig?action=save'
    headers = {'Cookie':token, 'Content-type':'application/vnd.com.citrix.netscaler.nsconfig+json'}
    data = {"nsconfig":{}}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response

def get_details(nsname, vserver, AuthToken):
    token = 'NITRO_AUTH_TOKEN=' + AuthToken
    url = 'https://' + nsname + '/nitro/v1/config/lbvserver_servicegroup_binding/' + vserver
    headers = {'Cookie':token, 'Content-type':'application/vnd.com.citrix.netscaler.lbvserver_servicegroup_binding+json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200 or response.status_code == 201:
        nslist = json.loads(response.text)
        for x in nslist['lbvserver_servicegroup_binding']:
            detail = x['servicegroupname']
            return detail
    else:
        #message = json.loads(response.text['message'])
        return response.text

def ns_lb_svcg_bind(nsname, lbvserver, servicegroup, AuthToken):
    token = 'NITRO_AUTH_TOKEN=' + AuthToken
    url = 'https://' + nsname + '/nitro/v1/config/lbvserver_servicegroup_binding'
    headers = {'Cookie':token, 'Content-Type':'application/vnd.com.citrix.netscaler.lbvserver_servicegroup_binding+json'}
    data = {"lbvserver_servicegroup_binding":{"servicegroupname":servicegroup,"name":lbvserver}}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200 or response.status_code == 201:
        slack_channel = app.config['SLACK_RELEASE_CHANNEL_ID']
        slack_message = 'Success: ' + lbvserver + ' bound to ' + servicegroup + ' on ' + nsname + ' by ' + session['ns_user']
        slack.send_message(slack_channel,slack_message)
    message = response.status_code
    return message

def ns_lb_svcg_unbind(nsname, lbvserver, servicegroup, AuthToken):
    token = 'NITRO_AUTH_TOKEN=' + AuthToken
    url = 'https://' + nsname + '/nitro/v1/config/lbvserver_servicegroup_binding/' + lbvserver + '?args=servicegroupname:' + servicegroup
    headers = {'Cookie':token}
    response = requests.delete(url, headers=headers)
    if response.status_code == 200 or response.status_code == 201:
        slack_channel = app.config['SLACK_RELEASE_CHANNEL_ID']
        slack_message = 'Success: ' + lbvserver + ' unbound from ' + servicegroup + ' on ' + nsname + ' by ' + session['ns_user']
        slack.send_message(slack_channel,slack_message)
    message = response.status_code
    return message




def bindings(nsname, AuthToken):
    ns_vs_list = app.config['PRODUCTION_VS_LIST']
    ns_bound_list= []
    pvtweb = ''
    pvtapi = ''
    pubweb = ''
    betaweb = ''
    for vs in app.config['PRODUCTION_VS_LIST']:
        vs_bound_list = dict()
        vs_bound_to = get_details(nsname, vs, AuthToken)
        if vs == app.config['PVT_VS_HTTP'] and vs_bound_to == app.config['PVT_SIDE_A_HTTP']:
            vs_bound_list['vs'] = 'pvt_http'
            vs_bound_list['svcg'] = 'A'
            pvtweb = 'A'
            ns_bound_list.append(vs_bound_list)
        elif vs == app.config['PVT_VS_HTTP'] and vs_bound_to == app.config['PVT_SIDE_B_HTTP']:
            vs_bound_list['vs'] = 'pvt_http'
            vs_bound_list['svcg'] = 'B'
            pvtweb = 'B'
            ns_bound_list.append(vs_bound_list)
        elif vs == app.config['PVT_VS_API'] and vs_bound_to == app.config['PVT_SIDE_A_API']:
            vs_bound_list['vs'] = 'pvt_api'
            vs_bound_list['svcg'] = 'A'
            pvtapi = 'A'
            ns_bound_list.append(vs_bound_list)
        elif vs == app.config['PVT_VS_API'] and vs_bound_to == app.config['PVT_SIDE_B_API']:
            vs_bound_list['vs'] = 'pvt_api'
            vs_bound_list['svcg'] = 'B'
            pvtapi = 'B'
            ns_bound_list.append(vs_bound_list)
        elif vs == app.config['PUB_VS_API'] and vs_bound_to == app.config['PUB_SIDE_A_API']:
            vs_bound_list['vs'] = 'pub_api'
            vs_bound_list['svcg'] = 'A'
            pubweb = 'A'
            ns_bound_list.append(vs_bound_list)
        elif vs == app.config['PUB_VS_API'] and vs_bound_to == app.config['PUB_SIDE_B_API']:
            vs_bound_list['vs'] = 'pub_api'
            vs_bound_list['svcg'] = 'B'
            pubweb = 'B'
            ns_bound_list.append(vs_bound_list)
        elif vs == app.config['BETA_VS_API'] and vs_bound_to == app.config['BETA_SIDE_A_API']:
            vs_bound_list['vs'] = 'beta_api'
            vs_bound_list['svcg'] = 'A'
            betaweb = 'A'
            ns_bound_list.append(vs_bound_list)
        elif vs == app.config['BETA_VS_API'] and vs_bound_to == app.config['BETA_SIDE_B_API']:
            vs_bound_list['vs'] = 'beta_api'
            vs_bound_list['svcg'] = 'B'
            betaweb = 'B'
            ns_bound_list.append(vs_bound_list)
    vs_summary_list = dict()
    if pvtweb == 'A' and pvtapi == 'A':
        vs_summary_list['vs'] = 'pvt_web'
        vs_summary_list['svcg'] = 'A'
        ns_bound_list.append(vs_summary_list)
        vs_summary_list = dict()
    elif pvtweb == 'B' and pvtapi =='B':
        vs_summary_list['vs'] = 'pvt_web'
        vs_summary_list['svcg'] = 'B'
        ns_bound_list.append(vs_summary_list)
        vs_summary_list = dict()
    if pubweb == 'A':
        vs_summary_list['vs'] = 'pub_web'
        vs_summary_list['svcg'] = 'A'
        ns_bound_list.append(vs_summary_list)
        vs_summary_list = dict()
    elif pubweb == 'B':
        vs_summary_list['vs'] = 'pub_web'
        vs_summary_list['svcg'] = 'B'
        ns_bound_list.append(vs_summary_list)
        vs_summary_list = dict()
    if betaweb == 'A':
        vs_summary_list['vs'] = 'beta_web'
        vs_summary_list['svcg'] = 'A'
        ns_bound_list.append(vs_summary_list)
        vs_summary_list = dict()
    elif betaweb == 'B':
        vs_summary_list['vs'] = 'beta_web'
        vs_summary_list['svcg'] = 'B'
        ns_bound_list.append(vs_summary_list)
        vs_summary_list = dict()
    return ns_bound_list

def buildserverlist(list):
    serverlist = []
    for server in list:
        serverlist.append()
