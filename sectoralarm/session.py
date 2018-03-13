'''
Sector Alarm session, using Sector Alarm app api
'''

from datetime import datetime
import json
import aiohttp
from asyncinit import asyncinit
from . import urls


async def _validate_response(response):
    """ Verify that response is OK """
    if response.status == 200:
        return await response.json()
    raise ResponseError(response.status_code, response.text)


def fix_date_short(date_string):
    '''
    Convert the short date to ISO.
    '''
    try:
        result = datetime.strptime(date_string, '%m/%d %H:%M')
        result = result.replace(datetime.now().year)
    except ValueError:
        if date_string[:5] == 'Today':
            return fix_date_short(
                datetime.now().strftime('%m/%d') + date_string[5:])
        if date_string[:9] == 'Yesterday':
            return fix_date_short(
                datetime.now().strftime('%m/%d') + date_string[9:])

    return result.isoformat()


class Error(Exception):
    ''' Sector Alarm session error '''
    pass


class RequestError(Error):
    ''' Wrapped requests.exceptions.RequestException '''
    pass


class LoginError(Error):
    ''' Login failed '''
    pass


class ResponseError(Error):
    ''' Unexcpected response '''
    def __init__(self, status_code, text):
        super(ResponseError, self).__init__(
            'Invalid response'
            ', status code: {0} - Data: {1}'.format(
                status_code,
                text))
        self.status_code = status_code
        self.text = json.loads(text)


@asyncinit
class Session:
    """ Sector Alarm app session

    Args:
        username (str): Username used to login to Sector Alarm app
        password (str): Password used to login to Sector Alarm app

    """

    async def __init__(self, username, password, panel):
        self._username = username
        self._password = password
        self._panel = panel
        self.session = await aiohttp.ClientSession().__aenter__()

    async def get_arm_state(self):
        """ Get arm state """
        response = None
        response = await self.session.get(
            urls.status(self._username, self._password, self._panel))
        res = await _validate_response(response)
        res['timeex'] = fix_date_short(res['timeex'])
        return res

    async def get_temperature(self, device_label=None):
        """ Get temperatures """
        response = None
        response = await self.session.get(urls.get_temperature(
            self._username, self._password, self._panel))
        res = await _validate_response(response)
        if device_label is not None:
            res['temperatureComponentList'] = [
                i for i in res['temperatureComponentList']
                if i['serialNo'] == device_label]
        return res

    async def get_ethernet_status(self):
        """ Get ethernet state """
        response = None
        response = await self.session.get(urls.get_ethernet_status(
            self._username,
            self._password,
            self._panel))
        res = await _validate_response(response)
        return res

    async def get_lock_devices(self):
        """ Get lock devices """
        response = None
        response = await self.session.get(urls.get_doorlock_devices(
            self._username,
            self._password,
            self._panel))
        res = await _validate_response(response)
        return res

    async def get_lock_status(self):
        """ Get lock state """
        response = None
        response = await self.session.get(urls.get_doorlock_status(
            self._username,
            self._password,
            self._panel))
        res = await _validate_response(response)
        return res

    async def set_arm_state(self, code, state):
        """ Set alarm state

        Args:
            code (str): Personal alarm code (four or six digits)
            state (str): 'ARMED_HOME', 'ARMED_AWAY' or 'DISARMED'
        """
        response = None
        response = await self.session.put(
            urls.set_armstate(self._giid),
            headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/json',
                'Cookie': 'vid={}'.format(self._vid)},
            data=json.dumps({"code": str(code), "state": state}))
        res = await _validate_response(response)
        return res

    async def get_history(self, offset=0):
        """ Get recent events
        """
        response = None
        response = await self.session.get(
            urls.history(self._username, self._password, self._panel),
            params={
                "startIndex": int(offset)})
        res = await _validate_response(response)
        for row in res['logs']:
            row['time'] = fix_date_short(row['time'])
        return res

    async def lock_doorlock(self, serialNo, code):
        """ Lock

        Args:
            serialNo (str): Device serialNo of lock
            code (str): Lock code
        """
        response = None
        response = await self.session.get(urls.lock_doorlock(
            self._username,
            self._password,
            self._panel,
            serialNo,
            code))
        res = await _validate_response(response)
        return res

    async def unlock_doorlock(self, serialNo, code):
        """ Lock

        Args:
            serialNo (str): Device serialNo of lock
            code (str): Lock code
        """
        response = None
        response = await self.session.get(urls.unlock_doorlock(
            self._username,
            self._password,
            self._panel,
            serialNo,
            code))
        res = await _validate_response(response)
        return res

    async def get_lock_config(self, device_label):
        """ Get lock configuration

        Args:
            device_label (str): device label of lock
        """
        response = None
        response = await self.session.get(
            urls.lockconfig(self._giid, device_label),
            headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Cookie': 'vid={}'.format(self._vid)})
        res = await _validate_response(response)
        return res

    async def logout(self):
        """ Logout and remove vid """
        response = None
        response = await self.session.delete(
            urls.login(),
            headers={
                'Cookie': 'vid={}'.format(self._vid)})
        await _validate_response(response)
