from bs4 import BeautifulSoup
import requests
from retry import retry
import os



# あとで消すimport
from pprint import pprint
from testdata import push_testdata

# url='https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ra=013&rn=0205&ek=020538720&ae=02051&cb=0.0&ct=5.0&mb=0&mt=9999999&et=9999999&cn=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&sngz=&po1=09&page=1'
# pk='mukosugi5'

# 環境変数に「URL1」「PK」として格納済み

url = os.environ['URL1']
pk = os.environ['PK']

@retry(tries=3, delay=10, backoff=2)
def get_html(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    return soup

# 検索結果を一時格納
new_bukken_list=[]

# DBから通知済みの物件リストを取得
al_bukken_list=[]

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
        d['floor'] = tbody.findAll("td")[2].getText().strip()
        d['rents'] = tbody.findAll("td")[3].findAll("li")[0].getText().strip()
        d['siki'] = tbody.findAll("td")[4].findAll("li")[0].getText().strip()
        d['rei'] = tbody.findAll("td")[4].findAll("li")[1].getText().strip()
        d['madori'] = tbody.findAll("td")[5].findAll("li")[0].getText().strip()
        d['area'] = tbody.findAll("td")[5].findAll("li")[1].getText().strip()
        d['url'] = "https://suumo.jp" + tbody.findAll("td")[8].find("a").get("href")
        d['smn']=tbody.findAll("td")[7].find("input",{"class":"js-clipkey"})["value"]
    new_bukken_list.append(d)

# 新着データを new_bukken_list に格納完了

# DBのデータと照合

# /テストコード部/
testdata = push_testdata()
al_bukken_list=testdata
# /テストコード部/

# 既出物件リストのsmnだけをリスト化
al_bukken_list_smn=[]
for i in al_bukken_list:
    al_bukken_list_smn.append(i['smn'])

# 検索データを1件ずつ新着かどうかチェック
for data in new_bukken_list:
    smn=data['smn']
    if smn in al_bukken_list_smn:
        # print('aruyo')
        pass
    else:
        # 新着の場合はここ
        # DBに入れつつSNS通知
        pass