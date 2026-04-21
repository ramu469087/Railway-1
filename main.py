#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import sys
import uuid
import json
import random
import threading
import requests
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template_string, jsonify, session as flask_session
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
import pyfiglet
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

console = Console()
app = Flask(__name__)
app.secret_key = 'lord-devil-insta-tools-2024-secret-key'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global storage
active_tasks = {}
task_logs = {}
task_start_time = {}
active_sessions = {}
task_threads = {}

# ----------- LOGO -----------
def show_logo():
    os.system('clear' if os.name == 'posix' else 'cls')
    ascii_banner = pyfiglet.figlet_format("LORD DEVIL", font="slant")
    console.print(f"[bold red]{ascii_banner}[/bold red]")
    console.print("[bold cyan]🔥 INSTA TOOLS BY LORD DEVIL 🔥[/bold cyan]")
    console.print("[yellow]⚡ Messenger & Group Name Changer - 100% Working[/yellow]")
    console.print("[green]🔐 Login Methods: Cookies Only[/green]\n")

# ----------- INSTAGRAPI LOGIN -----------
def instagram_login_with_cookies(cookies_str):
    """Login to Instagram using cookies string"""
    cl = Client()
    try:
        # Parse cookies
        cookies_dict = {}
        for cookie in cookies_str.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies_dict[key.strip()] = value.strip()
        
        # Try sessionid method first
        sessionid = cookies_dict.get('sessionid', '')
        if sessionid:
            try:
                cl.login_by_sessionid(sessionid)
                user_info = cl.account_info()
                console.print(f"[green]✅ Login successful with sessionid! Username: {user_info.username}[/green]")
                return cl
            except Exception as e:
                console.print(f"[yellow]⚠️ Sessionid login failed, trying full cookies: {e}[/yellow]")
        
        # Try full cookies method
        try:
            cl.set_settings({
                "user_agent": "Instagram 219.0.0.12.117 Android",
                "device_settings": {
                    "cpu": "64-bit",
                    "dpi": "480dpi",
                    "model": "SM-G973F",
                    "device": "samsung",
                    "resolution": "1080x1920",
                    "app_version": "219.0.0.12.117",
                    "manufacturer": "samsung",
                    "version_code": "291685405"
                }
            })
            
            # Set cookies
            for key, value in cookies_dict.items():
                cl.set_cookie(key, value)
            
            # Verify login
            user_info = cl.account_info()
            console.print(f"[green]✅ Login successful! Username: {user_info.username}[/green]")
            return cl
            
        except Exception as e:
            console.print(f"[red]❌ Cookie login failed: {e}[/red]")
            return None
            
    except Exception as e:
        console.print(f"[red]❌ Login error: {e}[/red]")
        return None

# ----------- FAST API LOGIN -----------
def parse_cookies_string(cookies_str):
    """Parse cookies string to dict"""
    cookies_dict = {}
    if not cookies_str:
        return cookies_dict
    
    for cookie in cookies_str.split(';'):
        cookie = cookie.strip()
        if '=' in cookie:
            key, value = cookie.split('=', 1)
            cookies_dict[key.strip()] = value.strip()
    return cookies_dict

