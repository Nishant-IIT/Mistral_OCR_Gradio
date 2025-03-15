import gradio as gr
import os
import base64
import requests
from mistralai import Mistral

api_key = "V7Hh6XjfDJggdJG2ZSPA0KcajDW6jfj0"
client = Mistral(api_key=api_key)

def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    for img_name, base64_str in images_dict.items():
        markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})")
    return markdown_str

def get_combined_markdown(ocr_response) -> tuple:
    markdowns = []
    raw_markdowns = []
    for page in ocr_response.pages:
        image_data = {}
        for img in page.images:
            image_data[img.id] = img.image_base64
        markdowns.append(replace_images_in_markdown(page.markdown, image_data))
        raw_markdowns.append(page.markdown)
    return "\n\n".join(markdowns), "\n\n".join(raw_markdowns)

def get_content_type(url):
    """Fetch the content type of the URL."""
    try:
        response = requests.head(url)
        return response.headers.get('Content-Type')
    except Exception as e:
        return f"Error fetching content type: {e}"

def perform_ocr_file(file, ocr_method="Mistral OCR"):
    if ocr_method == "Mistral OCR":
        if file.name.endswith('.pdf'):
            uploaded_pdf = client.files.upload(
                file={
                    "file_name": file.name,
                    "content": open(file.name, "rb"),
                },
                purpose="ocr"
            )
            signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url.url,
                },
                include_image_base64=True
            )
            client.files.delete(file_id=uploaded_pdf.id)

        elif file.name.endswith(('.png', '.jpg', '.jpeg')):
            base64_image = encode_image(file.name)
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                },
                include_image_base64=True
            )

        combined_markdown, raw_markdown = get_combined_markdown(ocr_response)
        return combined_markdown, raw_markdown

    return "## Method not supported.", "Method not supported."

def perform_ocr_file(file, ocr_method="Mistral OCR"):
    if ocr_method == "Mistral OCR":
        if file.name.endswith('.pdf'):
            uploaded_pdf = client.files.upload(
                file={
                    "file_name": file.name,
                    "content": open(file.name, "rb"),
                },
                purpose="ocr"
            )
            signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url.url,
                },
                include_image_base64=True
            )
            client.files.delete(file_id=uploaded_pdf.id)

        elif file.name.endswith(('.png', '.jpg', '.jpeg')):
            base64_image = encode_image(file.name)
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                },
                include_image_base64=True
            )

        combined_markdown, raw_markdown = get_combined_markdown(ocr_response)
        return combined_markdown, raw_markdown

    return "## Method not supported.", "Method not supported."

def perform_ocr_url(url, ocr_method="Mistral OCR"):
    if ocr_method == "Mistral OCR":
        content_type = get_content_type(url)
        if 'application/pdf' in content_type:
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": url,
                },
                include_image_base64=True
            )

        elif any(image_type in content_type for image_type in ['image/png', 'image/jpeg', 'image/jpg']):
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "image_url",
                    "image_url": url,
                },
                include_image_base64=True
            )
        else:
            return "Unsupported file type. Please provide a URL to a PDF or an image.", ""

        combined_markdown, raw_markdown = get_combined_markdown(ocr_response)
        return combined_markdown, raw_markdown

    return "## Method not supported.", "Method not supported."

with gr.Blocks() as demo:
    gr.Markdown("# Mistral OCR")
    gr.Markdown("Upload a PDF or an image, or provide a URL to extract text and images using Mistral OCR capabilities.\n\nLearn more in the blog post [here](https://mistral.ai/news/mistral-ocr).")

    with gr.Tab("Upload File"):
        file_input = gr.File(label="Upload a PDF or Image")
        ocr_method_file = gr.Dropdown(choices=["Mistral OCR"], label="Select OCR Method", value="Mistral OCR")
        file_output = gr.Markdown(label="Rendered Markdown")
        file_raw_output = gr.Textbox(label="Raw Markdown")
        file_button = gr.Button("Process")

        # example_files = gr.Examples(
        #     examples=[
        #         "receipt.png"
        #     ],
        #     inputs=[file_input]
        # )

        file_button.click(
            fn=perform_ocr_file,
            inputs=[file_input, ocr_method_file],
            outputs=[file_output, file_raw_output]
        )

    with gr.Tab("Enter URL"):
        url_input = gr.Textbox(label="Enter a URL to a PDF or Image")
        ocr_method_url = gr.Dropdown(choices=["Mistral OCR"], label="Select OCR Method", value="Mistral OCR")
        url_output = gr.Markdown(label="Rendered Markdown")
        url_raw_output = gr.Textbox(label="Raw Markdown")
        url_button = gr.Button("Process")

        example_urls = gr.Examples(
            examples=[
                "https://arxiv.org/pdf/2410.07073",
                "https://raw.githubusercontent.com/mistralai/cookbook/refs/heads/main/mistral/ocr/receipt.png"
            ],
            inputs=[url_input]
        )

        url_button.click(
            fn=perform_ocr_url,
            inputs=[url_input, ocr_method_url],
            outputs=[url_output, url_raw_output]
        )

demo.launch(max_threads=1,server_name="0.0.0.0")

