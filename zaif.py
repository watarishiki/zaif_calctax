from zaifapi import *
import json
import numpy as np
import datetime
import csv
from collections import OrderedDict

#zaifapiによる損益計算及びその出力クラス
class CalcZaif():

    def __init__(self):
        # apiキーとパスワードの読み込み
        with open('input.csv', 'r') as input:
            reader = csv.DictReader(input)
            for row in reader:
                apikey = row["apikey"]
                apisecret = row["api_secret"]

        self.public = ZaifPublicApi()
        self.private = ZaifTradeApi(apikey, apisecret)
        self.owninfo = self.private.get_info()
        self.deposit_jpylist = {}


    #通貨ペア名を取得：大文字を小文字にキャスト
    #@param currency_name:通貨名
    #@return: {string}通貨ペア名
    def pair_name(self,currency_name):
        return str.lower(currency_name) + '_jpy'

    #資産の円換算
    #@return: {float}通貨の日本円換算
    def deposit_jpy(self,currency_name):
        #保有量*最終取引価格で取引ペアの日本円換算
        return self.owninfo['deposit'][currency_name]*self.public.last_price(self.pair_name(currency_name))['last_price']

    #全ての保有通貨の円換算をそれぞれ出す
    def deposit_jpyall(self):
        for i in self.owninfo['deposit']:
            #jpyは例外でそのままリストに加える
            if i == "jpy":
                self.deposit_jpylist[i] = self.owninfo['deposit']['jpy']
                continue
            self.deposit_jpylist[i] = self.deposit_jpy(i)
        return self.deposit_jpylist

    #資産総額の日本円換算
    def deposit_jpytotal(self):
        total = 0
        for i in self.deposit_jpylist:
            total += self.deposit_jpylist[i]
        return total

    #各通貨の資産総額に占める割合
    #資産の円換算(jpyはそのまま)/資産総額
    def deposit_jpyratio(self,currency_name):
        if currency_name == 'jpy':
            return self.deposit_jpylist['jpy']/self.deposit_jpytotal()*100.0
        else:
            return self.deposit_jpy(currency_name)/self.deposit_jpytotal()*100.0

    #通貨の資産総額に占める割合（全通貨）
    #@return : {dict}保持する通貨名と資産割合
    def deposit_jpyratioall(self):
        ratioall = {}
        for i in self.deposit_jpylist:
            #キー：通貨名、バリュー：資産割合で格納
            ratioall[i] = self.deposit_jpyratio(i)
        return ratioall

    #各通貨の取引履歴
    #@param
    # currency_name: 通貨名
    #@return : {dict}通貨名の取引履歴
    def trade_history(self,currency_name):
        history = self.private.trade_history(currency_pair = self.pair_name(currency_name))
        #それぞれの取引履歴のタイムスタンプを日付に直して格納
        for i in history:
            history[i]['date']=datetime.datetime.fromtimestamp(float(history[i]['timestamp'])).strftime('%Y/%m/%d %H:%M:%S')
        return history

    #取引履歴の追加
    def add_history(self,history,currency_pair):
        with open('add.csv', 'r') as input:
            reader = csv.DictReader(input)
            for row in reader:
                if currency_pair == row["currency_pair"]:
                    history[row["TimeStamp"]]={
                        "date": row["date"],
                        "your_action": row["your_action"],
                        "fee_amount": float(row["fee"]),
                        "amount": float(row["order_amount"]),
                        "price": float(row["price"]),
                        "currency_pair": row["currency_pair"]
                        }
        return history

    #取引履歴から取得平均、損益を計算
    #@param
    # history {dict}取引履歴
    #@return: {dict}取得平均、損益、その他の情報を追加した取引履歴
    def calc_profit(self,history):
        index = 0 #ループ回数インデックス
        balance = [] #残高数量のリスト
        TradeVolumeList = [] #取引数量のリスト
        TradeAmountList = [] #取引金額のリスト
        totalprofit = 0
        for k,v in sorted(history.items()):

            #売りの履歴からの場合例外処理
            if index == 0 and history[k]['your_action'] == "ask":
                print('売りから入っていて不正な履歴です。他取引所からの入金を反映させてください。通貨名：',history[k]['currency_pair'])
                return 0

            #売りならfeeを通貨換算の値にする
            if history[k]['your_action'] == "ask":
                history[k]['fee_amount'] = history[k]['fee_amount']/history[k]['price']

            #取引数量設定
            #買いなら手数料を抜いた値が取引される
            if history[k]['your_action'] == "bid":
                history[k]['取引数量'] = history[k]['amount'] - history[k]['fee_amount']
                TradeVolumeList.append(history[k]['取引数量'])
            #売りなら取引数量は変わらない
            else:
                history[k]['取引数量'] = -1 * history[k]['amount']

            #取引金額（円）設定
            history[k]['取引円'] = history[k]['取引数量'] * history[k]['price']

            #総平均計算のためにリストに追加する
            if history[k]['your_action'] == "bid":
                TradeAmountList.append(history[k]['取引円'])

            #残高数量設定
            if index == 0:
                history[k]['残高数量'] = history[k]['取引数量']
                balance.append(history[k]['残高数量'])
            else:
                history[k]['残高数量'] = balance[index - 1] + \
                                                  history[k]['取引数量']
                balance.append(history[k]['残高数量'])

            #残高（円）と取得平均の算出
            history[k]['残高円'] = history[k]['残高数量'] * history[k]['price']
            history[k]['総平均'] = sum(TradeAmountList) / sum(TradeVolumeList)

            #売りの場合損益を計算
            if history[k]['your_action'] == "ask":
                history[k]['損益'] = -1 * history[k]['取引円'] - history[k]['総平均'] * -1 * history[k]['取引数量']-history[k]['fee_amount']
                totalprofit += history[k]['損益']

            #損益の累計を計算
            history[k]['累計損益']=totalprofit
            # print(k, json.dumps((v), indent=4, ensure_ascii=False))
            # print('合計損益', totalprofit)

            #（最終取引価格-取得平均）×　最新の残高 で含み益
            self.Unrealized_gains = (self.public.last_price(history[k]['currency_pair'])['last_price'] - history[k]['総平均']) * balance[-1]
            # print(k,v)
            index += 1

        return history

    # 取引履歴をcsv形式で出力
    # @param
    # history {dict}取得平均、損益、その他の情報を追加した取引履歴
    # mode {string}モード選択 w:新規書き込みモード a:追記モード
    def export_csv(self,history,mode):
        header = ['date','currency_pair','your_action','price','order_amount','fee bid:crypto ask:jpy','取引数量','取引金額','残高数量','残高円','総平均','損益','累計損益']

        print(history)
        with open('output.csv', mode) as f:
          writer = csv.writer(f)  # writerオブジェクトを作成
          writer.writerow(header) # ヘッダーを書き込む
          writer.writerows(history)  # 内容を書き込む

    def exportgains_csv(self):
        with open('output.csv', 'a') as f:
          writer = csv.writer(f)  # writerオブジェクトを作成
          writer.writerow(['含み益',calzaif.Unrealized_gains]) # ヘッダーを書き込む

    # 辞書型をリストに変換
    # @param
    # history {dict}取引履歴
    # @return
    # {リスト}取引履歴
    def conv_list(self,history):
        body =[]
        for x, y in sorted(history.items()):
            pl = history[x]['損益'] if history[x][
                                              'your_action'] == 'ask' else 0
            body.append([history[x]['date'], history[x]['currency_pair'],
                         history[x]['your_action'], history[x]['price'],
                         history[x]['amount'], history[x]['fee_amount'],
                         history[x]['取引数量'], history[x]['取引円'],
                         history[x]['残高数量'], history[x]['残高円'],
                         history[x]['総平均'], pl, history[x]['累計損益']
                         ])
        return body

    #trade_history(),conv_list(),含み益表示を一度に行う
    def WriteProfitToCsv(self,currency_name):
        trade_history = self.trade_history(currency_name)
        trade_added_history = self.add_history(trade_history,self.pair_name(currency_name))
        trade_profit = self.calc_profit(trade_added_history)
        trade_list = self.conv_list(trade_profit)
        return trade_list

calzaif = CalcZaif()
print(calzaif.owninfo)
print(calzaif.owninfo['deposit'])

#jpyは計算して欲しくないので退避してリストから削除する
jpydeposit = calzaif.owninfo['deposit']['jpy']
del calzaif.owninfo['deposit']['jpy']

#depositにある通貨ごとに取引履歴の取得、利益の計算、結果の出力を行う
for index,k in enumerate(calzaif.owninfo['deposit']):
    if index == 0:
        print(k)
        trade_list = calzaif.WriteProfitToCsv(k)
        calzaif.export_csv(trade_list,'w')
        calzaif.exportgains_csv()
    else:
        print(k)
        trade_list = calzaif.WriteProfitToCsv(k)
        calzaif.export_csv(trade_list,'a')
        calzaif.exportgains_csv()







