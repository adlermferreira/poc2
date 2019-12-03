import re
import os
import nltk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import collections

nltk.download('stopwords')
nltk.download('rslp')

irrelevant = nltk.corpus.stopwords.words('portuguese')
irrelevant.append("dá")
irrelevant.append("sobre")

# path where ou want to save
path_saveCsv = os.path.dirname(os.path.abspath(__file__)) + "\\Datasets\\"
csv_name = "PedroChavesRadicals"

if not os.path.exists(path_saveCsv):
    os.makedirs(path_saveCsv)

# deputy's dataframe path after get_propositions.py script
path_PedroChaves = "Datasets\\PedroChaves.csv"

########################################################################################
# THE BLOCK BELOW IS TO CREATE THE DATAFRAME THAT 
# WILL BE USED ON THE CLASSIFIER
########################################################################################

def stemming(instancia):
    stemmer = nltk.stem.RSLPStemmer()
    palavras=[]
    for w in instancia:
        palavras.append(stemmer.stem(w))
    return palavras

def fixDF(df):
    new_df = df.drop_duplicates(subset='ID', keep="first").reset_index(drop=True)
    new_df["Partido"] = new_df["Partido"].str.strip(" ")
    return new_df

def concatDataframes(dict_ex, deputy_df):
    df = pd.DataFrame.from_dict(dict_ex, orient='index')
    df.index.name = 'ID'
    df.reset_index(inplace=True)
    
    authors = deputy_df[["ID", "ObjVotacao", "Orientacao", "Voto"]]
    authors_cols = authors.columns.tolist()

    new_df = pd.merge(df, authors, on="ID")
    cols = new_df.columns.tolist()
    for col in range(len(authors_cols) - 1):
        cols = cols[-1:] + cols[: -1]

    new_df = new_df[cols]
    return new_df

def splitSummaries(df):
    id_summaries, summaries = df["ID"], df["Ementa"]
    dict_summary = collections.OrderedDict()
    radicals_summary = collections.OrderedDict()
    for row in zip(id_summaries, summaries):
        summary_sp = re.sub('[()\\-".,:_;ª/º°§[0-9]', '', row[1])
        summary_sp = summary_sp.split()
        summaries_list = []
        for index, words in enumerate(summary_sp):
            if words in irrelevant or len(words) <= 2:
                continue
            summaries_list.append(summary_sp[index])

        dict_summary[row[0]] = summaries_list
        radicals_summary[row[0]] = stemming(summaries_list)
    
    return dict_summary, radicals_summary

def mergeWords(summary):
    words = collections.OrderedDict()
    for key in summary:
        for values in summary[key]:
            words[values] = None
    return words

def createDataframe(votes, dict_summaries, words):
    matrix = pd.DataFrame(0, index=dict_summaries.keys(), columns=words.keys())
    matrix.index.name = "ID"

    for key in dict_summaries:
        for value in dict_summaries[key]:
            for col in matrix.columns:
                if value == col:
                    matrix.loc[key][col] = 1
    
    new_df = pd.merge(matrix, votes, left_index=True, right_on="ID")
    #print(df_full_words["Voto"].value_counts())

    new_df["Voto"].replace(["-", "Obstrução", "Abstenção", "Nao votou"], "Não", inplace=True)
    new_df["Voto"].replace(["Sim", "Não"], [1, 0], inplace=True)
    return new_df

def saveDataframe(df, path, name):
    df.to_csv(path + name + ".csv", index=False, encoding="utf-8-sig")

########################################################################################
# BELOW HERE THE PURPOSE IS TO GENERATE GRAPHS ABOUT 
# THE FREQUENCY OF WORDS ACCORDING TO THE PARTIES
########################################################################################

def countWords(df, cols_list, titulo):
    values = []
    values_labels = []
    index = [1,2,3,4,5]
    for i in cols_list:
        values.append(df.iloc[:, i].value_counts()[1])
    for i in cols_list:
        values_labels.append(df.columns[i])
    plt.bar(index, values, color='tab:red', alpha = 0.9)
    plt.xticks(index, values_labels, fontsize=10)
    plt.title(titulo)

def createAnotherDataframe(df, dict_summaries):
    summaries_df = pd.DataFrame.from_dict(dict_summaries, orient='index')
    summaries_df.index.name = "ID"
    new_df = pd.merge(df, summaries_df, left_on="ID", right_index=True)
    return new_df

def getPartyFrequency(df):
    frequency = {}
    ignored_cols = ["ID", "Autor", "Ementa", "Voto",  "ObjVotacao", "Orientacao"]
    for party in df.groupby("Partido").groups.keys():
        frequency_party = countFrequency(df.drop(ignored_cols, axis=1), party)
        frequency[party] = frequency_party
    
    return frequency

def countFrequency(df, party):
    dict_power = {}
    
    for row in df.itertuples():
        if row.Partido == party:
            for word in row:
                if word == row.Partido or word == row.Index:
                    continue
                if word in dict_power.keys():
                    dict_power[word] += 1
                else:
                    dict_power[word] = 1
    
    del dict_power[None]
    sorted_x = sorted(dict_power.items(), key=lambda kv: kv[1], reverse=True)
    return sorted_x

def plotBar(frequency):
    # this is for plotting purpose
    index = [1,2,3,4,5]
    my_colors = 'tab:blue'
    for key in frequency:
        count = 1
        temp_list = []
        temp_labels = []

        for value in frequency[key]:
            temp_list.append(value[1])
            temp_labels.append(value[0])
            count += 1
            if count > 6:
                break
        index = np.arange(count-1)
        count = 1
        for value in frequency[key]:    
            plt.bar(index, temp_list, color=my_colors, alpha = 0.5)
            plt.xticks(index, temp_labels, fontsize=10)
            count += 1
            if count >= 5:
                break
        plt.xlabel(key)
        plt.show()

pedro = pd.read_csv(path_PedroChaves)
cleaner_pedro = fixDF(pedro)

summary, rad_summary = splitSummaries(cleaner_pedro)

words = mergeWords(summary)
rad_words = mergeWords(rad_summary)

df_full_words = createDataframe(cleaner_pedro[["ID","Partido", "Voto"]], summary, words)
df_rad_words = createDataframe(cleaner_pedro[["ID","Partido", "Voto"]], rad_summary, rad_words)

saveDataframe(df_rad_words, path_saveCsv, csv_name)

# for some reason, there is a difference of 1 between the 
# indexes on python spyder and the google colab notebook
# the columns on google colab are [201, 528, 334, 987, 235]
countWords(df_rad_words, [200, 527, 333, 986, 234], 'Nº de vezes que as palavras mais relevantes aparecem')

new_df = createAnotherDataframe(cleaner_pedro, summary)

frequency = getPartyFrequency(new_df)
plotBar(frequency)







