from . import invoices, binding, types

from urllib import request, error


class Scheduler:

    PLAYGROUND_ENDPOINT = "https://pg.eet.cz:443/eet/services/EETServiceSOAP/v3/"
    PRODUCTION_ENDPOINT = "https://pg.eet.cz:443/eet/services/EETServiceSOAP/v3/"

    def __init__(self):
        self._queue = []

    def process(self, invoice):
        resp = self.send(invoice)
        if not resp:
            invoice.Hlavicka["prvni_zaslani"] = types.boolean(False)
            self._queue.append(invoice)
        return resp
    
    def dispatch(self):
        queue = []
        for invoice in self._queue:
            resp = self.send(invoice)
            if not resp:
                queue.append(invoice)
        self._queue = queue

    @staticmethod
    def send(invoice):
        xml = invoice.build()
        endpoint = Scheduler.PRODUCTION_ENDPOINT if invoice.prod() else Scheduler.PLAYGROUND_ENDPOINT

        try:
            resp = Scheduler._request(endpoint, xml)
            resp_data = binding.Soap.parse_response(resp, not invoice.prod())
            return invoices.Factory.Response(invoice.codes(), resp_data)
        except error.URLError:
            return invoices.Factory.Response(invoice.codes(), binding.Odpoved())
    
    @staticmethod
    def _request(endpoint, data):
        req = request.Request(endpoint, data, method="POST")
        with request.urlopen(req, timeout=3) as response:
            return response.read()
        