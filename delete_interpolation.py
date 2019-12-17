import math

import sympy

from common import *

'''
Inputs: 
vocab_num: 词汇数量
word_num: 在给定历史条件下单词出现的次数
hist_num: 历史条件出现的次数

Returns:
new_p: 加值平滑后的词汇条件概率
'''


def add_smoothing(vocab_num, word_num, hist_num):
    new_p = (word_num + 1) / (vocab_num + hist_num)
    return new_p


'''
要点：具有相同历史的gram对应的参数λ相同，要先计算相同历史的gram出现的次数，然后计算概率乘积，对参数求偏导得到极值点
Inputs: 
gram_num: gram的数量
p_list: 不同gram的值列表 shape = (gram_num, probability_num)

Returns:
p_2gram_matrix: 插值平滑一轮后的gram概率矩阵
'''


def delete_interpolation(gram_num, p_list, word2id):
    p_1gram_matrix = p_list[0]
    if gram_num == 2:
        p_2gram_matrix = p_list[1]
        '''
    if gram_num == 3:
        p_2gram_matrix = p_list[1]
        p_3gram_matrix = p_list[2]
        '''

    with open('rest.txt', 'r') as f:
        gram_list = generate_gram_list(f)
        corpus_p = cal_corpus_p(f)
        vocab_num = get_vocab_num(f)
    old_cross_entropy = -1
    new_cross_entropy = cross_entropy(vocab_num, corpus_p)

    while (old_cross_entropy != new_cross_entropy):
        old_cross_entropy = new_cross_entropy
        p_2gram_matrix = round(gram_list, p_1gram_matrix, p_2gram_matrix)
        new_cross_entropy = cross_entropy(corpus_p, p_2gram_matrix)

    return p_2gram_matrix


'''
计算得到plist
plist[0]是unigram的概率
plist[2]是bigram的概率
概率形式自己定义,只要和get_p_with_gram一致即可
'''


def get_p_1gram_matrix(f):
    flist = f_original_shape(f)
    counter = generate_counter_list(flist)
    unigram = get_unigram(counter)

    return unigram


def get_p_2gram_matrix(f):
    flist = f_original_shape('train_LM.txt')
    counter = generate_counter_list(flist)
    word2id = get_word2id(counter)
    bigram = get_bigram(word2id, flist)

    return bigram


'''
一轮参数更新
Inputs:
gram_list, shape = (2 * gram_tuple_num)
gram_list[n][0]是gram内容
gram_list[n][1]是出现次数
p_1gram_matrix: unigram概率矩阵
p_2gram_matrix: bigram概率矩阵

Returns:
p_2gram_matrix: 更新的bigram概率矩阵
'''


def round(gram_list, p_1gram_matrix, p_2gram_matrix, word2id):
    p_case = {}

    for i in range(len(gram_list)):
        word1 = gram_list[i][0]
        word2 = gram_list[i][1]
        gram_count = gram_list[i][2]
        '''
        word = gram_split[2]
        history2 = ' '.join(gram_split[0], gram_split[1])
        history1 = gram_split[1]
        '''
        word = word2
        history = word1
        if history not in p_case:
            p_case[history] = 1

        x = sympy.symbols("x")
        p_1gram = get_p_with_unigram(word, p_1gram_matrix, word2id)
        p_2gram = get_p_with_bigram(word1, word2, p_2gram_matrix, word2id)
        p_new = x * p_1gram + (1 - x) * p_2gram
        p_case[history] = p_case[history] * pow(p_new, gram_count)
        # p_3gram = get_p()

    for history in p_case:
        x_result = 0
        p_case_t = p_case[history].subs(x, x_result)
        difpx = sympy.diff(p_case[history], x)
        t = sympy.solve(difpx, x)
        for x_candidate in t:
            if 0 < x_candidate < 1 and p_case[history].subs(x, x_candidate) < p_case_t:
                p_case_t = p_case[history].subs(x, x_candidate)
                x_result = x_candidate
        p_2gram_matrix = update_gram_matrix_by_history(x_result, history, p_2gram_matrix, p_1gram_matrix)

    return p_2gram_matrix


'''
该函数计算数据集的bigram概率
Inputs:
f: 数据集文件

Returns:
data_p: 数据集的概率
'''


def cal_corpus_p(f):
    data_p = 1.00
    flist = f_original_shape(f)
    counter = generate_counter_list(flist)
    word2id = get_word2id(counter)
    unigram = get_unigram(counter)
    bigram = get_bigram(word2id, flist)
    bigram2 = get_bigram_times(word2id, flist)
    for element1, element2 in zip(bigram.flat, bigram2.flat):
        element = element1 ** element2
        data_p = element * data_p

    return data_p


'''
该函数从数据集中返回词汇数目
Inputs:
f: 数据集文件

Returns:
vocab_num: 词汇数目
'''


def get_vocab_num(f):
    f_list = f_original_shape(f)
    list = generate_counter_list(f_list)
    vocab_num = len(list)

    return vocab_num


'''
该函数以插值参数x更新gram概率矩阵
Inputs:
x: 插值参数
history: gram历史
p_matrix: gram概率矩阵

Returns:
updated_gram_matrix: 更新过的gram概率矩阵
'''


def update_gram_matrix_by_history(x, history, p_2gram_matrix, p_1gram_matrix):
    p_2gram_matrix[history] = x * p_1gram_matrix + (1 - x) * p_2gram_matrix[history]

    return p_2gram_matrix


'''
输入 i  ,得到p(i )
该函数从gram矩阵中返回指定gram的概率
Inputs:
gram: gram的内容
gram_matrix: gram概率矩阵

Returns:
p: gram的概率  # []
'''


def get_p_with_unigram(word, unigram, word2id):
    p = unigram[word2id[word]]

    return p


'''
输入 i ,be ,得到p(i ,be)
该函数从gram矩阵中返回指定gram的概率
Inputs:
gram: gram的内容
gram_matrix: gram概率矩阵

Returns:
p: gram的概率  # []
'''


def get_p_with_bigram(word1, word2, bigram, word2id):
    id1 = word2id[word1]
    id2 = word2id[word2]
    p = bigram[id1, id2]

    return p


'''
input:f 语料文件
Returns:
gram_list[n][0]是w1
gram_list[n][1]是w2
gram_list[n][2]是出现次数
'''


def generate_gram_list(f):
    flist = f_original_shape(f)
    counter = generate_counter_list(flist)
    word2id = get_word2id(counter)
    id2word = get_id2word(word2id)
    unigram = get_unigram(counter)
    bigram = get_bigram(word2id, flist)
    lec = len(word2id)
    gram_list = [[0 for col in range(2)] for row in range(lec * lec)]
    [rows, cols] = bigram.shape
    item = 0
    for i in range(rows):
        for j in range(cols):
            gram_list[item][0] = id2word[i]  # history
            gram_list[item][1] = id2word[j]  # word
            gram_list[item][2] = bigram[i, j]
            item = item + 1
    return gram_list


'''
Inputs:
vocab_num: 词汇数量
corpus_p: 整个测试集的概率

Returns: 交叉熵
'''


def cross_entropy(vocab_num, corpus_p):
    cross_entropy = -(1 / vocab_num) * math.log2(corpus_p)
    return cross_entropy


'''
Inputs:
cross_entropy: 模型交叉熵

Returns
perplexity: 模型困惑度
'''


def perplexity(cross_entropy):
    perplexity = 2 ** cross_entropy
    return perplexity


if __name__ == "__main__":
    delete_interpolation(0, 0)