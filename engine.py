import spacy
import re
import torch
from sentence_transformers import SentenceTransformer, util
from reader import Reader
from pprint import pprint
import fitz # PyMuPDF
import os


class Engine:

    def __init__(self, text_doc=None, embedder="msmarco-MiniLM-L-6-v3", file_path=None):
        if text_doc == None:
            self.initialized = False
            return
        self.text_doc = text_doc
        segmented = self._segment_text(text_doc.text)

        self.search_index = self._build_index(segmented, text_doc)
        self.segmented = self._clean_segmented(segmented)
        self.embedder = SentenceTransformer(embedder)
        self._create_windowed_batch()
        self._embed_batches()
        self.initialized = True
        self.file_path = file_path



    def load(self, file_path):
        text_doc = Reader._get_text_doc(file_path)
        self.__init__(text_doc=text_doc, file_path=file_path)
    
    def query(self, query):
        query_embed = self._embed(query)
        cos_scores = util.cos_sim(query_embed, self.corpus_embeddings)

        top_res = torch.topk(cos_scores, 3)
        for score, idx in zip(top_res[0].reshape(-1), top_res[1].reshape(-1)):
            print(self.batches[idx]["batch"], "(Score: {:.4f})".format(score))

        return [self.batches[idx]["start_block"][0] for score, idx in zip(top_res[0].reshape(-1), top_res[1].reshape(-1))], [self.batches[idx] for score, idx in zip(top_res[0].reshape(-1), top_res[1].reshape(-1))]


    def label_top_boxes(self, top_res, input_path, output_path):
        all_points = []
        doc = fitz.open(input_path)

        for res in top_res:
            start_block = res["start_block"]
            end_block = res["end_block"]
            

            # print(start_block)
            # print(end_block)

            for (i, page) in enumerate(doc):
                page = doc[i]
                page_w = page.rect.width
                page_h = page.rect.height
                shape = page.new_shape()

                if i + 1 < start_block[0]: continue
                if i + 1 > end_block[0]: break

                for (j, block) in enumerate(self.text_doc.pages[i].paragraphs):
                    
                    if i + 1 == start_block[0] and j < start_block[1]:
                        continue
                    if i + 1 == end_block[0] and j > end_block[1]:
                        continue
                    # print(i + 1, j)
                    rect_coords = block.layout.bounding_poly.normalized_vertices
                    points = []
                    for coords in rect_coords:
                        points.append(fitz.Point(coords.x * page_w, page_h - coords.y * page_h))
                        all_points.append(points)
                    # print(points)
                    quad = fitz.Quad(points[0], points[3], points[1], points[2])
                    shape.draw_quad(quad)
                    shape.finish(
                        width=1,  # line width
                    )

                    shape.commit()


            # for (i, page) in enumerate(doc):
            #     page = doc[i]
            #     page_w = page.rect.width
            #     page_h = page.rect.height
            #     shape = page.new_shape()

            #     for block in self.text_doc.pages[i].paragraphs:
            #         rect_coords = block.layout.bounding_poly.normalized_vertices
            #         points = []
            #         for coords in rect_coords:
            #             points.append(fitz.Point(coords.x * page_w, page_h - coords.y * page_h))

            #         quad = fitz.Quad(points[0], points[3], points[1], points[2])
            #         shape.draw_quad(quad)

            #         shape.finish(
            #             width=2,  # line width
            #         )

            #         shape.commit()

        scriptdir = os.path.dirname(__file__)
        doc.save(os.path.join(scriptdir, output_path))


    def _embed(self, text):
        return self.embedder.encode(text, convert_to_tensor=True)


    def _embed_batches(self):
        corpus = [b["batch"] for b in self.batches]

        corpus_embeddings = self.embedder.encode(corpus, convert_to_tensor=True)
        self.corpus_embeddings = corpus_embeddings
        

    def _create_windowed_batch(self, window_size=4, overlap=2):
        
        slide_inc = window_size - overlap
        window_ptr = 0
        batches = []
        while window_ptr < len(self.segmented):
            right_ptr = window_ptr + window_size
            if right_ptr > len(self.segmented):
                right_ptr = len(self.segmented)
            batches.append({"batch": ' '.join(self.segmented[window_ptr:right_ptr]), 
                            "start_block": self.search_index[window_ptr]["start_block"],
                            "end_block": self.search_index[right_ptr - 1]["end_block"]})
            window_ptr += slide_inc
        
        self.batches = batches

    def _segment_text(self, text):
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        segmented = [s.text for s in doc.sents]

        return segmented
    

    def _build_index(self, segmented, text_doc):
        assert len(segmented) > 0

        # {page, block id, block start, block end}
        block_indices = []
        for (i, page) in enumerate(text_doc.pages):
            for (j, block) in enumerate(page.paragraphs):
                text_segments = block.layout.text_anchor.text_segments
                block_indices.append({"page": i + 1, "pos": j, "start": text_segments[0].start_index, "end": text_segments[0].end_index})

        seg_pointer = 0
        prev_seg_pointer = 0
        block_pointer = block_indices[0]["start"]
        prev_block_pointer = 0

        block_counter = 0
        prev_block_counter = 0
        res = []

        for segment in segmented:
            prev_seg_pointer = seg_pointer
            prev_block_counter = block_counter

            seg_pointer += len(segment)
            while block_pointer < seg_pointer:
                block_counter += 1
                prev_block_pointer = block_pointer
                block_pointer = block_indices[block_counter]["end"]

            # perfectly aligned
            start_block_counter = prev_block_counter
            if prev_seg_pointer == prev_block_pointer:
                start_block_counter += 1
            # for each segment, store page and position in block list to find original block start and end indices
            res.append({
                "start_block": [block_indices[start_block_counter]["page"], block_indices[start_block_counter]["pos"]],
                "end_block": [block_indices[block_counter]["page"], block_indices[block_counter]["pos"]]
                })

        return res
    

    @staticmethod
    def _clean_segmented(segmented):
        return [re.sub('[^A-Za-z0-9 ]+', ' ', s) for s in segmented]
