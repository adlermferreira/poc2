import re
import os
import requests
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET

# path where you want to save
path_csv = os.path.dirname(os.path.abspath(__file__)) + "\\Datasets\\"

if not os.path.exists(path_csv):
    os.makedirs(path_csv)

# deputy variables
deputy_name = "Pedro Chaves"
deputy_party = "PMDB"
csv_name = "PedroChaves"

# paths to HTTP GET
path_getProposition = 'http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterProposicao?tipo={}&numero={}&ano={}'
path_getVoting = 'http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterVotacaoProposicao?tipo={}&numero={}&ano={}'
path_listVotings = 'http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario?ano={}&tipo={}'

def buildXML(response):
    tree_xml = ET.fromstring(response.content)
    return tree_xml
    
def mergeInfoPropositions(xml):
    info_voting = []

    for proposition in xml:
        propos = proposition.find("nomeProposicao")
        info_voting.append(re.split(' |/', propos.text))

    return info_voting

def buildDictRequest(category, path, begin_year, end_year):
    # for each key(propositions' ID) from the dictionary, a request is made
    voting = {}
    for year in range(begin_year, end_year):
        voting[year] = requests.get(path.format(year, category))
    
    return voting

def buildDictXML(voting, begin_year, end_year):
    all_votings = {}
    for year in range(begin_year, end_year):
        xml_voting = buildXML(voting[year])
        all_votings[year] = mergeInfoPropositions(xml_voting)
    
    return all_votings

# needs a stable network connection, and takes some time
def getVotesRequest(all_propos, path_voting, path_propos):
    all_response = {}
    previous = 0
    for key in all_propos:
        all_response[key] = [[], []]
        for propos in all_propos[key]:
            if previous == propos:
                continue
            previous = propos
            # save info about the proposition's voting
            all_response[key][0].append(requests.get(path_voting.format(propos[0],propos[1], propos[2])))
            # save info about the proposition itself, like its summary
            all_response[key][1].append(requests.get(path_propos.format(propos[0],propos[1], propos[2])))
    
    return all_response

def getXML(dict_responses):
    xml = {}
    for key in dict_responses:
        xml[key] = [[], []]
        for voting in dict_responses[key][0]:
            xml[key][0].append(buildXML(voting))
        for proposition in dict_responses[key][1]:
            xml[key][1].append(buildXML(proposition))

    return xml

def buildDataFrame(xml, deputy, party):
    df = pd.DataFrame(columns = ["ID", "Autor", "Partido", "Ementa", "ObjVotacao", "Orientacao", "Voto"])
    id_list, author, party_author, summary = [], [], [], [] 
    objVoting, orient, vote_deputy = [], [], []

    for key in xml:
        for propositions in zip(xml[key][0], xml[key][1]):
            votings = propositions[0].find("Votacoes")
            propos = propositions[1].find("Ementa")
            
            author_propos = propositions[1].find("Autor").text
            party_temp = propositions[1].find("partidoAutor").text
            party_temp = party_temp.strip(" ")
            if party_temp == "\n":
                party_temp = author_propos

            initials = propositions[0].find("Sigla").text
            num = propositions[0].find("Numero").text
            year =propositions[0].find("Ano").text
            
            for voting in votings:
                id_list.append(initials + " " + num + "/" + year)
                summary.append(propos.text)
                
                author.append(author_propos)
                party_author.append(party_temp)

                objVoting.append(voting.attrib["ObjVotacao"])

                votes = voting.find("votos")
                orientations = voting.find("orientacaoBancada")

                for vote in votes:
                    if vote.attrib["Nome"] == deputy:
                        vote_deputy.append(vote.attrib["Voto"].strip())
                
                if len(vote_deputy) < len(id_list):
                    for i in range(len(id_list) - len(vote_deputy)):
                        vote_deputy.append("Nao votou")
                party_oriented = False
                
                try:
                    for orientation in orientations:
                        if orientation.attrib["Sigla"] == party:
                            orient.append(orientation.attrib["orientacao"].strip())
                            party_oriented = True
                            #break
                except TypeError:
                    orient.append("Nada")
                    party_oriented = True
                
                if party_oriented == False:
                    orient.append("Nada")

    df["ID"] = id_list
    df["Autor"] = author
    df["Partido"] = party_author
    df["Ementa"] = summary
    df["ObjVotacao"] = objVoting
    df["Orientacao"] = orient
    df["Voto"] = vote_deputy

    print(df.head())
    return df

def saveCsvDeputy(df, path_csv, name):
    df.to_csv(path_csv + name + ".csv", index=False, encoding="utf-8-sig")

def buildDFDeputy(xml_PEC, xml_PL, deputy, party):
    df_PEC = buildDataFrame(xml_PEC, deputy, party)
    df_PL = buildDataFrame(xml_PL, deputy, party)

    df_all = pd.concat([df_PEC, df_PL])
    return df_all

begin_year = 1999
end_year = 2018

voting_PEC = buildDictRequest("PEC", path_listVotings, begin_year, end_year)
voting_PL = buildDictRequest("PL", path_listVotings, begin_year, end_year)

all_PEC_votings = buildDictXML(voting_PEC, begin_year, end_year)
all_PL_votings = buildDictXML(voting_PL, begin_year, end_year)

# needs a stable network connection, and takes some time
dict_PEC_responses = getVotesRequest(all_PEC_votings, path_getVoting, path_getProposition)
dict_PL_responses = getVotesRequest(all_PL_votings, path_getVoting, path_getProposition)

xml_PEC = getXML(dict_PEC_responses)
xml_PL = getXML(dict_PL_responses)

df = buildDFDeputy(xml_PEC, xml_PL, deputy_name, deputy_party)
saveCsvDeputy(df, path_csv, csv_name)
