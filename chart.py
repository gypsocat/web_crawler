import os
import matplotlib.pyplot as plt
import numpy as np
import jieba
from wordcloud import WordCloud
import csv

# 数据处理​

info_path = os.getcwd() + "/csv/" + "20230614125309_movie_info.csv"
comment_path = os.getcwd() + "/csv/" + "20230614125309_movie_comment.csv"
emotion_path = os.getcwd() + "/csv/" + "20230614125500_comment_emotion.csv"

with open(info_path, 'r', encoding="UTF-8") as info_file, \
        open(comment_path, 'r', encoding="UTF-8") as comment_file, \
        open(emotion_path, 'r', encoding='UTF-8') as emotion_file:
    info_csv = list(csv.reader(info_file))
    comment_csv = list(csv.reader(comment_file))
    emotion_csv = list(csv.reader(emotion_file))

    # 图书CSV中名称索引​
    movie_name_index = 1
    # 图书CSV中ID索引​
    movie_id_index = 0
    # 评论CSV中内容索引​
    comment_content_index = 4
    # 评论CSV中图书ID索引​
    comment_movie_id_index = 0
    # 情感分析CSV中是否积极索引​
    is_positive_index = 2

    for i in range(0, len(info_csv[0])):
        if info_csv[0][i] == "movie_name":
            movie_name_index = i
        if movie_id_index == "movie_id":
            movie_id_index = i

    for i in range(0, len(comment_csv[0])):
        if comment_csv[0][i] == "comment_content":
            comment_content_index = i
        if comment_csv[0][i] == "movie_id":
            comment_movie_id_index = i

    for i in range(0, len(emotion_csv[0])):
        if emotion_csv[0][i] == "is_positive":
            is_positive_index = i

    info_file.close()
    comment_file.close()
    emotion_file.close()

# 绘制柱状图​
def plot_movie_comment_histogram():
    # 绘制流程​

    # 图书名称​
    movie_name = []
    # 评论数量​
    comments = []
    # 积极评论数量​
    positives = []
    # 消极评论数量​
    negatives = []

    with open(info_path, 'r', encoding="UTF-8") as info_file, \
            open(comment_path, 'r', encoding="UTF-8") as comment_file, \
            open(emotion_path, 'r', encoding='UTF-8') as emotion_file:
        
        info_csv = list(csv.reader(info_file))
        comment_csv = list(csv.reader(comment_file))
        emotion_csv = list(csv.reader(emotion_file))

        
        # 获取评论个数、积极评论数、消极评论数​
        for i in range(1, len(info_csv)):
            movie_name.append(info_csv[i][movie_name_index])
            comment_num = 0
            positive_num = 0
            negative_num = 0
            for j in range(1, len(comment_csv)):
                if info_csv[i][movie_id_index] == comment_csv[j][comment_movie_id_index]:
                    comment_num += 1
                    if emotion_csv[j][is_positive_index] == "1":
                        positive_num += 1
                    else:
                        negative_num += 1
            comments.append(comment_num)
            positives.append(positive_num)
            negatives.append(negative_num)
        
        # 资源释放​
        info_file.close()
        comment_file.close()
        emotion_file.close()
        
    plt.clf()
    x = np.arange(len(movie_name))  # x轴刻度标签位置​
    width = 0.1  # 柱子的宽度​
    # 计算每个柱子在x轴上的位置，保证x轴刻度标签居中​
    plt.bar(x - width, comments, width, label='评论个数')
    plt.bar(x, positives, width, label='正向评论')
    plt.bar(x + width, negatives, width, label='负向评论')
    plt.ylabel('个数')
    plt.title('书籍评论详情')
    # x轴刻度标签位置不进行计算​
    plt.xticks(x, labels=movie_name)
    plt.legend()
    #plt.show()
    plt.savefig("./analysis/柱状图.jpg")
    plt.clf()

#绘制词云
def plot_movie_comment_wordcloud(movie_id):
    # 图书评论字符串之和​
    comment = ""
    with open(info_path, 'r', encoding="UTF-8") as info_file, \
            open(comment_path, 'r', encoding="UTF-8") as comment_file:

        info_csv = list(csv.reader(info_file))
        comment_csv = list(csv.reader(comment_file))
        # for i in range(1, len(info_csv)):
        #     if info_csv[i][movie_id_index] != movie_id:
        #         continue
        for j in range(1, len(comment_csv)):
            if comment_csv[j][comment_movie_id_index] == movie_id:
                comment += comment_csv[j][comment_content_index]
        info_file.close()
        comment_file.close()
    if comment == "":
        print({"code": -1, "message": "无对应ID的图书或该图书无评论信息"})
        return
    
    # 中文分词​
    cut_text = " ".join(jieba.lcut(comment))
    with open('userless', 'r', encoding='utf-8') as f:
        stopWords = f.read()
        stopWords = ['\n', '', ' '] + stopWords.split()  # 前后列表拼接​
    
    mycloudword = WordCloud(width=400, height=300, scale=1, margin=2,font_path="./SimHei.ttf",
                            background_color='white', max_words=200,
                            random_state=100,stopwords=stopWords).generate(cut_text)

    plt.clf()
    plt.imshow(mycloudword)
    plt.axis("off")   # 关闭坐标轴，必须​
    #plt.show()
    plt.savefig("./analysis/"+movie_id+"词云.jpg")
    plt.clf()



if __name__ == '__main__':
    plt.rcParams["font.sans-serif"] = ["SimHei"]  # 设置字体​
    plt.rcParams["axes.unicode_minus"] = False  # 该语句解决图像中的“-”负号的乱码问题​
    # 设置画布为长18英寸，高6英寸​
    plt.figure(figsize=(18, 6))
    plot_movie_comment_histogram()
    plot_movie_comment_wordcloud("1292052")