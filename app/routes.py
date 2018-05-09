from flask import render_template, flash, redirect, url_for, session, request, jsonify
from app import app, db
from app import emails
from app import nsfunctions as ns
from app import nafunctions as na
from app import winfunctions as win
from app.forms import LoginForm, OutageForm, ReportForm, NSForm, EmailReportForm
from app.models import Outage
from functools import wraps
from app import uptime
from app import slackfunctions as slack
from datetime import datetime
import json
import os

def login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first...')
            return  redirect(url_for('login'))
    return wrap

def before_request():
    session.modified = True

@app.route('/active_test', methods=['GET', 'POST'])
def activetest():
    title = 'jQuery Testing'
    return render_template('active_test.html', title=title)

@app.route('/_sample', methods=['GET', 'POST'])
def _sample():
    if request.method == 'POST':
        data = request.data
        print(data)
        volume_count = na.volume_count_over_90('count')
        return jsonify({'volume_count': volume_count})
    else:
        allowed = ['_testhome', '_testdl', '_testtutorials']
        data = request.args.get('page')
        if data in allowed:
            fileDir = os.path.dirname(os.path.realpath('__file__'))
            filename = os.path.join(fileDir, 'app/templates/' + data + '.html')
            with open(filename) as page:
                content = page.read()
            return content
        else:
            return 'Sorry Not Allowed'

@app.route('/')
@app.route('/index')
def index():
    uptime_pvt = uptime.PrivateUptime('.net')
    uptime_pub = uptime.PrivateUptime('.com')
    uptime_eml = uptime.PrivateUptime('email')
    if 'logged_in' in session:
        #flash('already logged in')
        ns_bound_list = ns.bindings(session['ns_name'], session['ns_auth_token'])
        return render_template('index.html', bindings=ns_bound_list, uptime_pvt=uptime_pvt['mtd'], uptime_pub=uptime_pub['mtd'], uptime_eml=uptime_eml['mtd'])
    else:
        ns_name = 'nsvpx2.realtracs.net'
        ns_user = app.config['NS_RO_USER']
        ns_pwd = app.config['NS_RO_PWD']
        read_login = ns.nslogin(ns_name, ns_user, ns_pwd)
        if read_login.status_code == 200 or read_login.status_code == 201:
            session['read_token'] = read_login.cookies['NITRO_AUTH_TOKEN']
            #flash('logged in with ' + session['read_token'])
            ns_bound_list = ns.bindings(ns_name, session['read_token'])
            return render_template('index.html', bindings=ns_bound_list, uptime_pvt=uptime_pvt['mtd'], uptime_pub=uptime_pub['mtd'], uptime_eml=uptime_eml['mtd'])
        else:
            flash('Something went wrong with login...')
            return render_template('index.html', uptime_pvt=uptime_pvt['mtd'], uptime_pub=uptime_pub['mtd'], uptime_eml=uptime_eml['mtd'])
        logout_result = ns.nslogout(ns_name, session['read_token'])
        #flash(logout_result)

@app.route('/_naclusterpeerhealth', methods=['POST'])
def _naclusterpeerhealth():
    if request.method == 'POST':
        data = request.data
        cluster_peer_count = na.cluster_peer_counts()
        warning_cluster_peer_count = na.warning_cluster_peer_counts()
        return jsonify({'warning_cluster_peer_count': warning_cluster_peer_count,'cluster_peer_count':cluster_peer_count})

@app.route('/_nasnapmirrorhealth', methods=['POST'])
def _nasnapmirrorhealth():
    if request.method == 'POST':
        data = request.data
        healthy_snapmirror_count = na.healthy_snapmirror_counts()
        warning_snapmirror_count = na.warning_snapmirror_counts()
        return jsonify({'warning_snapmirror_count': warning_snapmirror_count, 'healthy_snapmirror_count':healthy_snapmirror_count})

@app.route('/_navolhealth', methods=['POST'])
def _navolhealth():
    if request.method == 'POST':
        data = request.data
        total_volume_count = na.total_volumes_count()
        warning_volume_count = na.warning_volumes_count()
        return jsonify({'warning_volume_count': warning_volume_count,'total_volume_count':total_volume_count})

