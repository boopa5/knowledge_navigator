from google.cloud import documentai
from google.api_core.client_options import ClientOptions
import pathlib
import fitz # PyMuPDF
import json

class Reader:
    _VALID_EXTENSIONS = [".pdf", ".docx", ".png", ".jpg"]

    @staticmethod
    def _get_file_type(path: str):
        return pathlib.Path(path).suffix
    

    @staticmethod
    def _get_text_doc(file_path="./test_files/174aproject.pdf", write=False) -> documentai.Document:
        file_type = Reader._get_file_type(file_path)

        if file_type not in Reader._VALID_EXTENSIONS:
            raise Exception("file type not accepted: must be .pdf or .docx")
        

        project_id = "fluted-ranger-411108"
        location = "us"  # Format is "us" or "eu"

        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")

        client = documentai.DocumentProcessorServiceClient(client_options=opts)
        processor = client.processor_path(project_id, location, "60bd24139d4001d5")

        with open(file_path, "rb") as image:
            image_content = image.read()

        raw_document = documentai.RawDocument(
            content=image_content,
            mime_type="application/pdf",  # Refer to https://cloud.google.com/document-ai/docs/file-types for supported file types
        )

        request = documentai.ProcessRequest(name=processor, raw_document=raw_document)
        result = client.process_document(request=request)
        document = result.document

        if write:
            Reader._write_doc_to("./test_files/output.json", document)

        return document
    

    @staticmethod
    def _draw_boxes(file_path="./test_files/174aproject.pdf"):
        processed = Reader._get_text_doc(file_path)
            
        doc = fitz.open(file_path)

        for (i, page) in enumerate(doc):
            page = doc[i]
            page_w = page.rect.width
            page_h = page.rect.height
            shape = page.new_shape()

            for block in processed.pages[i].paragraphs:
                rect_coords = block.layout.bounding_poly.normalized_vertices
                points = []
                for coords in rect_coords:
                    points.append(fitz.Point(coords.x * page_w, page_h - coords.y * page_h))

                quad = fitz.Quad(points[0], points[3], points[1], points[2])
                shape.draw_quad(quad)

                shape.finish(
                    width=2,  # line width
                )

                shape.commit()

        import os
        scriptdir = os.path.dirname(__file__)
        doc.save(os.path.join(scriptdir, "annotated.pdf"))
            
    
    
    @staticmethod
    def _write_doc_to(path, doc) -> None:
        jsonified = documentai.Document.to_json(doc)
        with open(path, 'w') as out:
            out.write(jsonified)
            print("Wrote to " + path)


if __name__ == "__main__":
    # Reader._get_text(write=True)
    Reader._draw_boxes("./test_files/ec.pdf")