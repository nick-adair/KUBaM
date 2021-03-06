from ucscsdk.ucschandle import UcscHandle
from ucscsdk.ucscexception import UcscException
from helper import KubamError
import socket
from urllib2 import HTTPError


class UCSCSession(object):
    # Get the current firmware version.  Returns something like: 3.1(2b)

    # Returns handle or error message
    def login(self, username, password, server):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(20)
        try:
            result = s.connect_ex((server, 443))
            if result != 0:
                return None, "{0} on port 443 is not reachable.".format(server)
            s.close()
        except Exception as e:
            return None, "UCS Central connection error: {0} {1}".format(server, e)
            
        handle = EUcscHandle(server, username, password)
        try:
            handle.login()
        except UcscException as err:
            print "Login Error: " + err.error_descr
            return None, err.error_descr
        except HTTPError as err:
            print "Connection Error: Bad UCSC? " + err.reason
            return None, err.reason
        except Exception as e:
            print "Issue logging in. Please check that all parameters are correct"
            print e
            return None, "Issue logging in: {0}".format(str(e))

        return handle, None

    @staticmethod
    def logout(handle):
        try:
            handle.logout()
        except UcscException as e:
            raise KubamError(str(e))


class EUcscHandle(UcscHandle):
    
    def rawXML(self, xml):
        from ucscsdk import ucscxmlcodec
        # send the XML to UCS Central

        response_str = self.post_xml(xml, dme="resource-mgr")
        try: 
            dn_dict = {}
            if response_str:
                response = ucscxmlcodec.from_xml_str(response_str, self)
            for out_mo in response.out_configs.child:
                dn_dict[out_mo.dn] = out_mo    
            return dn_dict
        except:
            raise
        return None