@app.route('/_winupdcnt', methods=['POST'])
def _winupdcnt():
    if request.method == 'POST':
        servers_needing_updates_count = win.servers_needing_updates()
        return jsonify({'servers_needing_updates_count':servers_needing_updates_count})

@app.route('/_winfailupdcnt', methods=['POST'])
def _winfailupdcnt():
    if request.method == 'POST':
        servers_failed_updates_count = win.servers_failed_updates()
        return jsonify({'servers_failed_updates_count':servers_failed_updates_count})

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    errormsg = ''
    if form.validate_on_submit():
        session['ns_name'] = form.device.data
        session['ns_user'] = form.username.data
        session['ns_pwd'] = form.password.data
        login_result = ns.nslogin(session['ns_name'], session['ns_user'], session['ns_pwd'])
        if login_result.status_code == 201 or login_result.status_code == 200 :
            session.permanent = True
            session['ns_auth_token'] = login_result.cookies['NITRO_AUTH_TOKEN']
            session['logged_in'] = True
            flash(session['ns_user'] + ' just logged into ' + session['ns_name'])
            return redirect(url_for('nsmgmt'))
        else:
            message = json.loads(login_result.text)
            errormsg = message['message']
            return render_template('login.html',title='Sign In', form=form, errormsg=errormsg)
    else:
        return render_template('login.html', title='Sign In', form=form)


@app.route('/nsmgmt', methods=['GET', 'POST'])
@login_required
def nsmgmt():
    before_request()
    authtoken_still_valid = ns.nslbcount(session['ns_name'], session['ns_auth_token'])
    if authtoken_still_valid != 200:
        flash('Your session may have expired please login again')
        return redirect(url_for('login'))
    ns_bound_list = ns.bindings(session['ns_name'], session['ns_auth_token'])
    form = NSForm()
    if form.validate_on_submit():
        session['ns_flip_pvt'] = form.enablepvtflip.data
        session['ns_flip_pub'] = form.enablepubflip.data
        session['ns_flip_beta'] = form.enablebetaflip.data
        return redirect(url_for('nsbndmgr'))
    else:
        return render_template('nsmgmt.html', title='NetScaler Stack Management', form=form, bindings=ns_bound_list, token=session['ns_auth_token'], user=session['ns_user'], netscaler=session['ns_name'])

@app.route('/nsbndmgr', methods=['GET', 'POST'])
@login_required
def nsbndmgr():
    if request.method =='POST':
        return
    else:
        ns_bound_list = ns.bindings(session['ns_name'], session['ns_auth_token'])
        for binding in ns_bound_list:
            if binding['vs'] == 'pvt_web':
                pvtweb = binding['svcg']
            elif binding['vs'] == 'pub_web':
                pubweb = binding['svcg']
            elif binding['vs'] == 'beta_web':
                betaweb = binding['svcg']

        return render_template('nsbndmgr.html', title='Binding Manager', pvtweb=pvtweb, pubweb=pubweb, betaweb=betaweb, pvtflip=session['ns_flip_pvt'], pubflip=session['ns_flip_pub'], betaflip=session['ns_flip_beta'])

@app.route('/_currentbindings', methods=['GET','POST'])
def _currentbindings():
    ns_name = 'nsvpx2.realtracs.net'
    ns_user = app.config['NS_RO_USER']
    ns_pwd = app.config['NS_RO_PWD']
    read_login = ns.nslogin(ns_name, ns_user, ns_pwd)
    if read_login.status_code == 200 or read_login.status_code == 201:
        session['read_token'] = read_login.cookies['NITRO_AUTH_TOKEN']
        #flash('logged in with ' + session['read_token'])
        ns_bound_list = ns.bindings(ns_name, session['read_token'])
        for binding in ns_bound_list:
            if binding['vs'] == 'pvt_web':
                pvt_web = binding['svcg']
            elif binding['vs'] == 'pub_web':
                pub_web = binding['svcg']
            elif binding['vs'] == 'beta_web':
                beta_web = binding['svcg']
        logout_result = ns.nslogout(ns_name, session['read_token'])
        return jsonify({'pvt_web': pvt_web, 'pub_web': pub_web, 'beta_web': beta_web})
    else:
        flash('Something went wrong with login...')
        logout_result = ns.nslogout(ns_name, session['read_token'])
        return jsonify({'message': "Something went wrong..."})
    logout_result = ns.nslogout(ns_name, session['read_token'])


