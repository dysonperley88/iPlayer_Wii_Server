from __future__ import print_function
import requests as reqs
from flask import Flask, Response, send_from_directory, send_file, request
import os
import xml.etree.ElementTree as ET

# --- FIX: absolute path for config.xml ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.xml")

tree = ET.parse(CONFIG_PATH)
root = tree.getroot()

# --- SAFE XML GETTER ---
def get_xml_value(tag, default=""):
    el = root.find(tag)
    return el.text if el is not None else default

IPLAYER_HOST = get_xml_value("host", "dysonperley.pythonanywhere.com")
IPLAYER_STATUS = get_xml_value("status", "active")
IPLAYER_VERSION_REQUIRED = get_xml_value("version_required", "Wii 1.0.12")
STATUS_MSG = get_xml_value("status_message", "")
PRELOAD_SWF = get_xml_value("preload_swf", "fonts")
MAIN_APP = get_xml_value("main_swf", "WiiiPlayer")

app = Flask(__name__)
WII_IPLAYER = MAIN_APP + ".swf"

# --- LOG REQUESTS ---
@app.before_request
def log():
    print(f"{request.method}: {request.path}, Headers: {dict(request.headers)}")

# --- VERSION FILE ---
@app.route("/version.txt")
def versionCheckFile():
    VERSION_CONTENTS = (
        f"versionRequired={IPLAYER_VERSION_REQUIRED}"
        f"&status={IPLAYER_STATUS}"
        f"&statusMessage={STATUS_MSG}"
        f"&mainApplication={MAIN_APP}"
        f"&preloadFiles={PRELOAD_SWF}"
    )

    return Response(VERSION_CONTENTS, mimetype="application/x-www-form-urlencoded")

# --- MAIN PLAYER ---
@app.route("/WiiiPlayer.swf")
def WiiiPlayer():
    return send_from_directory(os.path.join(BASE_DIR, "static"), WII_IPLAYER, mimetype="application/x-shockwave-flash")

# --- PROXY ---
@app.route("/proxy.asp", methods=["GET", "POST"])
def WiiiPlayerProxy():
    url = request.args.get("url")
    key = request.args.get("key")

    if not url:
        return "Bad request", 400

    if not key or key != "nstnstnst":
        return "Unauthorized", 403

    try:
        res = reqs.get(url, stream=True)

        return Response(
            res.iter_content(chunk_size=1024),
            status=res.status_code,
            content_type=res.headers.get("Content-Type")
        )
    except reqs.RequestException as e:
        return f"Error trying to fetch URI: {e}", 500

# --- FONTS ---
@app.route("/fonts.swf")
def iPlayerFonts():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "fonts.swf", mimetype="application/x-shockwave-flash")

# --- CROSSDOMAIN ---
@app.route("/crossdomain.xml")
def crossdomain():
    policy = """<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
   <allow-access-from domain="*"/>
</cross-domain-policy>"""
    return Response(policy, mimetype="application/xml")

# --- THUMBNAILS ---
@app.route("/thumbnails.xml")
def thumbnails_onserver():
    return send_file(os.path.join(BASE_DIR, "thumbnails.xml"))
