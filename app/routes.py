from flask import render_template, flash, redirect, url_for, session, request, jsonify
from app import app, db
from app import nsfunctions as ns
from app.forms import LoginForm, OutageForm, ReportForm, NSForm
from app.models import Outage
from functools import wraps
from app import uptime
from datetime import datetime
import json

def login_required(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first...')
            return  redirect(url_for('login'))
    return wrap

@app.route('/')
@app.route('/index')
def index():
    if 'logged_in' in session:
        #flash('already logged in')
        ns_bound_list = ns.bindings(session['ns_name'], session['ns_auth_token'])
        return render_template('index.html', bindings=ns_bound_list)
    else:
        ns_name = 'nsvpx2.realtracs.net'
        ns_user = app.config['NS_RO_USER']
        ns_pwd = app.config['NS_RO_PWD']
        read_login = ns.nslogin(ns_name, ns_user, ns_pwd)
        if read_login.status_code == 200 or read_login.status_code == 201:
            session['read_token'] = read_login.cookies['NITRO_AUTH_TOKEN']
            #flash('logged in with ' + session['read_token'])
            ns_bound_list = ns.bindings(ns_name, session['read_token'])
            return render_template('index.html', bindings=ns_bound_list)
        else:
            flash('Something went wrong with login...')
            return render_template('index.html')
        logout_result = ns.nslogout(ns_name, session['read_token'])
        #flash(logout_result)

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

@app.route('/_bindscript', methods=['GET','POST'])
def bindscript():
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
        return jsonify({'pvt_web': pvt_web, 'pub_web': pub_web, 'beta_web': beta_web})
    else:
        flash('Something went wrong with login...')
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