@app.route('/_flip', methods=['POST'])
@login_required
def flip_side():
    if request.form['text'] == 'Flip Private Web':
        results = ns.bindings(session['ns_name'], session['ns_auth_token'])
        for result in results:
            if result['vs'] == 'pvt_web':
                response = 'Updated to ' + result['svcg']
                svcg = result['svcg']
        return jsonify({'text': response, 'svcg': svcg})
    elif request.form['text'] == 'Flip Public Web':
        results = ns.bindings(session['ns_name'], session['ns_auth_token'])
        for result in results:
            if result['vs'] == 'pub_web':
                response = 'Updated to ' + result['svcg']
                svcg = result['svcg']
        return jsonify({'text': response, 'svcg': svcg})
    elif request.form['text'] == 'Flip Beta Web':
        sideincheck = ns.bindings(session['ns_name'], session['ns_auth_token'])
        for servicegroup in sideincheck:
            if servicegroup['vs'] == 'beta_web':
                sidein = servicegroup['svcg']
        if sidein == 'A':
            bindsvcg = ns.ns_lb_svcg_bind(session['ns_name'], app.config['BETA_VS_API'], app.config['BETA_SIDE_B_API'], session['ns_auth_token'])
            unbindsvcg = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['BETA_VS_API'], app.config['BETA_SIDE_A_API'], session['ns_auth_token'] )
            results = ns.bindings(session['ns_name'], session['ns_auth_token'])
            for result in results:
                if result['vs'] == 'beta_web':
                    response =  'Updated to Side ' + result['svcg']
                    svcg = result['svcg']
            return jsonify({'text': response, 'svcg': svcg })
        elif sidein == 'B':
            bindsvcg = ns.ns_lb_svcg_bind(session['ns_name'], app.config['BETA_VS_API'], app.config['BETA_SIDE_A_API'], session['ns_auth_token'])
            unbindsvcg = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['BETA_VS_API'], app.config['BETA_SIDE_B_API'], session['ns_auth_token'] )
            results = ns.bindings(session['ns_name'], session['ns_auth_token'])
            for result in results:
                if result['vs'] == 'beta_web':
                    response =  'Updated to Side ' + result['svcg']
                    svcg = result['svcg']
            return jsonify({'text': response, 'svcg': svcg })
        else:
            return jsonify({'text': 'Binding Failure', 'svcg': '?'})
    else:
        return jsonify({'text': 'Did not match Input', 'svcg': '?'})


@app.route('/logout')
@login_required
def logout():
    if 'logged_in' in session :
        logout_result = ns.nslogout(session['ns_name'], session['ns_auth_token'])
        if logout_result.status_code == 200 or logout_result.status_code == 201 :
            flash(session['ns_user'] + ' successfully logged out of ' + session['ns_name'])
            session.pop('logged_in', None)
            session.pop('ns_name', None)
            session.pop('ns_pwd', None)
            session.pop('ns_auth_token', None)
            return  redirect(url_for('index'))
        else:
            message = json.loads(logout_result.text)
            errormsg = message['message']
            session.pop('logged_in', None)
            session.pop('ns_name', None)
            session.pop('ns_pwd', None)
            session.pop('ns_auth_token', None)
            flash(errormsg)
    else:
        errormsg = 'Not Logged In'
        flash(errormsg)
    return redirect(url_for('login'))

@app.route('/outage_record', methods=['GET', 'POST'])
def outage_record():
    form = OutageForm()
    if form.validate_on_submit():
        incidentsvc = form.servicename.data
        incidentdate = datetime.combine(form.outagedate.data, form.outagestart.data)
        #incidenthour = form.outagehour.data
        #incidentminute = form.outageminute.data
        #incidentampm = form.outageampm.data
        incidentlength = form.outagelength.data
        incidentcategory = form.outagecategory.data
        incidentreason = form.outagereason.data
        incident = Outage(oservice=incidentsvc, odate=incidentdate, olength=incidentlength, ocategory=incidentcategory, oreason=incidentreason)
        db.session.add(incident)
        db.session.commit()
        flash('Your record has been saved...')
        return redirect(url_for('outage_record'))
    else:
        return render_template('outage_record.html', title='Record an Outage', form=form)

