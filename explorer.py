import qdrant_client
from qdrant_client import models
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path
import os
import json
import re
import random
import pickle
import sys
import dotenv

res = dotenv.load_dotenv("./.env")
if res is False:
    print("failed to lado dotenv")
    exit(1)

INCLUDE = [r".*\.py", r".*\.rs"]

client = qdrant_client.QdrantClient(os.environ["QDRANT_LOCATION"])


def include(include: list[str], filepaths: list[str]):
    res = []

    for fp in filepaths:        
        for pattern in include:
            if re.match(pattern, fp):
                res.append(fp)
                break
    return res



def create_counts(files: list[str]) -> dict:
    tfidf = TfidfVectorizer(input="filename")


def fit_by_type(filepaths: list[str]) -> dict:
    """ 
    Fit by file type `.rs`, `.py` etc.
    common context between files in kept

    create one qdrant collection pr filetype or one large collection?
    need to rescale vectors to either largest overall or withinn filetype

    add filetype as metadata?
    """

    res = {}
    filetypes = {}
    max_size = 0
    
    for fp in filepaths:
        p = Path(fp)

        file_name = p.name
        file_type = file_name.split(".")[-1]

        if filetypes.get(file_type) is None:
            filetypes[file_type] = []
        
        filetypes[file_type].append(p)

    
    for ft, fps in filetypes.items():

        print(ft)

        
        tfidf = TfidfVectorizer(input="filename")
        tfidf.fit(fps)

        # print(tfidf.vocabulary_)

        res[ft] = {"files":{}}

        # reverse = {v:k for k,v in tfidf.vocabulary_.items()}

        for fp in fps:
            # res[fp.name] 
            transformed = tfidf.transform([fp]).toarray()[0]
            
            if transformed.size > max_size:
                max_size = transformed.size

            res[ft]["files"][fp.name] = transformed

            # for idx, value  in enumerate(transform[0]):
            #     if value > 0.0:
            #         res[fp.name][reverse[idx]] = value
        
        # res[ft]["max_size"] = max_size

    for ft in res.keys():
        max_size = res[ft]["max_size"]
        for transform in res[ft]["files"].values():
            transform.resize(max_size, refcheck=False)

    res["max_size"] = max_size

    return res
                    

def fit_one_file(filepaths: list[str]) -> list[dict]:
    """
    fit all files individually
    """
    max_size = 0
    res = {}

    for fp in filepaths:
        tfidf = TfidfVectorizer(input="filename")
        tfidf.fit([fp])
        
        transformed = tfidf.transform([fp]).toarray()[0]

        if transformed.size > max_size:
            max_size = transformed.size

        # reverse = {v:k for k,v in tfidf.vocabulary_.items()}

        res[fp.name] = transformed

        # for idx, value in enumerate(res):
        #     if value > 0.0:
        #         res[fp.name][reverse[idx]] = value


    return res



def fit_all_files(filepaths: list[str]) -> list[dict]:
    """
    Fit all files under same context
    """

    res = {"all":{"files":{}}}


    tfidf = TfidfVectorizer(input="filename")

    tfidf.fit(filepaths)

    # reverse = {v:k for k,v in tfidf.vocabulary_.items()}

    for fp in filepaths:
        transformed = tfidf.transform([fp]).toarray()[0]

        res["all"]["files"][fp] = transformed

    res["max_size"] = transformed.size
        
        # for idx, value in enumerate(res):
        #         if value > 0.0:
        #             res[fp.name][reverse[idx]] = value
    
    # save vocabulary for reuse
    tfidf.input = "content"
    
    with open("tfidf.pckl", "wb") as f:
        pickle.dump(tfidf, f)

    return res

def help() -> str:
    return """
usage: explorer.py [COMMAND]

COMMANDs:
"""

def main(argv):

    # print(argv)
    # exit(1)

    

    files = os.listdir(".")
    files = include(INCLUDE, files)

    print(files)

    res = fit_all_files(files)

    root_folder = os.getcwd().split("\\")[-1]

    # if not client.collection_exists(collection_name=root_folder):
    client.recreate_collection(
        collection_name=root_folder,
        vectors_config=models.VectorParams(
            size=res["max_size"],
            distance=models.Distance.COSINE

        )
    )
    
    update_res = client.upsert(
        collection_name=root_folder,
        points=[
            models.PointStruct(
                id=random.randint(0, 100000),
                vector=list(transform),
                payload={"filename": filename}
            ) for filename, transform in res["all"]["files"].items()
        ]
    )

    print(update_res.model_dump_json())

if __name__ == "__main__":
    main(sys.argv)