
import sys
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer
import traceback

class XMLRPCServer(SimpleXMLRPCServer):

    def __init__(self, dispatch_method, *args, **kwargs):
        self.dispatch_method = dispatch_method
        kwargs['logRequests'] = False
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)

    def _marshaled_dispatch(self, data, dispatch_method = None):
        """Dispatches an XML-RPC method from marshalled (XML) data.

        XML-RPC methods are dispatched from the marshalled (XML) data
        using the _dispatch method and the result is returned as
        marshalled data. For backwards compatibility, a dispatch
        function can be provided as an argument (see comment in
        SimpleXMLRPCRequestHandler.do_POST) but overriding the
        existing method through subclassing is the prefered means
        of changing method dispatch behavior.
        """

        try:
            params, method = xmlrpclib.loads(data)

            # generate response
            if dispatch_method is not None:
                response = dispatch_method(method, params)
            else:
                response = self._dispatch(method, params)
            # wrap response in a singleton tuple
            response = (response,)
            response = xmlrpclib.dumps(response, methodresponse=1,
                                       allow_none=self.allow_none, encoding=self.encoding)
        except xmlrpclib.Fault, fault:
            response = xmlrpclib.dumps(fault, allow_none=self.allow_none,
                                       encoding=self.encoding)
        except Exception as e:
            print traceback.format_exc()
            # report exception back to server
            exc_type, exc_value, exc_tb = sys.exc_info()
            response = xmlrpclib.dumps(
                xmlrpclib.Fault(1, "%s:%s" % (exc_type, exc_value)),
                encoding=self.encoding, allow_none=self.allow_none,
                )

        return response

    def _dispatch(self, method, params):
        return self.dispatch_method(method, params)