@app.route('/outage_list')
def outage_list():
    outages = Outage.query.order_by(Outage.oservice.desc(), Outage.odate.desc()).all()
    return render_template('outage_list.html', title = 'List of Outages', services = ['.net','.com','email'], outages=outages)

@app.route('/uptimes')
def uptimes():
    uptime_pvt = uptime.PrivateUptime('.net')
    uptime_pub = uptime.PrivateUptime('.com')
    uptime_eml = uptime.PrivateUptime('email')
    return render_template('uptimes.html', title = 'Uptimes', PrivateUpTime=uptime_pvt, PublicUpTime=uptime_pub, EmailUpTime=uptime_eml)

@app.route('/_uptimes', methods=['POST'])
def _uptimes():
    uptime_pvt = uptime.PrivateUptime('.net')
    uptime_pub = uptime.PrivateUptime('.com')
    uptime_eml = uptime.PrivateUptime('email')
    return jsonify({'uptime_pvt':uptime_pvt['mtd'], 'uptime_pub':uptime_pub['mtd'], 'uptime_eml':uptime_eml['mtd']})

@app.route('/uptime_report', methods=['GET', 'POST'])
def uptime_report():
    form = ReportForm()
    if form.validate_on_submit():
        selection = form.SelectedDate.data
        selectedyear = selection.year
        selectedmonth = selection.month
        MonthString = selection.strftime("%B %Y")

        uptime_pvt = uptime.UptimeReport(selectedyear, selectedmonth, '.net')
        list_pvt = uptime.UptimeReportList(selectedyear, selectedmonth, '.net')

        uptime_pub = uptime.UptimeReport(selectedyear, selectedmonth, '.com')
        list_pub = uptime.UptimeReportList(selectedyear, selectedmonth, '.com')

        uptime_eml = uptime.UptimeReport(selectedyear, selectedmonth, 'email')
        list_eml = uptime.UptimeReportList(selectedyear, selectedmonth, 'email')

        return render_template('uptime_report.html', title='Uptime Report', Month=MonthString, PrivateUpTime=uptime_pvt, PrivateList=list_pvt, PublicUpTime=uptime_pub, PublicList=list_pub, EmailUpTime=uptime_eml, EmailList=list_eml)

    else:
        return render_template('uptime_report.html',title='Uptime Report', form=form)

@app.route('/email_report', methods=['GET', 'POST'])
def email_report():
    form = EmailReportForm()
    if form.validate_on_submit():
        selection = form.selecteddate.data
        selectedyear = selection.year
        selectedmonth = selection.month
        MonthString = selection.strftime("%B %Y")
        recipient = form.enteredemail.data

        uptime_pvt = uptime.UptimeReport(selectedyear, selectedmonth, '.net')
        list_pvt = uptime.UptimeReportList(selectedyear, selectedmonth, '.net')

        uptime_pub = uptime.UptimeReport(selectedyear, selectedmonth, '.com')
        list_pub = uptime.UptimeReportList(selectedyear, selectedmonth, '.com')

        uptime_eml = uptime.UptimeReport(selectedyear, selectedmonth, 'email')
        list_eml = uptime.UptimeReportList(selectedyear, selectedmonth, 'email')
        message_body_html = render_template('uptime_report.html', title='Uptime Report', Month=MonthString, PrivateUpTime=uptime_pvt, PrivateList=list_pvt, PublicUpTime=uptime_pub, PublicList=list_pub, EmailUpTime=uptime_eml, EmailList=list_eml)
        message_body_text = render_template('uptime_report.html', title='Uptime Report', Month=MonthString, PrivateUpTime=uptime_pvt, PrivateList=list_pvt, PublicUpTime=uptime_pub, PublicList=list_pub, EmailUpTime=uptime_eml, EmailList=list_eml)
        emails.send_email('Uptime Report', 'reports@realtracs.com', recipient, message_body_text, message_body_html )
        return render_template('uptime_report.html', title='Uptime Report', Month=MonthString, PrivateUpTime=uptime_pvt, PrivateList=list_pvt, PublicUpTime=uptime_pub, PublicList=list_pub, EmailUpTime=uptime_eml, EmailList=list_eml)

    else:
        return render_template('email_report.html',title='Uptime Report', form=form)


