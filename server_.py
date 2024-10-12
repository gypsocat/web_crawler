from sanic import Sanic, response
from sanic.response import text, json
import os
from bs4 import BeautifulSoup
import json as ger_json # 避免json库和sanic.response.json库冲突
import re
import requests
import time
import csv
import paddlehub
import matplotlib.pyplot as plt
import numpy as np
import jieba
from wordcloud import WordCloud


app = Sanic("mySanic")


# 爬虫请求 将电影数据与评论存入json文件
@app.route("spider/",methods=['POST'])

async def spider(request):

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
    m=3
    n=5

    movie_url_base = 'https://movie.douban.com/top250?start='
    movie_list=[]

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
        comment_list=[]
        #对该电影的前n页最新评论进行处理
        for j in range(0,n):
            comment_url=comment_url_base+str(n//20)
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
    movie_info=os.getcwd() + "/upload/movie_info/"+now_time+"_movie_info.json"
    with open (movie_info,"a",encoding='utf-8') as f:
        json.dump(movie_list, f, indent=4, ensure_ascii=False)

    #将电影评论存入“time_movie_comment.json”文件
    movie_comment=os.getcwd() + "/upload/movie_comment/"+now_time+"_movie_comment.json"
    with open (movie_comment,"a",encoding='utf-8') as f:
        json.dump(comment_list, f, indent=4, ensure_ascii=False)

    convert_movie(now_time+"_movie_comment.json")

def convert_movie(filename):
    keys=[]
    with open('./upload/movie_comment/'+filename,"r",encoding="UTF-8")as file:
        body=ger_json.load(file)  
        for key in body[0]:
            if not type(body[0][key]) == type({}) and not type(body[0][key])==key([]):
                keys.append(key.strip())
            file.close()

    now_time=time.strftime('%Y%m%d%H%M%S',time.localtime())
    csv_name=now_time+"_movie_comment.csv"
    with open('./csv/'+csv_name,"w+",newline='',encoding='UTF-8')as file:
        writer=csv.DictWriter(file,fieldnames=keys)
        writer.writeheader()
        for item in body:
                item.pop('comment_list',None)
                writer.writerow(item)
    return json({"code":1,"msg":"convert successfully!","data":{"name":csv_name}})


# # 查询云端文件信息​
# @app.route("./csv", methods=['GET'])

# async def get_csv_info(request): 
#     # 获取文件名​
#     filename = request.args.get("filename")
#     path = os.getcwd() + "/csv"
#     # 判断文件是否存在​
#     if os.path.exists(path) == False or os.path.isdir(path) == False:
#         return json({"code": 0})
    
#     data = []
#     # 读取文件内容并组装为JSON​
#     with open(path + "/" + filename, 'r', encoding='UTF-8') as file:
#         n_csv = list(csv.reader(file))
#         header = n_csv[0]
#         for i in range(1, len(n_csv)):
#             n_row = n_csv[i]
#             item = {}
#             for j in range(0, len(header)):
#                 item[header[j]] = n_row[j]
#             data.append(item)
#         file.close()
#     return json(data, ensure_ascii=False)
 
# 按需查询电影信息   ​
@app.route("./movie_info", methods=['GET'])
async def get_movie_info(request):
    # 拿到request下的filename​
    filename = request.args.get("filename")
    movid_id = request.args.get("movie_id")
    path = os.getcwd() + "/csv"
    # 传入不存在的文件名​
    if filename != None and not os.path.exists(path + "/" + filename):
        return json({"code": -1, "message": "the filename is none or the file is not exist!"})
    if not filename.endswith("movie.csv"):
        return json({"code": -1, "message": "the file is not about movie!"})
    
    movies = []
    with open(path + "/" + filename, 'r', encoding='UTF-8') as file:
        n_csv = list(csv.reader(file))
        header = n_csv[0]
        for i in range(1, len(n_csv)):
            n_row = n_csv[i]
            movie = {}
            movie_author = []
            movie_actor = []
            # 只返回指定 id 的 movie 信息​
            if movie_id != None and movie_id != n_row[0]:
                continue
            # 如果是列表下的字段，拼接为列表​
            for j in range(0, len(header)):
                if header[j] == "movie_author1" and n_row[j] != None:
                    movie_author.append(n_row[j])
                elif header[j] == "movie_author2" and n_row[j] != None:
                    movie_author.append(n_row[j])
                elif header[j] == "movie_actor1" and n_row[j] != None:
                    movie_actor.append(n_row[j])
                elif header[j] == "movie_actor2" and n_row[j] != None:
                    movie_actor.append(n_row[j])
                if (header[j] != "movie_author1" and header[j] != "movie_author2" and header[j] != "movie_actor1"
                        and header[j] != "movie_actor2"):
                    movie[header[j]] = n_row[j]
            movie["movie_author"] = movie_author
            movie["movie_actor"] = movie_actorW
            movies.append(movie)
        file.close()
    return json(movies, ensure_ascii=False)

# # 按需查询影评信息  ​
# @app.route("./csv", methods=['GET'])
# async def get_comment_info(request):
#     # 拿到request下的filename​
#     filename = request.args.get("filename")
#     movid_id = request.args.get("movie_id")
#     path = os.getcwd() + "/csv"
#     # 传入不存在的文件名​
#     if filename != None and not os.path.exists(path + "/" + filename):
#         return json({"code": -1, "message": "the filename is none or the file is not exist!"})
#     if not filename.endswith("comment.csv"):
#         return json({"code": -1, "message": "the file is not about comment!"})
    
#     res = {}
#     with open(path + "/" + filename, 'r', encoding='UTF-8') as file:
#         n_csv = list(csv.reader(file))
#         header = n_csv[0]
#         comments = []
#         for i in range(1, len(n_csv)):
#             n_row = n_csv[i]
#             if (n_row[0] != movid_id):
#                 continue
#             comment = {}
#             for j in range(0, len(header)):
#                 if header[j] != "movie_id":
#                     comment[header[j]] = n_row[j]
#             comments.append(comment)
#         res["movie_id"] = movid_id
#         res["comment_list"] = comments
#         file.close()
#     return json(res, ensure_ascii=False)


def analysis(request):

    filename=request.args.get("filename")
    path=os.getcwd()+"/csv/"+filename

    now_time = time.strftime('%Y%m%d%H%M%S', time.localtime())
    analysis_path = os.getcwd() + "/csv/"+now_time+"_comment_emotion.csv"

    if not os.path.exists(path):
        print({"code":-1,"msg":"file not exsists"})
    
    # 评论内容列表​
    res = []
    with open(path, encoding='UTF-8') as file:
        c_csv = list(csv.reader(file))
        c_header = c_csv[0]
        content_index = 0
        # 获取评论字段索引值​
        for i in range(0,len(c_header)):
            if c_header[i] == "comment_content":
                content_index = i
                break
        # 获取评论内容​
        for i in range(1, len(c_csv)):
            res.append(c_csv[i][content_index])
        file.close()
        
    # senta初始化​
    senta = paddlehub.Module(name="senta_bilstm")
    # 情感分析​
    input_dict = {"text": res}
    results = senta.sentiment_classify(data=input_dict)
    key_list = {"is_positive","positive_probs", "negative_probs"}
    # 新建文件存储情感数据​
    with open(analysis_path, 'w+', newline='',encoding='UTF-8') as file:
        writer = csv.DictWriter(file, fieldnames=key_list)
        writer.writeheader()
        for item in results:
            is_positive = 0
            if item["sentiment_key"] == "positive":
                is_positive = 1
            value = {"positive_probs": format(item["positive_probs"], '.4f'),
                    "negative_probs": format(item["negative_probs"], '.4f'),
                    "is_positive": is_positive}
            writer.writerow(value)
        file.close()
    
    return json({"value":value},ensure_ascii=False)



@app.route("v1/movie/chart",methods=['POST'])
async def chart(request):
    data = request.json.get("data")
    comment_path = os.getcwd() + "/csv/" + "20230205202505_book_comment.csv"​、
    emotion_path = os.getcwd() + "/csv/" + "20230205202627_comment_emotion.csv"

    with open(book_path, 'r', encoding="UTF-8") as book_file, \
            open(comment_path, 'r', encoding="UTF-8") as comment_file, \
            open(emotion_path, 'r', encoding='UTF-8') as emotion_file:
        book_csv = list(csv.reader(book_file))
        comment_csv = list(csv.reader(comment_file))
        emotion_csv = list(csv.reader(emotion_file))

        # 图书CSV中名称索引​
        book_name_index = 0
        # 图书CSV中ID索引​
        book_id_index = 0
        # 评论CSV中内容索引​
        comment_content_index = 0
        # 评论CSV中图书ID索引​
        comment_book_id_index = 0
        # 情感分析CSV中是否积极索引​
        is_positive_index = 0

        for i in range(0, len(book_csv[0])):
            if book_csv[0][i] == "book_name":
                book_name_index = i
            if book_id_index == "book_id":
                book_id_index = i

        for i in range(0, len(comment_csv[0])):
            if comment_csv[0][i] == "comment_content":
                comment_content_index = i
            if comment_csv[0][i] == "book_id":
                comment_book_id_index = i

        for i in range(0, len(emotion_csv[0])):
            if emotion_csv[0][i] == "is_positive":
                is_positive_index = i

        book_file.close()
        comment_file.close()
        emotion_file.close()

    # 绘制柱状图​
    def plot_book_comment_histogram():
        # 绘制流程​
        # 图书名称​
        book_name = []
        # 评论数量​
        comments = []
        # 积极评论数量​
        positives = []
        # 消极评论数量​
        negatives = []
        
        with open(book_path, 'r', encoding="UTF-8") as book_file, \
                open(comment_path, 'r', encoding="UTF-8") as comment_file, \
                open(emotion_path, 'r', encoding='UTF-8') as emotion_file:
            
            book_csv = list(csv.reader(book_file))
            comment_csv = list(csv.reader(comment_file))
            emotion_csv = list(csv.reader(emotion_file))
            
            # 获取评论个数、积极评论数、消极评论数​
            for i in range(1, len(book_csv)):
                book_name.append(book_csv[i][book_name_index])
                comment_num = 0
                positive_num = 0
                negative_num = 0
                for j in range(1, len(comment_csv)):
                    if book_csv[i][book_id_index] == comment_csv[j][comment_book_id_index]:
                        comment_num += 1
                        if emotion_csv[j][is_positive_index] == "1":
                            positive_num += 1
                        else:
                            negative_num += 1
                comments.append(comment_num)
                positives.append(positive_num)
                negatives.append(negative_num)
            
            # 资源释放​
            book_file.close()
            comment_file.close()
            emotion_file.close()
            
        x = np.arange(len(book_name))  # x轴刻度标签位置​
        width = 0.1  # 柱子的宽度​
        # 计算每个柱子在x轴上的位置，保证x轴刻度标签居中​
        plt.bar(x - width, comments, width, label='评论个数')
        plt.bar(x, positives, width, label='正向评论')
        plt.bar(x + width, negatives, width, label='负向评论')
        plt.ylabel('个数')
        plt.title('书籍评论详情')
        # x轴刻度标签位置不进行计算​
        plt.xticks(x, labels=book_name)
        plt.legend()
        plt.show()


    def wordcloud(book_id):
        # 图书评论字符串之和​
        comment = ""
        with open(book_path, 'r', encoding="UTF-8") as book_file, \
                open(comment_path, 'r', encoding="UTF-8") as comment_file:

            book_csv = list(csv.reader(book_file))
            comment_csv = list(csv.reader(comment_file))
            for i in range(1, len(book_csv)):
                if book_csv[i][book_id_index] != book_id:
                    continue
                for j in range(1, len(comment_csv)):
                    if comment_csv[j][comment_book_id_index] == book_id:
                        comment += comment_csv[j][comment_content_index]
            book_file.close()
            comment_file.close()
        if comment == "":
            print({"code": -1, "message": "无对应ID的图书或该图书无评论信息"})
            return
        
    # 中文分词​
    cut_text = " ".join(jieba.lcut(comment))



    # 绘制特定书籍的云图    ​
    def plot_book_comment_wordcloud(book_id):
        # 绘制流程​
        pass



    if __name__ == '__main__':
        plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体​
        plt.rcParams["axes.unicode_minus"] = False  # 该语句解决图像中的“-”负号的乱码问题​
        # 设置画布为长18英寸，高6英寸​
        plt.figure(figsize=(18, 6))


















# 生成可视化图表并提供下载    ​
@app.route("analysis/package", methods=['GET'])

async def get_data_show(request):
    # 拿到request下的filename​
    # 处理相关逻辑​
    

    return json({"code": 1, "msg": "query successfully!", "data": None})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)