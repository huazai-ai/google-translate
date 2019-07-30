#!/usr/bin/python3

import sys
import readline
import warnings
import sysv_ipc as ipc
from Translator import Translator
from termcolor import colored, cprint

def main(useShm):

    host1 = "https://translate.google.cn/"
    host2 = "https://translate.google.com/"

    proxy = { "https":"localhost:8123" }

    '''
    加了-s参数后会置1 useShm,
    表示用于取词翻译的内存共享设置
    '''
    if useShm:
        warnings.simplefilter("ignore")
        path = "/tmp"
        projectID = 2333
        key = ipc.ftok(path, projectID)
        shm = ipc.SharedMemory(key, 0, 0)
        shm.attach(0,0)

    tran = Translator( targetLang='zh-CN', host=host1, proxy=None, timeout=2 )
    tran1 = Translator( targetLang='en', host=host1, proxy=None, timeout=2 )
    tran2 = tran
    currTran = 'zh-CN'

    while True:
        try:
            #获取次数为1则从参数中获取，不用input获取
            if times == 1:
                In = ' '.join(list(sys.argv))
            else:
                In = str(input('>> '))
                if useShm:
                    print("Python接收字符串: In = "+In)

            if In == '':
                if useShm:
                    #空字符串标识
                    shm.write('3', 0)
                continue
            elif In == 'zh' and not useShm:
                print('切换到翻译中文模式',end='\n\n')
                currTran = 'zh-CN'
                tran = tran1
                continue
            elif In == 'en' and not useShm:
                print('切换到翻译英文模式', end='\n\n')
                currTran = 'en'
                tran = tran2
                continue

        except Exception as e:
            print("Python捕获异常")
            print(e)
            #退出标识
            shm.write('4', 0)
            print('Good bye~')
            sys.exit()

        try:
            if useShm:
                print('准备获取翻译...')
            dataList = tran.getTran(In)
        except Exception as e:
            print(e)
            try:
                #TODO
                tran = Translator( targetLang=currTran, host=host2, proxy=proxy, timeout=2 )
                dataList = tran.getTran(In)
            except Exception as e:
                if useShm:
                    shm.write('2', 0)
                print(e)
                '''
                如果只是获取参数的翻译结果，失败后当退出，防止
                一直失败导致无限循环尝试代理连接'''
                if times == 1:
                    sys.exit(1)
                continue

        #有用数据下标 0, 1, 11, 12
        #0: 返回到界面的直接翻译
        #1: 各词性的其他翻译
        #11:不同词性的同义词
        #12:英语解释

        #获取翻译界面的直接结果
        string = str(dataList[0][0][0])
        try:
            length = len(dataList[0])
        except Exception as e:
            print(e)

        if string is None:
            continue

        if useShm:
            for i in range(1, length-1):
                cprint('    '+dataList[0][i][0], 'cyan')
                string = string + dataList[0][i][0]

            shm.write(string+'|', 10)
            print("写入:"+string+'|')
            offset = len((string+'|').encode('utf8'))
        else:
            for i in range(length-1):
                cprint('    '+dataList[0][i][0], 'cyan')

        #英语释义
        if len(dataList) > 12:
            string = tran.getSynonym(dataList[12], 0)
            #排除空字符串
            if string:
                string.replace('\n', '')
                if useShm:
                    string +=  '|'
                    print("写入:"+string)
                    shm.write(string, offset+10)
                    offset = len(string.encode('utf8')) + offset
                else:
                    print()
                    cprint("    英语释义:", 'cyan')
                    for i,ch in enumerate(string):
                        if i % 60 == 0:
                            print()
                            print('      ',end='')

                        cprint(ch, 'cyan', end='')
                    print()

        #其他翻译结果
        string = tran.getMoreTran(dataList[1], dataList[0][0][1])
        if string:
            string.replace('\n', '')
            if useShm:
                print("写入:"+string)
                shm.write(string, offset+10)
                offset = len(string.encode('utf8')) + offset
            else:
                '''
                因为此翻译程序用在了其他工程项目，加入了符号'|'用于满足
                其他工程, 这里没有必要使用，因此要将他们消除掉
                '''
                print()

                length = len(string)
                list1 = list(string)

                chNum = 0
                chIndex = 0

                '''去除最后一个无用的|,若只有一行翻译，一个|符号，则不要把它删掉
                不然会破会后面的逻辑，这里是判断竖线符号是否只有一个,并记下最后
                一个竖线符号的下标.
                这是段缝缝补补的代码....'''
                for i in range(length-1, 0, -1):
                    if list1[i] == '|':
                        chNum = chNum + 1
                        if chNum >= 2:
                            break

                        chIndex = i

                if chNum != 1:
                    list1[chIndex] = '\0'
                else:
                    str1 = ''.join(list1).replace('|', '\n')

                #将list1重新连接成字符串并替代分隔符|为'\n |-'
                if chNum != 1:
                    str1 = ''.join(list1).replace('|', '\n        |-')
                try:
                    index = str.index(str1, '\n')
                    index2 = str.index(str1,':') + 1
                    cprint('      '+str1[:index2], 'yellow', end='')
                    if len(str1[:index].encode('utf8')) > 60:
                        for i, ch in enumerate(str1[index2:index]):
                            if i % 30 == 0 and i:
                                print()
                                cprint('           ','yellow',end='')

                            cprint(ch, 'yellow', end='')
                            pass
                    else:
                        cprint(str1[index2:index], 'yellow', end='')

                    if chNum != 1:
                        print()

                    if chNum != 1:
                        cprint(str1[index:])
                    else:
                        print()

                    #print()
                except:
                    pass

        #获取相关词汇
        if len(dataList) > 12:
            if dataList[11] is not None:
                string = tran.getSynonym(dataList[11])
                if string:
                    print()
                    if useShm:
                        shm.write(string, offset+10)
                        print("写入:"+string)
                        offset = len(string.encode('utf8')) + offset
                    else:
                        #优化显示的需要，让字符串在一行内不要显示的太长
                        cprint('    相关: ', 'green', end='\n')
                        if len(string) > 60:
                            for i, ch in enumerate(string):
                                if i % 60 == 0:
                                    print()
                                    print('     ',end='')
                                cprint(ch, 'green', end='')
                                pass
                            print()
                        else:
                            cprint('        '+string, 'green')

        if useShm:
            '''
            用于其他工程项目,在第一字节内写入1表示
            内容写入完毕
            '''
            #print(shm.read())
            print('翻译写入完成')
            shm.write('\0', offset+10)
            shm.write('1', 0)

        if times == 1:
            print()
            sys.exit(0)

        print()

if __name__ == '__main__':

    #共享内存使用标识
    useShm = 0
    times = 0
    sys.argv.remove(sys.argv[0])
    if len(sys.argv) >= 1:
        for arg in sys.argv:
            if arg == '-s':
                print('Using SharedMemory')
                useShm = 1
            else:
                times = 1
                pass

    main(useShm)
