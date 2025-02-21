import datetime as dt
from io import StringIO

from django.utils.translation import gettext_lazy as _

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
    hide_data_timezone = True

    def connect(self):
        u = self.telemetry.username
        p = self.telemetry.password
        xmlroot = self._make_request(f"function=login&user={u}&passwd={p}")
        self.session_id = xmlroot.find("result/string").text

    def disconnect(self):
        if hasattr(self, "session_id"):
            self._make_request("function=logout")
            del self.session_id

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
        if timeseries_end_date is None:
            timeseries_end_date = dt.datetime(1990, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
        xmlroot = self._make_request(
            "function=getdata"
            f"&id={sensor_id}"
            f"&df=time_t"
            f"&date={int(timeseries_end_date.timestamp())}"
            "&slots=10000"
        )
        result = ""
        prev_timestamp = None
        for record in xmlroot.findall("node/v"):
            timestamp = record.attrib["t"]
            if timestamp.startswith("+"):
                timestamp = prev_timestamp + dt.timedelta(seconds=int(timestamp))
            else:
                timestamp = dt.datetime.fromtimestamp(
                    int(timestamp), dt.timezone.utc
                ).replace(tzinfo=None)
            value = float(record.text)
            flags = self._get_flags(record, timestamp)
            result += f"{timestamp.isoformat()},{value},{flags}\n"
            prev_timestamp = timestamp
        return StringIO(result)

    def _get_flags(self, record, timestamp):
        s = self._get_s_attribute(record, timestamp)
        if s in (1, 2):
            return "INVALID"
        if s < 0:
            return "MISSING"
        return ""

    def _get_s_attribute(self, record, timestamp):
        try:
            s = None
            s = record.attrib["s"]
            si = int(s)
            if si < -99 or si > 2:
                raise ValueError()
            return si
        except (KeyError, ValueError):
            from enhydris.telemetry import TelemetryError

            raise TelemetryError(
                f"The record with timestamp {timestamp} has an invalid status "
                f'value (s="{s}")'
            )

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
                xmlroot = ElementTree.fromstring(response.content)
                error = xmlroot.find("error")
                if error is not None:
                    raise requests.RequestException(error.attrib["msg"])
                return xmlroot
            except requests.RequestException as e:
                raise TelemetryError(str(e))
