import urllib.parse
import requests # requires a module install
import xml.etree.ElementTree as ET
import time
import hashlib

# have a look at this document to see how authentication works: https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/AVM_Technical_Note_-_Session_ID_english_2021-05-03.pdf

LOGIN_URL = '/login_sid.lua?version=2'

class FritzBoxAuthenticator:
    def __init__(self, base_url: str, user: str, password: str) -> None:
        self.url = urllib.parse.urljoin(base_url, LOGIN_URL)
        self.user = user
        self.password = password

    """Authenticates at the fritz-box and returning the session-id"""
    def auth(self) -> str:
        auth_info = self.__get_auth_info()
        self.__respect_block_time(auth_info['block_time'])
        response = self.__get_challenge_response(auth_info['challenge'])
        session_id = self.__get_session_id(response)

        return session_id
    
    def logout(self, session_id: str) -> None:
        logout_data = {
            'username': self.user,
            'sid': session_id,
            'logout': 1
        }

        post_data = urllib.parse.urlencode(logout_data).encode()
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
        post_response = requests.post(self.url, post_data, headers=headers)

        if post_response.status_code != 200:
            raise Exception(f'unable to logout. received status-code "{post_response.status_code}"')
    
    """Get information from the login-endpoint to get information about challenge"""
    def __get_auth_info(self) -> dict[str, any]:
        response = requests.get(self.url)

        if response.status_code != 200:
            raise Exception(f'unable to retrieve authentication-information. received status-code "{response.status_code}"')
        
        xml_tree = ET.ElementTree(ET.fromstring(response.content))
        xml_root = xml_tree.getroot()

        challenge = xml_root.find('Challenge').text
        block_time = int(xml_root.find('BlockTime').text)

        if len(challenge) < 1:
            raise Exception('unable to find challenge in authentication-information')
        
        return {
            'challenge': challenge,
            'block_time': block_time,
        }
    
    def __respect_block_time(self, block_time: int) -> None:
        if block_time > 0:
            time.sleep(block_time)

    def __get_challenge_response(self, challenge: str) -> str:
        tokens = self.__get_challenge_tokens(challenge)

        if tokens['version'] != 2:
            raise Exception(f'login version "{tokens["version"]}" is not (yet) supported')
        
        hash1 = self.__pbkdf2_hex(self.password.encode(), tokens['salt1'], tokens['iter1'])
        hash2 = self.__pbkdf2_hex(hash1, tokens['salt2'], tokens['iter2'])

        response = f'{tokens["salt2"].hex()}${hash2.hex()}'
        return response
    
    def __get_session_id(self, challenge_response: str) -> str:
        data_dict = {
            'username': self.user,
            'response': challenge_response
        }

        post_data = urllib.parse.urlencode(data_dict).encode()
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' }

        response = requests.post(self.url, post_data, headers=headers)

        if response.status_code != 200:
            raise Exception(f'error while getting session-id. received status-code "{response.status_code}"')
        
        xml_tree = ET.ElementTree(ET.fromstring(response.content))
        xml_root = xml_tree.getroot()
        session_id = xml_root.find('SID').text

        if len(session_id) < 1 or session_id == '0000000000000000':
            raise Exception('wrong username or password')
        
        return session_id

    def __get_challenge_tokens(self, challenge: str) -> dict[str, any]:
        split = challenge.split('$')
        if len(split) < 5:
            raise Exception(f'challenge "{challenge}" is not in the right format')
        
        tokens = {
            'version': int(split[0]),
            'iter1': int(split[1]),
            'salt1': bytes.fromhex(split[2]),
            'iter2': int(split[3]),
            'salt2': bytes.fromhex(split[4]),
        }
        return tokens

    def __pbkdf2_hex(self, password_bytes: bytes, salt: bytes, iterations: int) -> bytes:
        hashed_password = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, iterations)
        return hashed_password

