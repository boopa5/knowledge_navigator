from sentence_transformers import SentenceTransformer, util
from pypdf import PdfReader
import torch
from engine import Engine
from reader import Reader
from pprint import pprint


test_file_path = "./static/uploads/Physics_6AL_Math_Lab.pdf"

# text_doc = Reader._get_text_doc(test_file_path)
Reader._draw_boxes(test_file_path)

# engine = Engine(text_doc)

# query = "Shortest path"
# engine.query(query)




# Corpus with example sentences
# corpus = ['A man is eating food.',
#           'A man is eating a piece of bread.',
#           'The girl is carrying a baby.',
#           'A man is riding a horse.',
#           'A woman is playing violin.',
#           'Two men pushed carts through the woods.',
#           'A man is riding a white horse on an enclosed ground.',
#           'A monkey is playing drums.',
#           'A cheetah is running behind its prey.'
#           ]

# corpus = ["akdakdj adjakdj djdj ajdjadfkaj as adjsf df d s a sdjfaj adjfjd fdaf ."] * 200
# corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True)

# Query sentences:
# queries = ['A man is eating pasta.', 'Someone in a gorilla costume is playing a set of drums.', 'A cheetah chases prey on across a field.']


# # Find the closest 5 sentences of the corpus for each query sentence based on cosine similarity
# top_k = min(5, len(corpus))
# for query in queries:
#     query_embedding = embedder.encode(query, convert_to_tensor=True)

#     # We use cosine-similarity and torch.topk to find the highest 5 scores
#     cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
#     top_results = torch.topk(cos_scores, k=top_k)

#     print("\n\n======================\n\n")
#     print("Query:", query)
#     print("\nTop 5 most similar sentences in corpus:")

#     for score, idx in zip(top_results[0], top_results[1]):
#         print(corpus[idx], "(Score: {:.4f})".format(score))
