from bilibili import bilibili
from configloader import ConfigLoader
import rsa
import base64
from urllib import parse
import time

    
def calc_name_passw(key, Hash, username, password):
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(key.encode())
    password = base64.b64encode(rsa.encrypt((Hash + password).encode('utf-8'), pubkey))
    password = parse.quote_plus(password)
    username = parse.quote_plus(username)
    return username, password


class Login:
    def login(self):
        username = ConfigLoader().dic_bilibili['account']['username']
        password = ConfigLoader().dic_bilibili['account']['password']

        if not ConfigLoader().dic_bilibili['saved-session']['cookie']:
            response = bilibili().request_getkey()
            value = response.json()['data']
            key = value['key']
            Hash = str(value['hash'])
            username, password = calc_name_passw(key, Hash, username, password)
            
            response = bilibili().normal_login(username, password)
            while response.json()['code'] == -105:
                response = bilibili().login_with_captcha(username, password)
            try:
                # print(response.json())
                data = response.json()['data']
                access_key = data['token_info']['access_token']
                cookie = data['cookie_info']['cookies']
                cookie_format = ""
                for i in range(0, len(cookie)):
                    cookie_format = cookie_format + cookie[i]['name'] + "=" + cookie[i]['value'] + ";"
                dic_saved_session = {
                    'csrf': cookie[0]['value'],
                    'access_key': access_key,
                    'cookie': cookie_format,
                    'uid': cookie[1]['value']
                    }
                # print(dic_saved_session)
                bilibili().load_session(dic_saved_session)
                if ConfigLoader().dic_user['other_control']['keep-login']:
                    ConfigLoader().write2bilibili(dic_saved_session)
                print("[{}] {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '密码登陆成功'))
                return True
                
            except:
                print("[{}] 登录失败,错误信息为:{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), response.json()['message']))
                return False
                
        else:
            bilibili().load_session(ConfigLoader().dic_bilibili['saved-session'])
            print("[{}] {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '重用上次cookie登陆'))
            return True
    
    def logout(self):
        response = bilibili().request_logout()
        if response.text.find('成功退出登录') == -1:
            print('登出失败', response)
        else:
            print('成功退出登陆')
        

    
