import os
from bs4 import BeautifulSoup
import requests
import boto3

def lambda_handler(event, context):
    # 環境変数にURLとパーティションキーを指定済み
    # Lambdaの数が増えても環境変数で対応
    url = os.environ['URL1']
    pk = os.environ['PK']
    
    # メールテスト用コード SNS通知テストのときはここのコメントアウトを外して以下をすべてコメントアウト
    # client = boto3.client('sns')
    # client.publish(
    #     TopicArn = 'arn:aws:sns:ap-northeast-1:【】:【】',
    #     Message = 'test',
    #     Subject = '新着物件情報'
    # )

    # DynamoDBとコネクションを確立
    dynamodb = boto3.resource('dynamodb')
    # テーブルとコネクションを確立
    table = dynamodb.Table('redb')
    
    # 読み込んで格納(Itemsのみ)
    response = table.scan(ReturnConsumedCapacity='TOTAL')['Items']
    
    # DBから通知済みの物件リストを取得
    al_bukken_list_smn=[]
    for i in response:
        al_bukken_list_smn.append(i['smn'])


    # @retry(tries=3, delay=10, backoff=2) エラーが多発した場合はretryモジュールの導入を検討
    def get_html(url):
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
        return soup

    # 検索結果を一時格納
    new_bukken_list=[]
    
    soup=get_html(url)
    
    items = soup.findAll("div", {"class": "cassetteitem"})
    
    for item in items:
        d={}
        d['pk'] = pk
        d['name'] = item.find("div", {"class": "cassetteitem_content-title"}).getText().strip()
        d['cat'] = item.find("div", {"class": "cassetteitem_content-label"}).getText().strip()
        d['address'] = item.find("li", {"class": "cassetteitem_detail-col1"}).getText().strip()
        d['age'] = item.find("li", {"class": "cassetteitem_detail-col3"}).findAll("div")[0].getText().strip()
        d['stair'] = item.find("li", {"class": "cassetteitem_detail-col3"}).findAll("div")[1].getText().strip()
        stations = item.findAll("div", {"class": "cassetteitem_detail-text"})
        station_name=[]
        for i in stations:
            station_name.append(i.getText().strip())
        d['station']=station_name
    
        tbodys = item.find("table", {"class": "cassetteitem_other"}).findAll("tbody")
        for tbody in tbodys:
            d['smn']=tbody.findAll("td")[7].find("input",{"class":"js-clipkey"})["value"]
            d['floor'] = tbody.findAll("td")[2].getText().strip()
            d['rents'] = tbody.findAll("td")[3].findAll("li")[0].getText().strip()
            d['siki'] = tbody.findAll("td")[4].findAll("li")[0].getText().strip()
            d['rei'] = tbody.findAll("td")[4].findAll("li")[1].getText().strip()
            d['madori'] = tbody.findAll("td")[5].findAll("li")[0].getText().strip()
            d['area'] = tbody.findAll("td")[5].findAll("li")[1].getText().strip()
            d['url'] = "https://suumo.jp" + tbody.findAll("td")[8].find("a").get("href")
        if d['smn'] in al_bukken_list_smn:
            continue
        new_bukken_list.append(d)
    
    if new_bukken_list:
        #SNSと接続を確立
        client = boto3.client('sns')
        
        for j in new_bukken_list:
            table.put_item(Item=j)
            #同時に新規物件内容をSNS通知
            client = boto3.client('sns')
            client.publish(
                TopicArn = 'arn:aws:sns:ap-northeast-1:【自分の数字に】:【ここをsnsネームに】',
                Message = j,
                Subject = '新着物件情報'
            )
    
    