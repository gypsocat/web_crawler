from bs4 import BeautifulSoup
import json
import re
import sys
import requests
import os
import time
import csv


#向指定url爬取，获得未处理的beautifulsoup
def askurl(url):
    headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Cookie': 'bid=kgATzEVw3Sc; douban-fav-remind=1; ll="118371"; _ga=GA1.2.309249037.1657293685; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1685710884%2C%22https%3A%2F%2Fuestc.feishu.cn%2F%22%5D; _pk_ses.100001.4cf6=*; ap_v=0,6.0; __yadk_uid=7Sow34lCrkdoraL83JvvRHITBDsSWaB4; __utma=30149280.309249037.1657293685.1676721591.1685710885.12; __utmc=30149280; __utmz=30149280.1685710885.12.7.utmcsr=uestc.feishu.cn|utmccn=(referral)|utmcmd=referral|utmcct=/; __utma=223695111.309249037.1657293685.1685710885.1685710885.1; __utmb=223695111.0.10.1685710885; __utmc=223695111; __utmz=223695111.1685710885.1.1.utmcsr=uestc.feishu.cn|utmccn=(referral)|utmcmd=referral|utmcct=/; _vwo_uuid_v2=D4388D9A5CC673607B995CA687B7F9711|71308ed975144e9d462b75ce44e5edb6; __utmt=1; __gads=ID=2903cc40ac447f2a-22d8cdb287d3004b:T=1657293685:RT=1685711606:S=ALNI_MbcCEIaw4W1T1R9zPZ-nTQK_jv7BQ; __gpi=UID=00000780cfd5b2e6:T=1657293685:RT=1685711606:S=ALNI_MYeno0RZzCkmQPjn_plxjg_zxKgnA; __utmb=30149280.3.10.1685710885; _pk_id.100001.4cf6=8dfb0a9970c5de6d.1685710884.1.1685711645.1685710884.',
    'Host': 'movie.douban.com',
    'Pragma': 'no-cache',
    'Referer': 'https://uestc.feishu.cn/',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="8"',
    'sec-ch-ua-mobile': '?0',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 SLBrowser/8.0.1.4031 SLBChan/30'
    }
    resp = requests.get(url, headers=headers)
    bs=BeautifulSoup(resp.text,'html.parser')
    return bs

#获取指定要爬取的 Top m 个电影的前 n 页最新评论电影信息并保存到.json文件
def getdata(m,n):

    movie_url_base = 'https://movie.douban.com/top250?start='
    movie_list=[]
    comment_list=[]
    
    #对top m 个电影进行处理
    for i in range(0,m):
        #获取真正的url
        movie_url=movie_url_base+str(i)
        #对一个电影进行处理
        movie_bs = askurl(movie_url)
        movie=movie_bs.find("div", {"class": "item"})
        movie_hd = movie.find("div", {"class": "hd"})
        movie_href = movie_hd.find("a")["href"]
        movie_id = movie_href.split("/")[-2]
        movie_title = movie_hd.find("span", {"class": "title"}).get_text()
        movie_rating = movie.find("span", {"class": "rating_num"}, {"property": "v:average"}).get_text()

        comment_url_base = movie_href + "comments?sort=time&start="
        
        #对该电影的前n页最新评论进行处理
        for j in range(0,n):
            comment_url=comment_url_base+str(j//20)
            comment_bs = askurl(comment_url)

            for comment in comment_bs.find_all("div", {"class": "comment-item"}):
                comment_cid=comment['data-cid']
                comment_timestamp=comment.find("span",{"class":"comment-time"})["title"]
                match = re.search(r'<span class="allstar(\d*) rating" title="(.*)"></span>',str(comment))
                if match:
                    comment_rating = match.group(2)
                else:
                    comment_rating = "未评分"  # 没有找到匹配项时可以设置默认值
                comment_content=comment.find("p",{"class":"comment-content"}).find("span", {"class":"short"}).get_text()

                #处理完的评论加入评论列表
                item={"movie_id":movie_id,
                      "comment_cid": comment_cid,
                      "comment_timestamp": comment_timestamp,
                      "comment_rating":comment_rating,
                      "comment_content":comment_content}
                comment_list.append(item)

        #处理完的电影加入电影列表
        item={"movie_id":movie_id,"movie_title":movie_title,"movie_rating":movie_rating}
        movie_list.append(item)

    

    
    now_time = time.strftime('%Y%m%d%H%M%S', time.localtime())
    
    #将电影数据存入“time_movie_info.json”文件
    with open (os.getcwd() + "/upload/"+now_time+"_movie_info.json","a",encoding='utf-8') as f:
        json.dump(movie_list, f, indent=4, ensure_ascii=False)

    #将电影评论存入“time_movie_comment.json”文件
    with open (os.getcwd() + "/upload/"+now_time+"_movie_comment.json","a",encoding='utf-8') as f:
        json.dump(comment_list, f, indent=4, ensure_ascii=False)

    #将电影数据存入“time_movie_info.csv”文件
    json2csv(now_time+"_movie_info.json")
    
    #将电影评论存入“time_movie_comment.csv”文件
    json2csv(now_time+"_movie_comment.json")

def json2csv(json_name):
    with open("./upload/"+json_name,'r',encoding='utf-8') as jf:
        data=json.load(jf)

    header=data[0].keys()


    split=os.path.splitext(json_name)
    csv_name=split[0]+'.csv'

    with open("./csv/"+csv_name,'w+',newline='',encoding='utf-8') as cf:
        writer=csv.writer(cf)
        writer.writerow(header)
        for item in data:
            writer.writerow(item.values())

if __name__ == '__main__':
    m=int(sys.argv[1])
    n=int(sys.argv[2])
    getdata(m,n)

