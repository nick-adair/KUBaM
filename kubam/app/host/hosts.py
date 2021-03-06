from flask import jsonify, request, Blueprint
from flask_cors import cross_origin
from db import YamlDB
from config import Const

hosts = Blueprint("hosts", __name__)


class Hosts(object):
    # list the server group information
    @staticmethod
    def list_hosts():
        """
        Basic test to see if site is up.
        Should return { 'status' : 'ok'}
        """
        db = YamlDB()
        err, msg, host_list = db.list_hosts(Const.KUBAM_CFG)
        if err == 1:
            return {'error': msg}, 500
        return {"hosts": host_list}, 200

    # create a new server group
    @staticmethod
    def create_hosts(req):
        """
        Create a new host entry
        """
        db = YamlDB()
        err, msg = db.new_hosts(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {'status': "Hosts created!"}, 201

    @staticmethod
    def update_hosts(req):
        """
        Given a list of hosts will completely rewrite 
        the existing hosts entries as long as the values
        of each entry are correct. 
        Should be an array of hosts passed in. 
        Basically does the same thing as a create. 
        """ 
        db = YamlDB()
        err, msg = db.new_hosts(Const.KUBAM_CFG, req)
        if err == 1:
            return {'error': msg}, 400
        return {"status": "hosts updated"}, 201

    @staticmethod
    def delete_hosts(req):
        """
        Delete the hosts group from the config.
        """
        if not isinstance(req, dict):
            return {"error": "invalid parameters: {0}".format(req)}, Const.HTTP_BAD_REQUEST
        if not "name" in req:
            return {"error": "please give the name of the host you wish to delete"}, Const.HTTP_BAD_REQUEST
        name = req["name"]
        db = YamlDB()
        err, msg = db.delete_hosts(Const.KUBAM_CFG, name)
        if err == 1:
            return {'error': msg}, 400
        else:
            return {'status': "Hosts deleted"}, 201


@hosts.route(Const.API_ROOT2 + "/hosts", methods=['GET', 'POST', 'PUT', 'DELETE'])
@cross_origin()
def host_handler():
    if request.method == 'POST':
        j, rc = Hosts.create_hosts(request.json)
    elif request.method == 'PUT':
        j, rc = Hosts.update_hosts(request.json)
    elif request.method == 'DELETE':
        j, rc = Hosts.delete_hosts(request.json)
    else:
        j, rc = Hosts.list_hosts()
    return jsonify(j), rc
