try:
    import console
except ImportError:
    pass
from matplotlib import colors
from configloader import ConfigLoader
import time
import codecs
import sys

        
class Printer():
    def init_config(self):
        configs = ConfigLoader()
        self.dic_color = configs.dic_color
        self.dic_user = configs.dic_user
        self.dic_title = configs.dic_title
        if (sys.platform == 'ios'):
            self.danmu_print = self.concole_print
        else:
            self.danmu_print = self.normal_print
        self.danmu_control = self.dic_user['print_control']['danmu']
        
    def control_printer(self, danmu_control=None, debug_control=None):
        if danmu_control is not None:
            self.danmu_control = danmu_control
            ConfigLoader().dic_user['print_control']['danmu'] = danmu_control
        if debug_control is not None:
            ConfigLoader().dic_user['print_control']['debug'] = debug_control
            self.debug_control = debug_control
            
    def timestamp(self, tag_time):
        if tag_time:
            str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f'[{str_time}]', end=' ')
            return str_time
        return None
        
    def info(self, list_msg, tag_time=False):
        self.timestamp(tag_time)
        for msg in list_msg:
            print(msg)
            
    def warn(self, msg):
        return
        with codecs.open(r'bili.log', 'a', encoding='utf-8') as f:
            f.write(f'{self.timestamp(True)} {msg}\n')
        # print(msg)
        
    def debug(self, msg):
        if ConfigLoader().dic_user['print_control']['debug']:
            self.info([msg], True)
            
    def error(self, msg):
        print('出现致命错误，请联系作者！！！！', msg, file=sys.stderr)
        sys.exit(-1)
            
    # "#969696"
    def hex_to_rgb_percent(self, hex_str):
        rgb_pct_color = colors.hex2color(hex_str)
        return rgb_pct_color
        
    def concole_print(self, msg, color):
        for i, j in zip(msg, color):
            console.set_color(*j)
            print(i, end='')
        print()
        console.set_color()
            
    def normal_print(self, msg, color):
        print(''.join(msg))
             
    # 弹幕 礼物 。。。。type
    def print_danmu(self, dic_msg, type='normal'):
        if not self.danmu_control:
            return
        info = dic_msg['info']

        list_msg = []
        list_color = []
        if info[7] == 3:
            # print('舰', end=' ')
            list_msg.append('⚓️ ')
            list_color.append([])
        else:
            if info[2][3] == 1:
                if info[2][4] == 0:
                    list_msg.append('爷 ')
                    list_color.append(self.dic_color['others']['vip'])
                else:
                    list_msg.append('爷 ')
                    list_color.append(self.dic_color['others']['svip'])
            if info[2][2] == 1:
                list_msg.append('房管 ')
                list_color.append(self.dic_color['others']['admin'])
                
            # 勋章
            if info[3]:
                list_color.append(self.dic_color['fans-level'][f'fl{info[3][0]}'])
                list_msg.append(f'{info[3][1]}|{info[3][0]} ')
            # 等级
            if not info[5]:
                list_color.append(self.dic_color['user-level'][f'ul{info[4][0]}'])
                list_msg.append(f'UL{info[4][0]} ')
        try:
            if info[2][7]:
                list_color.append(self.hex_to_rgb_percent(info[2][7]))
                list_msg.append(info[2][1] + ':')
            else:
                list_msg.append(info[2][1] + ':')
                list_color.append(self.dic_color['others']['default_name'])
        except:
            print("# 小电视降临本直播间")
            list_msg.append(info[2][1] + ':')
            list_color.append(self.dic_color['others']['default_name'])
            
        list_msg.append(info[1])
        list_color.append([])
        self.danmu_print(list_msg, list_color)
 
printer = Printer()


def init_config():
    printer.init_config()


def info(list_msg, tag_time=False):
    printer.info(list_msg, tag_time)


def warn(msg):
    printer.warn(msg)
        
        
def error(msg):
    printer.error(msg)
   
             
def debug(msg):
    printer.debug(msg)
  
      
def print_danmu(dic_msg, type='normal'):
    printer.print_danmu(dic_msg, type)
    
    
def control_printer(danmu_control=None, debug_control=None):
    printer.control_printer(danmu_control, debug_control)
            
