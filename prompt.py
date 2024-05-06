import sys
import qdrant_client
import groq
import dotenv
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle

dotenv.load_dotenv("./.env")

def main(argv):
    metaprompt = ""

    prompt = argv[1]
    if len(argv) == 3 and argv[2] == "-q":
        with open("./tfidf.pckl", "rb") as f:
            tfidf: TfidfVectorizer = pickle.load(f)

        root_folder = os.getcwd().split("\\")[-1]

        tfidf.input = "content"
        transformed = tfidf.transform([prompt]).toarray()[0]

        qdrant = qdrant_client.QdrantClient(os.environ["QDRANT_LOCATION"])
        
        res = qdrant.search(
            collection_name=root_folder,
            query_vector=transformed,
            limit=3
        )

        if res[0].score > 0.2:
            metaprompt = f"""
help me answer the following question based on the provided context.

the provided context is the most important to the question.

do not pretend like you know the answer, if you don't know, respond with i dont know.

question: 
{prompt}

context: 
this context is provided from the {res[0].payload["filename"]} file,
{open(res[0].payload["filename"]).read()}
"""        
            print(metaprompt)
    # exit(1)

    client = groq.Client()

    res = client.chat.completions.create(
        messages=[
            {
                "role":"system",
                "content": "you are en expert rust programmer that loves to help other programmers"
            },

            {
                "role":"user",
                "content": metaprompt if metaprompt else prompt,
            }
        ],
        model="mixtral-8x7b-32768"
    )

    print(
        res.model, 
        res.usage.total_time, 
        res.usage.prompt_tokens, 
        res.usage.total_tokens, 
        sep=" | "
    )

    print(res.choices[0].message.content)

if __name__ == "__main__":
    main(sys.argv)