@app.route('/_navols', methods=['POST'])
def _navols():
    volumes = request.get_json(silent=True)

    with open('storage.txt', 'w') as outfile:
        outfile.write(volumes)
    return jsonify({'text':'200'})

@app.route('/_nahealth', methods=['POST'])
def _nahealth():
    netapp_health_data = request.get_json(silent=True)
    netapp_health = json.dumps(netapp_health_data)
    with open('nahealth.txt', 'w') as outfile:
        outfile.write(netapp_health)
    return jsonify({'status_code':'201'})

@app.route('/_winupdates', methods=['POST'])
def _winupdates():
    windows_update_data = request.get_json(silent=True)
    windows_update_health = json.dumps(windows_update_data)
    with open('wsushealth.txt', 'w') as outfile:
        outfile.write(windows_update_health)
    return jsonify({'status_code':'201'})

@app.route('/_flips', methods=['POST'])
def _flips():
    if 'logged_in' in session:
        before_request()
        data = request.form['text']
        sideincheck = ns.bindings(session['ns_name'], session['ns_auth_token'])
        if data == 'pvt_web':
            for servicegroup in sideincheck:
                if servicegroup['vs'] == 'pvt_web':
                    sidein = servicegroup['svcg']
            if sidein == 'A':
                bindsvcghttp = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PVT_VS_HTTP'], app.config['PVT_SIDE_B_HTTP'], session['ns_auth_token'])
                unbindsvcghttp = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PVT_VS_HTTP'], app.config['PVT_SIDE_A_HTTP'], session['ns_auth_token'] )
                bindsvcgapi = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PVT_VS_API'], app.config['PVT_SIDE_B_API'], session['ns_auth_token'])
                unbindsvcgapi = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PVT_VS_API'], app.config['PVT_SIDE_A_API'], session['ns_auth_token'] )
                bindstagesvcghttp = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PVT_VS_HTTP'], app.config['PVT_SIDE_A_HTTP'], session['ns_auth_token'])
                unbindstagesvcghttp = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PVT_VS_HTTP'], app.config['PVT_SIDE_B_HTTP'], session['ns_auth_token'] )
                bindstagesvcgapi = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PVT_VS_API'], app.config['PVT_SIDE_A_API'], session['ns_auth_token'])
                unbindstagesvcgapi = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PVT_VS_API'], app.config['PVT_SIDE_B_API'], session['ns_auth_token'] )
                results = ns.bindings(session['ns_name'], session['ns_auth_token'])
                for result in results:
                    if result['vs'] == 'pvt_web':
                        response =  'Updated to Side ' + result['svcg']
                        svcg = result['svcg']
                ns.nssaveconfig(session['ns_name'], session['ns_auth_token'])
                return jsonify({'text': response, 'svcg': svcg })
            elif sidein == 'B':
                bindsvcghttp = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PVT_VS_HTTP'], app.config['PVT_SIDE_A_HTTP'], session['ns_auth_token'])
                unbindsvcghttp = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PVT_VS_HTTP'], app.config['PVT_SIDE_B_HTTP'], session['ns_auth_token'] )
                bindsvcgapi = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_A_API'], session['ns_auth_token'])
                unbindsvcgapi = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_B_API'], session['ns_auth_token'] )
                bindstagesvcghttp = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PVT_VS_HTTP'], app.config['PVT_SIDE_B_HTTP'], session['ns_auth_token'])
                unbindstagesvcghttp = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PVT_VS_HTTP'], app.config['PVT_SIDE_A_HTTP'], session['ns_auth_token'] )
                bindstagesvcgapi = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PVT_VS_API'], app.config['PVT_SIDE_B_API'], session['ns_auth_token'])
                unbindstagesvcgapi = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PVT_VS_API'], app.config['PVT_SIDE_A_API'], session['ns_auth_token'] )
                results = ns.bindings(session['ns_name'], session['ns_auth_token'])
                for result in results:
                    if result['vs'] == 'pvt_web':
                        response =  'Updated to Side ' + result['svcg']
                        svcg = result['svcg']
                ns.nssaveconfig(session['ns_name'], session['ns_auth_token'])
                return jsonify({'text': response, 'svcg': svcg })
            else:
                return jsonify({'text': 'Binding Failure', 'svcg': '?'})
            return jsonify({'text': response, 'svcg': svcg})
        elif data == 'pub_web':
            for servicegroup in sideincheck:
                if servicegroup['vs'] == 'pub_web':
                    sidein = servicegroup['svcg']
            if sidein == 'A':
                bindsvcg = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_B_API'], session['ns_auth_token'])
                unbindsvcg = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_A_API'], session['ns_auth_token'] )
                bindstagesvcg = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_A_API'], session['ns_auth_token'])
                unbindstagesvcg = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_B_API'], session['ns_auth_token'] )
                results = ns.bindings(session['ns_name'], session['ns_auth_token'])
                for result in results:
                    if result['vs'] == 'pub_web':
                        response =  'Updated to Side ' + result['svcg']
                        svcg = result['svcg']
                ns.nssaveconfig(session['ns_name'], session['ns_auth_token'])
                return jsonify({'text': response, 'svcg': svcg })
            elif sidein == 'B':
                bindsvcg = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_A_API'], session['ns_auth_token'])
                unbindsvcg = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_B_API'], session['ns_auth_token'] )
                bindstagesvcg = ns.ns_lb_svcg_bind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_B_API'], session['ns_auth_token'])
                unbindstagesvcg = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['PUB_VS_API'], app.config['PUB_SIDE_A_API'], session['ns_auth_token'] )
                results = ns.bindings(session['ns_name'], session['ns_auth_token'])
                for result in results:
                    if result['vs'] == 'pub_web':
                        response =  'Updated to Side ' + result['svcg']
                        svcg = result['svcg']
                ns.nssaveconfig(session['ns_name'], session['ns_auth_token'])
                return jsonify({'text': response, 'svcg': svcg })
            else:
                return jsonify({'text': 'Binding Failure', 'svcg': '?'})
            return jsonify({'text': response, 'svcg': svcg})
        elif data == 'beta_web':
            #sideincheck = ns.bindings(session['ns_name'], session['ns_auth_token'])
            for servicegroup in sideincheck:
                if servicegroup['vs'] == 'beta_web':
                    sidein = servicegroup['svcg']
            if sidein == 'A':
                bindsvcg = ns.ns_lb_svcg_bind(session['ns_name'], app.config['BETA_VS_API'], app.config['BETA_SIDE_B_API'], session['ns_auth_token'])
                unbindsvcg = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['BETA_VS_API'], app.config['BETA_SIDE_A_API'], session['ns_auth_token'] )
                results = ns.bindings(session['ns_name'], session['ns_auth_token'])
                for result in results:
                    if result['vs'] == 'beta_web':
                        response =  'Updated to Side ' + result['svcg']
                        svcg = result['svcg']
                ns.nssaveconfig(session['ns_name'], session['ns_auth_token'])
                return jsonify({'text': response, 'svcg': svcg })
            elif sidein == 'B':
                bindsvcg = ns.ns_lb_svcg_bind(session['ns_name'], app.config['BETA_VS_API'], app.config['BETA_SIDE_A_API'], session['ns_auth_token'])
                unbindsvcg = ns.ns_lb_svcg_unbind(session['ns_name'], app.config['BETA_VS_API'], app.config['BETA_SIDE_B_API'], session['ns_auth_token'] )
                results = ns.bindings(session['ns_name'], session['ns_auth_token'])
                for result in results:
                    if result['vs'] == 'beta_web':
                        response =  'Updated to Side ' + result['svcg']
                        svcg = result['svcg']
                ns.nssaveconfig(session['ns_name'], session['ns_auth_token'])
                return jsonify({'text': response, 'svcg': svcg })
            else:
                return jsonify({'text': 'Binding Failure', 'svcg': '?'})
        else:
            return jsonify({'text': 'Did not match Input', 'svcg': 'X'})
    else:
        flash('Session Expired...')
        return jsonify({'text': 403})