def verify_cookies_login(session, cookies_dict):
    """Verify Instagram cookies"""
    try:
        headers = {
            "User-Agent": "Instagram 219.0.0.12.117 Android",
            "X-IG-App-ID": "936619743392459",
        }
        
        # Set cookies
        for key, value in cookies_dict.items():
            session.cookies.set(key, value)
        
        # Try to get user info
        url = "https://i.instagram.com/api/v1/accounts/current_user/"
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            try:
                user_data = response.json()
                username = user_data.get('user', {}).get('username')
                if username:
                    return True, username
            except:
                pass
        
        # Try inbox as alternative check
        inbox_url = "https://i.instagram.com/api/v1/direct_v2/inbox/"
        response = session.get(inbox_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return True, "cookies_user"
        
        return False, None
        
    except Exception as e:
        console.print(f"[red]❌ Cookie verification error: {e}[/red]")
        return False, None

def get_random_headers():
    """Get random Instagram headers"""
    user_agents = [
        "Instagram 219.0.0.12.117 Android",
        "Instagram 220.0.0.13.119 Android",
        "Instagram 221.0.0.15.120 Android",
        "Instagram 222.0.0.16.121 Android",
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "X-IG-App-ID": "936619743392459",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

def fast_instagram_login(cookies_str=None):
    """Fast login using requests"""
    session = requests.Session()
    
    if cookies_str:
        cookies_dict = parse_cookies_string(cookies_str)
        if not cookies_dict:
            return None
        
        is_valid, detected_user = verify_cookies_login(session, cookies_dict)
        if is_valid:
            session.headers.update(get_random_headers())
            csrf = cookies_dict.get('csrftoken')
            if csrf:
                session.headers.update({'X-CSRFToken': csrf})
                session.cookies.set('csrftoken', csrf)
            console.print(f"[green]✅ Fast cookies login successful![/green]")
            return session
        else:
            console.print("[red]❌ Fast cookies login failed[/red]")
            return None
    
    return None

# ----------- MESSENGER FUNCTIONS -----------
def send_inbox_message(cl, target_username, hater_name, messages, delay, task_id):
    """Send messages to inbox/DM"""
    try:
        user_id = cl.user_id_from_username(target_username)
        index = 0
        total = len(messages)
        
        while task_id in active_tasks and active_tasks[task_id].get('running', True):
            # Check if task should stop
            if not active_tasks[task_id].get('running', True):
                add_log(task_id, "🛑 Task stopped by user", 'info')
                break
                
            try:
                full_msg = f"{hater_name} {messages[index]}" if hater_name else messages[index]
                cl.direct_send(full_msg, [user_id])
                
                # Update stats
                if 'sent_count' in active_tasks[task_id]:
                    active_tasks[task_id]['sent_count'] += 1
                else:
                    active_tasks[task_id]['sent_count'] = 1
                
                log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Sent to {target_username}: {full_msg[:50]}... (Total: {active_tasks[task_id]['sent_count']})"
                add_log(task_id, log_msg, 'success')
                
                index = (index + 1) % total
                
                # Delay with stop checking
                for _ in range(delay):
                    if task_id not in active_tasks or not active_tasks[task_id].get('running', True):
                        break
                    time.sleep(1)
                
            except Exception as e:
                err_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {str(e)[:100]}"
                add_log(task_id, err_msg, 'error')
                
                # Delay with stop checking
                for _ in range(5):
                    if task_id not in active_tasks or not active_tasks[task_id].get('running', True):
                        break
                    time.sleep(1)
                
    except Exception as e:
        err_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Fatal error: {str(e)}"
        add_log(task_id, err_msg, 'error')
    finally:
        add_log(task_id, "🛑 Task stopped completely", 'info')
        console.print(f"[red]Task {task_id} stopped completely[/red]")

def send_group_message(cl, thread_id, hater_name, messages, delay, task_id):
    """Send messages to group"""
    try:
        index = 0
        total = len(messages)
        
        while task_id in active_tasks and active_tasks[task_id].get('running', True):
            # Check if task should stop
            if not active_tasks[task_id].get('running', True):
                add_log(task_id, "🛑 Task stopped by user", 'info')
                break
                
            try:
                full_msg = f"{hater_name} {messages[index]}" if hater_name else messages[index]
                cl.direct_send(full_msg, thread_ids=[thread_id])
                
                # Update stats
                if 'sent_count' in active_tasks[task_id]:
                    active_tasks[task_id]['sent_count'] += 1
                else:
                    active_tasks[task_id]['sent_count'] = 1
                
                log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Sent to group: {full_msg[:50]}... (Total: {active_tasks[task_id]['sent_count']})"
                add_log(task_id, log_msg, 'success')
                
                index = (index + 1) % total
                
                # Delay with stop checking
                for _ in range(delay):
                    if task_id not in active_tasks or not active_tasks[task_id].get('running', True):
                        break
                    time.sleep(1)
                
            except Exception as e:
                err_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {str(e)[:100]}"
                add_log(task_id, err_msg, 'error')
                
                # Delay with stop checking
                for _ in range(5):
                    if task_id not in active_tasks or not active_tasks[task_id].get('running', True):
                        break
                    time.sleep(1)
                
    except Exception as e:
        err_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Fatal error: {str(e)}"
        add_log(task_id, err_msg, 'error')
    finally:
        add_log(task_id, "🛑 Task stopped completely", 'info')
        console.print(f"[red]Task {task_id} stopped completely[/red]")

def change_group_name_fast(session, thread_id, names, delay, task_id):
    """Ultra fast group name changer"""
    try:
        index = 0
        total = len(names)
        
        while task_id in active_tasks and active_tasks[task_id].get('running', True):
            # Check if task should stop
            if not active_tasks[task_id].get('running', True):
                add_log(task_id, "🛑 Task stopped by user", 'info')
                break
                
            try:
                new_name = names[index].strip()
                if new_name:
                    url = f"https://i.instagram.com/api/v1/direct_v2/threads/{thread_id}/update_title/"
                    data = {"title": new_name}
                    
                    response = session.post(url, data=data, headers=get_random_headers(), timeout=10)
                    
                    # Update stats
                    if 'changed_count' in active_tasks[task_id]:
                        active_tasks[task_id]['changed_count'] += 1
                    else:
                        active_tasks[task_id]['changed_count'] = 1
                    
                    if response.status_code == 200:
                        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ⚡ FAST Changed to: {new_name} (Total: {active_tasks[task_id]['changed_count']})"
                        add_log(task_id, log_msg, 'fast')
                    else:
                        err_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Fast error: HTTP {response.status_code}"
                        add_log(task_id, err_msg, 'error')
                    
                    index = (index + 1) % total
                    
                    # Delay with stop checking
                    for _ in range(delay):
                        if task_id not in active_tasks or not active_tasks[task_id].get('running', True):
                            break
                        time.sleep(1)
                    
            except Exception as e:
                err_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Fast error: {str(e)[:100]}"
                add_log(task_id, err_msg, 'error')
                
                # Delay with stop checking
                for _ in range(5):
                    if task_id not in active_tasks or not active_tasks[task_id].get('running', True):
                        break
                    time.sleep(1)
                
    except Exception as e:
        err_msg = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Fatal fast error: {str(e)}"
        add_log(task_id, err_msg, 'error')
    finally:
        add_log(task_id, "🛑 Task stopped completely", 'info')
        console.print(f"[red]Task {task_id} stopped completely[/red]")

# ----------- COMMON FUNCTIONS -----------
def add_log(task_id, message, log_type='info'):
    """Add log entry"""
    if task_id not in task_logs:
        task_logs[task_id] = []
    
    # Keep last 100 logs
    if len(task_logs[task_id]) >= 100:
        task_logs[task_id].pop(0)
    
    task_logs[task_id].append({
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'message': message,
        'type': log_type
    })

def read_messages_from_file(file):
    """Read messages/names from uploaded file"""
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        os.remove(filepath)
        return lines
    except Exception as e:
        console.print(f"[red]❌ File read error: {e}[/red]")
        return []

def get_uptime(task_id):
    """Get task uptime"""
    if task_id in task_start_time:
        elapsed = datetime.now() - task_start_time[task_id]
        hours = elapsed.seconds // 3600
        minutes = (elapsed.seconds % 3600) // 60
        seconds = elapsed.seconds % 60
        return f"{hours}h {minutes}m {seconds}s"
    return "N/A"

# ----------- FLASK ROUTES -----------
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get form data
        tool_type = request.form.get('tool_type', 'messenger')
        engine = request.form.get('engine', 'instagrapi')
        
        # Generate task ID
        task_id = str(uuid.uuid4())[:8]
        
        try:
            # Handle login based on engine
            if engine == 'instagrapi':
                cookies = request.form.get('cookies', '').strip()
                if not cookies:
                    return render_template_string(HTML_TEMPLATE, result={
                        'error': 'Please provide Instagram cookies'
                    })
                cl = instagram_login_with_cookies(cookies)
                
                if not cl:
                    return render_template_string(HTML_TEMPLATE, result={
                        'error': 'Instagram login failed. Check cookies.'
                    })
                
                # Process based on tool type
                if tool_type == 'messenger':
                    return process_messenger_instagrapi(cl, request, task_id)
                else:
                    return render_template_string(HTML_TEMPLATE, result={
                        'error': 'Name changer removed. Use Ultra Speed mode.'
                    })
                    
            else:  # Fast engine
                cookies = request.form.get('cookies', '').strip()
                if not cookies:
                    return render_template_string(HTML_TEMPLATE, result={
                        'error': 'Please provide Instagram cookies'
                    })
                
                session = fast_instagram_login(cookies_str=cookies)
                if not session:
                    return render_template_string(HTML_TEMPLATE, result={
                        'error': 'Fast login failed. Check cookies.'
                    })
                
                return process_namechanger_fast(session, request, task_id)
                
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            return render_template_string(HTML_TEMPLATE, result={
                'error': f'Error: {str(e)}'
            })
    
    return render_template_string(HTML_TEMPLATE)

def process_messenger_instagrapi(cl, request, task_id):
    """Process messenger tool with instagrapi"""
    try:
        # Get form data
        hater_name = request.form.get('hater_name', '').strip()
        message_type = request.form.get('message_type', 'inbox')
        delay = int(request.form.get('delay', 10))
        
        # Get messages
        messages = []
        if 'messages' in request.form and request.form['messages'].strip():
            messages = [msg.strip() for msg in request.form['messages'].split('\n') if msg.strip()]
        elif 'message_file' in request.files:
            file = request.files['message_file']
            if file.filename != '':
                messages = read_messages_from_file(file)
        
        if not messages:
            return render_template_string(HTML_TEMPLATE, result={
                'error': 'No messages provided'
            })
        
        # Initialize task
        active_tasks[task_id] = {'running': True, 'sent_count': 0}
        task_logs[task_id] = []
        task_start_time[task_id] = datetime.now()
        
        if message_type == 'inbox':
            target_username = request.form.get('target_username', '').strip()
            if not target_username:
                return render_template_string(HTML_TEMPLATE, result={
                    'error': 'Target username required for inbox'
                })
            
            add_log(task_id, f"Starting messenger to {target_username}", 'info')
            add_log(task_id, f"Total messages loaded: {len(messages)}", 'info')
            add_log(task_id, f"Delay: {delay} seconds", 'info')
            
            thread = threading.Thread(
                target=send_inbox_message,
                args=(cl, target_username, hater_name, messages, delay, task_id),
                daemon=True
            )
            thread.start()
            task_threads[task_id] = thread
            
            result = {
                'success': f'✅ Messenger started for @{target_username}',
                'tool_type': 'messenger',
                'hater_name': hater_name,
                'data': messages[:10],
                'delay': delay,
                'task_id': task_id,
                'target': target_username
            }
            
        else:  # Group messages
            thread_id = request.form.get('thread_id', '').strip()
            if not thread_id:
                return render_template_string(HTML_TEMPLATE, result={
                    'error': 'Thread ID required for group'
                })
            
            add_log(task_id, f"Starting group messenger for thread {thread_id}", 'info')
            add_log(task_id, f"Total messages loaded: {len(messages)}", 'info')
            add_log(task_id, f"Delay: {delay} seconds", 'info')
            
            thread = threading.Thread(
                target=send_group_message,
                args=(cl, thread_id, hater_name, messages, delay, task_id),
                daemon=True
            )
            thread.start()
            task_threads[task_id] = thread
            
            result = {
                'success': f'✅ Group messenger started for thread {thread_id}',
                'tool_type': 'messenger',
                'hater_name': hater_name,
                'data': messages[:10],
                'delay': delay,
                'task_id': task_id,
                'thread_id': thread_id
            }
        
        return render_template_string(HTML_TEMPLATE, result=result)
        
    except Exception as e:
        console.print(f"[red]❌ Messenger error: {e}[/red]")
        return render_template_string(HTML_TEMPLATE, result={
            'error': f'Messenger error: {str(e)}'
        })

def process_namechanger_fast(session, request, task_id):
    """Process fast name changer"""
    try:
        thread_id = request.form.get('thread_id', '').strip()
        delay = int(request.form.get('delay', 5))
        
        # Get names
        names = []
        if 'names_file' in request.files:
            file = request.files['names_file']
            if file.filename != '':
                names = read_messages_from_file(file)
        
        if not names:
            return render_template_string(HTML_TEMPLATE, result={
                'error': 'No names provided in file'
            })
        
        if not thread_id:
            return render_template_string(HTML_TEMPLATE, result={
                'error': 'Thread ID required'
            })
        
        # Initialize task
        active_tasks[task_id] = {'running': True, 'changed_count': 0}
        task_logs[task_id] = []
        task_start_time[task_id] = datetime.now()
        
        add_log(task_id, f"Starting FAST name changer for thread {thread_id}", 'info')
        add_log(task_id, f"Total names loaded: {len(names)}", 'info')
        add_log(task_id, f"Delay: {delay} seconds", 'info')
        
        thread = threading.Thread(
            target=change_group_name_fast,
            args=(session, thread_id, names, delay, task_id),
            daemon=True
        )
        thread.start()
        task_threads[task_id] = thread
        
        result = {
            'success': f'⚡ ULTRA SPEED name changer started for thread {thread_id}',
            'tool_type': 'namechanger_fast',
            'data': names[:10],
            'delay': delay,
            'task_id': task_id,
            'thread_id': thread_id,
            'fast_mode': True
        }
        
        return render_template_string(HTML_TEMPLATE, result=result)
        
    except Exception as e:
        console.print(f"[red]❌ Fast name changer error: {e}[/red]")
        return render_template_string(HTML_TEMPLATE, result={
            'error': f'Fast name changer error: {str(e)}'
        })

@app.route('/stop_task', methods=['POST'])
def stop_task():
    """Stop task and completely remove it"""
    data = request.get_json()
    task_id = data.get('task_id')
    
    if task_id in active_tasks:
        # Send stop signal
        active_tasks[task_id]['running'] = False
        add_log(task_id, "🛑 Stop signal sent - Task stopping...", 'info')
        
        # Wait for thread to finish (max 3 seconds)
        if task_id in task_threads:
            task_threads[task_id].join(timeout=3)
        
        # COMPLETELY REMOVE TASK - No trace left
        if task_id in active_tasks:
            del active_tasks[task_id]
        if task_id in task_logs:
            del task_logs[task_id]
        if task_id in task_start_time:
            del task_start_time[task_id]
        if task_id in task_threads:
            del task_threads[task_id]
        
        console.print(f"[red]✅ Task {task_id} stopped and removed completely[/red]")
        return jsonify({'success': True, 'message': 'Task stopped and removed completely'})
    else:
        return jsonify({'error': 'Task ID not found'})

@app.route('/get_logs')
def get_logs():
    task_id = request.args.get('task_id')
    if task_id in task_logs:
        return jsonify({'logs': task_logs[task_id]})
    else:
        return jsonify({'logs': [], 'message': 'Task not found or already removed'})

@app.route('/task_status')
def task_status_route():
    task_id = request.args.get('task_id')
    if task_id in active_tasks:
        status = active_tasks[task_id].copy()
        status['running'] = status.get('running', False)
        status['uptime'] = get_uptime(task_id)
        if 'sent_count' in status:
            status['total_sent'] = status['sent_count']
        if 'changed_count' in status:
            status['total_changed'] = status['changed_count']
        return jsonify(status)
    else:
        return jsonify({'running': False, 'message': 'Task not found or already stopped/removed'})

@app.route('/status')
def status():
    return jsonify({
        'active_tasks': len([t for t in active_tasks if active_tasks[t].get('running', False)]),
        'total_tasks_ever': 'Use task_status for specific task',
        'version': '3.0',
        'author': 'LORD DEVIL'
    })

# HTML Template (Complete Original)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🔥 INSTA TOOLS BY LORD DEVIL 🔥</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .owner-name {
            font-size: 2.5rem;
            background: linear-gradient(45deg, #ff0000, #ff9900);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #aaa;
            font-size: 1.2rem;
        }
        .mode-selector {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .mode-btn {
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
            flex: 1;
            min-width: 200px;
            text-align: center;
        }
        .mode-btn.active {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        .messenger-btn { background: linear-gradient(45deg, #2196F3, #03A9F4); }
        .fast-btn { background: linear-gradient(45deg, #00FF00, #00CC00); }
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #ddd;
            font-weight: 600;
        }
        input, select, textarea, .file-input {
            width: 100%;
            padding: 12px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: #fff;
            font-size: 16px;
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #00ffff;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
        }
        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.3s;
            width: 100%;
            background: linear-gradient(45deg, #ff0000, #ff9900);
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 0, 0, 0.3);
        }
        .form-section {
            display: none;
        }
        .form-section.active {
            display: block;
            animation: fadeIn 0.5s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.3);
        }
        .success { color: #4CAF50; font-weight: bold; }
        .error { color: #f44336; font-weight: bold; }
        .fast-indicator {
            color: #00FF00;
            font-weight: bold;
            text-shadow: 0 0 10px #00FF00;
        }
        .logs-container {
            max-height: 300px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.5);
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .log-entry {
            padding: 8px;
            margin-bottom: 5px;
            border-radius: 4px;
            font-family: monospace;
        }
        .log-success { background: rgba(76, 175, 80, 0.2); border-left: 3px solid #4CAF50; }
        .log-error { background: rgba(244, 67, 54, 0.2); border-left: 3px solid #f44336; }
        .log-info { background: rgba(33, 150, 243, 0.2); border-left: 3px solid #2196F3; }
        .log-fast { background: rgba(0, 255, 0, 0.2); border-left: 3px solid #00FF00; }
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .tab-btn {
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 5px;
            color: white;
            cursor: pointer;
        }
        .tab-btn.active {
            background: linear-gradient(45deg, #ff0000, #ff9900);
        }
        .status-card {
            background: rgba(0, 0, 0, 0.5);
            padding: 15px;
            border-radius: 10px;
            margin-top: 15px;
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .status-label {
            font-weight: bold;
            color: #aaa;
        }
        .status-value {
            color: #00FF00;
            font-weight: bold;
        }
        .task-running {
            color: #00FF00;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        @media (max-width: 768px) {
            .mode-btn { min-width: 100%; }
            .owner-name { font-size: 1.8rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="owner-name">LORD DEVIL</div>
            <div class="subtitle">INSTA TOOLS - Messenger & Ultra Speed Name Changer</div>
        </div>
        
        <div class="mode-selector">
            <button class="mode-btn messenger-btn active" onclick="switchMode('messenger')">📨 Messenger Tool</button>
            <button class="mode-btn fast-btn" onclick="switchMode('fast')">⚡ Ultra Speed Name Changer</button>
        </div>
        
        <div class="tab-buttons">
            <button class="tab-btn active" onclick="switchTab('start')">Start Task</button>
            <button class="tab-btn" onclick="switchTab('stop')">Stop Task</button>
            <button class="tab-btn" onclick="switchTab('status')">Task Status</button>
            <button class="tab-btn" onclick="switchTab('logs')">Live Logs</button>
        </div>
        
        <!-- Messenger Form -->
        <div id="messenger-form" class="form-section active">
            <div class="card">
                <h2>📨 Messenger Tool</h2>
                <form method="POST" enctype="multipart/form-data" id="messengerForm">
                    <input type="hidden" name="tool_type" value="messenger">
                    <input type="hidden" name="engine" value="instagrapi">
                    
                    <div class="form-group">
                        <label for="cookies">Instagram Cookies:</label>
                        <textarea id="cookies" name="cookies" rows="3" placeholder="sessionid=xxx; ds_user_id=xxx; csrftoken=xxx" required></textarea>
                        <small>Only cookies login supported</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="hater_name">Hater's Name (Optional):</label>
                        <input type="text" id="hater_name" name="hater_name" placeholder="Enter hater name">
                    </div>
                    
                    <div class="form-group">
                        <label for="message_type">Send to:</label>
                        <select id="message_type" name="message_type" onchange="toggleMessageType()">
                            <option value="inbox">Inbox (DM)</option>
                            <option value="group">Group</option>
                        </select>
                    </div>
                    
                    <div class="form-group" id="target_username_div">
                        <label for="target_username">Target Username:</label>
                        <input type="text" id="target_username" name="target_username" placeholder="Enter target username">
                    </div>
                    
                    <div class="form-group" id="thread_id_div" style="display: none;">
                        <label for="thread_id">Group Thread ID:</label>
                        <input type="text" id="thread_id" name="thread_id" placeholder="Enter group thread ID">
                    </div>
                    
                    <div class="form-group">
                        <label>Messages:</label>
                        <textarea id="messages" name="messages" rows="4" placeholder="Enter messages (one per line)"></textarea>
                        <small>Or upload file:</small>
                        <input type="file" id="message_file" name="message_file" class="file-input">
                    </div>
                    
                    <div class="form-group">
                        <label for="delay">Delay (seconds):</label>
                        <input type="number" id="delay" name="delay" value="10" min="1">
                    </div>
                    
                    <button type="submit" class="btn">Start Messenger</button>
                </form>
            </div>
        </div>
        
        <!-- Fast Mode Form -->
        <div id="fast-form" class="form-section">
            <div class="card">
                <h2 class="fast-indicator">⚡ ULTRA SPEED NAME CHANGER</h2>
                <form method="POST" enctype="multipart/form-data" id="fastForm">
                    <input type="hidden" name="tool_type" value="namechanger">
                    <input type="hidden" name="engine" value="fast">
                    
                    <div class="form-group">
                        <label for="fast_cookies">Instagram Cookies:</label>
                        <textarea id="fast_cookies" name="cookies" rows="3" required placeholder="sessionid=xxx; ds_user_id=xxx; csrftoken=xxx"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="fast_thread_id">Group Thread ID:</label>
                        <input type="text" id="fast_thread_id" name="thread_id" required placeholder="Enter group thread ID">
                    </div>
                    
                    <div class="form-group">
                        <label for="fast_names_file">Names File:</label>
                        <input type="file" id="fast_names_file" name="names_file" class="file-input" required>
                        <small>Upload .txt file with names (one per line)</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="fast_delay">Delay (seconds):</label>
                        <input type="number" id="fast_delay" name="delay" value="5" min="1" max="10">
                        <small>Fast mode: 1-10 seconds only</small>
                    </div>
                    
                    <button type="submit" class="btn" style="background: linear-gradient(45deg, #00FF00, #00CC00);">Start Ultra Speed</button>
                </form>
            </div>
        </div>
        
        <!-- Stop Tab -->
        <div id="stop-tab" class="form-section">
            <div class="card">
                <h2>Stop Task</h2>
                <div class="form-group">
                    <label for="stop_task_id">Enter Task ID:</label>
                    <input type="text" id="stop_task_id" placeholder="Enter task ID to stop">
                </div>
                <button class="btn" onclick="stopTask()" style="background: linear-gradient(45deg, #f44336, #d32f2f);">Stop & Remove Task</button>
                <small style="display: block; margin-top: 10px; color: #ff9999;">⚠️ Task will be completely removed after stopping</small>
            </div>
        </div>
        
        <!-- Status Tab -->
        <div id="status-tab" class="form-section">
            <div class="card">
                <h2>Task Status & Info</h2>
                <div class="form-group">
                    <label for="status_task_id">Enter Task ID:</label>
                    <input type="text" id="status_task_id" placeholder="Enter task ID to check status">
                    <button class="btn" onclick="checkTaskStatus()" style="margin-top: 10px; background: linear-gradient(45deg, #4CAF50, #45a049);">Check Status</button>
                </div>
                <div id="status_display" style="display: none;">
                    <div class="status-card">
                        <div class="status-item">
                            <span class="status-label">Task ID:</span>
                            <span class="status-value" id="status_id"></span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Status:</span>
                            <span class="status-value" id="status_running"></span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Uptime:</span>
                            <span class="status-value" id="status_uptime"></span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Total Sent/Changed:</span>
                            <span class="status-value" id="status_count"></span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Last Activity:</span>
                            <span class="status-value" id="status_last"></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Logs Tab -->
        <div id="logs-tab" class="form-section">
            <div class="card">
                <h2>Live Logs</h2>
                <div class="form-group">
                    <label for="log_task_id">Enter Task ID:</label>
                    <input type="text" id="log_task_id" placeholder="Enter task ID to view logs">
                    <button class="btn" onclick="startLogs()" style="margin-top: 10px;">Start Monitoring</button>
                </div>
                <div class="logs-container" id="logsContainer">
                    <div class="log-entry">Enter Task ID and click Start Monitoring</div>
                </div>
            </div>
        </div>
        
        <!-- Results -->
        {% if result %}
        <div class="result">
            {% if result.error %}
                <div class="error">{{ result.error }}</div>
            {% else %}
                {% if result.fast_mode %}
                    <div class="fast-indicator">⚡ ULTRA SPEED MODE ACTIVATED!</div>
                {% endif %}
                <div class="success">{{ result.success }}</div>
                <p>Task ID: <strong>{{ result.task_id }}</strong></p>
                <p>Delay: {{ result.delay }} seconds</p>
                
                <div class="logs-container">
                    <h3>Loaded Data:</h3>
                    {% for item in result.data %}
                        <div class="log-entry {% if result.fast_mode %}log-fast{% else %}log-success{% endif %}">
                            {{ item }}
                        </div>
                    {% endfor %}
                </div>
                
                <button class="btn" onclick="autoStartLogs('{{ result.task_id }}')" style="margin-top: 20px;">
                    Show Live Logs
                </button>
            {% endif %}
        </div>
        {% endif %}
    </div>

    <script>
        let currentTaskId = null;
        let logsInterval = null;
        
        function switchMode(mode) {
            document.querySelectorAll('.mode-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            document.querySelectorAll('.form-section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(mode + '-form').classList.add('active');
            switchTab('start');
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            document.querySelectorAll('.form-section').forEach(section => {
                section.classList.remove('active');
            });
            
            if (tab === 'start') {
                const activeMode = document.querySelector('.mode-btn.active').classList[1];
                if (activeMode.includes('messenger')) {
                    document.getElementById('messenger-form').classList.add('active');
                } else {
                    document.getElementById('fast-form').classList.add('active');
                }
            } else {
                document.getElementById(tab + '-tab').classList.add('active');
            }
        }
        
        function toggleMessageType() {
            const messageType = document.getElementById('message_type').value;
            document.getElementById('target_username_div').style.display = messageType === 'inbox' ? 'block' : 'none';
            document.getElementById('thread_id_div').style.display = messageType === 'inbox' ? 'none' : 'block';
        }
        
        function stopTask() {
            const taskId = document.getElementById('stop_task_id').value;
            if (!taskId) {
                alert('Please enter Task ID');
                return;
            }
            
            if (confirm('⚠️ Are you sure? Task will be completely removed and cannot be accessed after stopping!')) {
                fetch('/stop_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({task_id: taskId})
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert('✅ Task stopped and removed completely!');
                        document.getElementById('stop_task_id').value = '';
                        // Clear logs if monitoring this task
                        if (currentTaskId === taskId) {
                            if (logsInterval) clearInterval(logsInterval);
                            document.getElementById('logsContainer').innerHTML = '<div class="log-entry">Task removed. Start new task.</div>';
                        }
                    } else {
                        alert('❌ Error: ' + data.error);
                    }
                });
            }
        }
        
        function checkTaskStatus() {
            const taskId = document.getElementById('status_task_id').value;
            if (!taskId) {
                alert('Please enter Task ID');
                return;
            }
            
            fetch('/task_status?task_id=' + taskId)
                .then(res => res.json())
                .then(data => {
                    const display = document.getElementById('status_display');
                    if (data.running) {
                        document.getElementById('status_id').textContent = taskId;
                        document.getElementById('status_running').innerHTML = '<span class="task-running">● RUNNING</span>';
                        document.getElementById('status_uptime').textContent = data.uptime;
                        if (data.total_sent) {
                            document.getElementById('status_count').textContent = data.total_sent + ' messages sent';
                        } else if (data.total_changed) {
                            document.getElementById('status_count').textContent = data.total_changed + ' names changed';
                        } else {
                            document.getElementById('status_count').textContent = '0';
                        }
                        if (data.last_message) {
                            document.getElementById('status_last').textContent = data.last_message;
                        } else if (data.last_name) {
                            document.getElementById('status_last').textContent = data.last_name;
                        } else {
                            document.getElementById('status_last').textContent = 'No activity yet';
                        }
                        display.style.display = 'block';
                    } else {
                        display.style.display = 'block';
                        document.getElementById('status_id').textContent = taskId;
                        document.getElementById('status_running').innerHTML = '❌ STOPPED / REMOVED';
                        document.getElementById('status_running').style.color = '#f44336';
                        document.getElementById('status_uptime').textContent = 'N/A';
                        document.getElementById('status_count').textContent = '0';
                        document.getElementById('status_last').textContent = 'Task not found or removed';
                    }
                })
                .catch(err => {
                    alert('Error fetching status');
                });
        }
        
        function startLogs() {
            const taskId = document.getElementById('log_task_id').value;
            if (!taskId) {
                alert('Please enter Task ID');
                return;
            }
            
            currentTaskId = taskId;
            if (logsInterval) clearInterval(logsInterval);
            fetchLogs();
            logsInterval = setInterval(fetchLogs, 2000);
        }
        
        function autoStartLogs(taskId) {
            document.getElementById('log_task_id').value = taskId;
            startLogs();
            switchTab('logs');
        }
        
        function fetchLogs() {
            if (!currentTaskId) return;
            
            fetch('/get_logs?task_id=' + currentTaskId)
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('logsContainer');
                    container.innerHTML = '';
                    
                    if (data.logs && data.logs.length > 0) {
                        data.logs.forEach(log => {
                            const div = document.createElement('div');
                            div.className = 'log-entry log-' + log.type;
                            div.textContent = log.message;
                            container.appendChild(div);
                        });
                        container.scrollTop = container.scrollHeight;
                    } else if (data.message) {
                        container.innerHTML = '<div class="log-entry">' + data.message + '</div>';
                    } else {
                        container.innerHTML = '<div class="log-entry">No logs. Task may be stopped or removed.</div>';
                    }
                });
        }
        
        window.onload = function() {
            toggleMessageType();
            {% if result and not result.error %}
                autoStartLogs('{{ result.task_id }}');
            {% endif %}
        };
    </script>
</body>
</html>
"""

def main():
    show_logo()
    
    print("\n" + "="*60)
    print("🔥 INSTA TOOLS BY LORD DEVIL - VERSION 3.0 (COMPLETE REMOVE ON STOP)")
    print("="*60)
    print("\n📋 Available Features:")
    print("  1. 📨 Messenger Tool - Send messages to DM/Group")
    print("  2. ⚡ Ultra Speed Mode - Fast group name changer")
    print("  3. 🔐 Login Method: Cookies Only")
    print("\n⚙️  How to use:")
    print("  • Open browser: http://localhost:5000")
    print("  • Get cookies from browser DevTools")
    print("  • Upload names/messages in .txt file")
    print("  • Save Task ID to stop or check status later")
    print("  • Tasks run continuously until stopped manually")
    print("\n🔧 NEW FEATURE:")
    print("  • Stop karte hi task COMPLETELY REMOVE ho jayega")
    print("  • Task ID dobara use nahi kar sakte")
    print("  • Logs bhi remove ho jayenge")
    print("\n" + "="*60)
    
    print("\n[green]🚀 Starting server on http://0.0.0.0:5000[/green]")
    print("[yellow]⚠️  Press Ctrl+C to stop[/yellow]\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]⚠️  Server stopped by user[/red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        sys.exit(1)
