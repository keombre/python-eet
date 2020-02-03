from . import invoices, binding, helpers

from urllib import request, error


class Scheduler:

    PLAYGROUND_ENDPOINT = "https://pg.eet.cz:443/eet/services/EETServiceSOAP/v3/"
    PRODUCTION_ENDPOINT = "https://pg.eet.cz:443/eet/services/EETServiceSOAP/v3/"

    @staticmethod
    def send(invoice):
        xml = invoice.build()
        endpoint = Scheduler.PRODUCTION_ENDPOINT if invoice.prod() else Scheduler.PLAYGROUND_ENDPOINT

        resp = Scheduler._request(endpoint, xml)
        resp_data = binding.Soap.parse_response(resp, not invoice.prod())
        
        return invoices.Factory.Response(invoice.codes(), resp_data)
    
    @staticmethod
    def _request(endpoint, data):
        try:
            req = request.Request(endpoint, data, method="POST")
            with request.urlopen(req, timeout=3) as response:
                return response.read()
        except error.URLError:
            raise ValueError("EET gate unreachable. Check internet connection")
