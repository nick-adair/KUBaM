from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from ucs import UCSUtil
from config import Const
from db import YamlDB

aci = Blueprint("aci", __name__)


class ACI(object):
    # List the server group information
    @staticmethod
    def list_aci():
        """
        Basic test to see if site is up.
        should return { 'status' : 'ok'}
        """
        db = YamlDB()
        err, msg, aci_list = db.list_aci(Const.KUBAM_CFG)
        if err == 1:
            return {'error': msg}, 500
        return {'aci': aci_list}, 200

    # create a new server group
    @staticmethod
    def create_aci(req):
        """
        Create a new ACI entry
        Format of request should be JSON that looks like:
        {"name", "aci01", "credentials" : {"user":"admin", "password": "secret-password",
        "ip" : "172.28.225.163" }, ...}
        """
        # Make sure we can log in first.
        msg, code = UCSUtil.check_aci_login(req)
        if code == 400:
            return msg, code
        db = YamlDB()
        err, msg = db.new_aci(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {'status': "new ACI group {0} created!". format(req["name"])}, 201

    @staticmethod
    def update_aci(req):
        """
        Update an ACI group
        """
        err, msg = UCSUtil.check_aci_login(req)
        if err == 1:
            return jsonify({'error': msg}), 400
        db = YamlDB()
        err, msg = db.update_aci(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {'status': "ACI group {0} updated!".format(req["name"])}, 201

    @staticmethod
    def delete_aci(req):
        """
        Delete the ACI group from the config.
        """
        if not isinstance(req, dict):
            return {'error': 'no details sent'}, Const.HTTP_BAD_REQUEST
        if not 'name' in req:
            return {'error': 'no name given for ACI to delete'}, Const.HTTP_BAD_REQUEST
        name = req['name']
        db = YamlDB()
        err, msg = db.delete_aci(Const.KUBAM_CFG, name)
        if err == 1:
            return {'error': msg}, 400
        else:
            return {'status': "ACI group deleted"}, 201


@aci.route(Const.API_ROOT2 + "/aci", methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin()
def aci_handler():
    if request.method == 'POST':
        j, rc = ACI.create_aci(request.json)
    elif request.method == 'PUT':
        j, rc = ACI.update_aci(request.json)
    elif request.method == 'DELETE':
        j, rc = ACI.delete_aci(request.json)
    else:
        j, rc = ACI.list_aci()
    return jsonify(j), rc
