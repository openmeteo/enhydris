import datetime as dt
from io import StringIO

from django.utils.translation import ugettext_lazy as _

import requests
from defusedxml import ElementTree

from enhydris.telemetry.types import TelemetryAPIClientBase


class TelemetryAPIClient(TelemetryAPIClientBase):
    name = "Adcon addUPI"
    device_locator_label = _("Gateway or addVANTAGE server URL")
    device_locator_help_text = _(
        'Use "https://hostname:port" or "https://hostname". You can use http instead '
        "of https, but it is not recommended."
    )

    def connect(self):
        u = self.telemetry.username
        p = self.telemetry.password
        xmlroot = self._make_request(f"function=login&user={u}&passwd={p}")
        self.session_id = xmlroot.find("result/string").text

    def get_stations(self):
        xmlroot = self._make_request("function=getconfig")
        result = {}
        for node in xmlroot.findall(".//node[@class='DEVICE']"):
            label = node.attrib["name"]
            subclass = node.attrib["subclass"]
            if subclass:
                label = f"{label} [{subclass}]"
            result[node.attrib["id"]] = label
        return result

    def get_sensors(self):
        xmlroot = self._make_request("function=getconfig")
        station = xmlroot.find(f".//node[@id='{self.telemetry.remote_station_id}']")
        sensors = station.findall("./nodes/node")
        return {x.attrib["id"]: x.attrib["name"] for x in sensors}

    def get_measurements(self, sensor_id, timeseries_end_date):
        from enhydris.telemetry import TelemetryError

        if timeseries_end_date is None:
            timeseries_end_date = dt.datetime(1990, 1, 1)
        xmlroot = self._make_request(
            "function=getdata"
            f"&id={sensor_id}"
            f"&date={timeseries_end_date.isoformat()}"
            "&slots=20000"
        )
        result = ""
        prev_timestamp = None
        for record in xmlroot.findall("node/v"):
            timestamp = record.attrib["t"]
            if timestamp.startswith("+"):
                timestamp = prev_timestamp + dt.timedelta(seconds=int(timestamp))
            else:
                timestamp = dt.datetime.strptime(timestamp, "%Y%m%dT%H:%M:%S")
            s = record.attrib["s"]
            if s != "0":
                raise TelemetryError(
                    f"The record with timestamp {timestamp} has a non zero s "
                    f'attribute (s="{s}"). This is probably normal, however it is '
                    "currently not supported by the Enhydris addupi driver. Please "
                    "ask for the driver to be fixed."
                )
            prev_timestamp = timestamp
            value = float(record.text)
            result += f"{timestamp.isoformat()},{value},\n"
        return StringIO(result)

    def _make_request(self, query_string):
        from enhydris.telemetry import TelemetryError

        if hasattr(self, "session_id"):
            query_string = f"{query_string}&session-id={self.session_id}"
        url = f"{self.telemetry.device_locator}/addUPI?{query_string}"
        with requests.get(url, verify=False) as response:
            try:
                response.raise_for_status()
                # Note: Do not use response.text; use response.content.
                # The Adcon Gateway might not specify the encoding in the HTTP response
                # headers, and requests (which doesn't speak XML) will often assume the
                # wrong encoding when decoding response.content to response.text.
                # However, the encoding is correctly specified in the XML itself, and
                # if ElementTree.fromstring() is fed the undecoded response.content,
                # it reads it correctly.
                return ElementTree.fromstring(response.content)
            except requests.RequestException as e:
                raise TelemetryError(str(e))
