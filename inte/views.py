from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import pandas as pd
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import requests
import base64
import json

# Azure Form Recognizer credentials and model ID
endpoint = "https://savic-ocr-integration-document-intelligence.cognitiveservices.azure.com/"
key = "7be7b9df5d014fbd94c2d5ce7961925a"
model_id = "Almaya_Choithram_Shankar_Trading_Custom_Model"

# Desired fields to extract from the documents
desired_fields = ['Invoice Number', 'Invoice Date', 'Purchase Order Number', 'VendorName', 'VendorAddress', 
                  'Vendor Tax Id', 'Customer Name', 'Customer Tax Id', 'SubTotal', 'Total Tax', 'Invoice Total', 
                  'Amount', 'Description', 'ProductCode', 'Barcode', 'Quantity', 'Tax', 'TaxRate', 'Unit', 'UnitPrice']

def extract_fields(result):
    data = []

    for idx, document in enumerate(result.documents):
        doc_data = flatten_document_fields(document.fields)
        data.append(doc_data)

    return data

def flatten_document_fields(fields):
    flattened_fields = {}

    for name, field in fields.items():
        field_value = field.value if field.value else field.content

        if name == 'Items' and field.value_type == "list":
            items_data = []
            for item in field.value:
                item_fields = flatten_document_fields(item.value)
                items_data.append(item_fields)
            flattened_fields[name] = items_data
        elif field.value_type == "dictionary":
            nested_flattened_fields = flatten_document_fields(field.value)
            flattened_fields.update(nested_flattened_fields)
        elif name in desired_fields:
            flattened_fields[name] = field_value

    return flattened_fields

def analyze_layout(file_content):
    # Initialize the Form Recognizer client
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    # Make sure your document's type is included in the list of document types the custom model can analyze
    poller = document_analysis_client.begin_analyze_document(
        model_id=model_id, document=file_content
    )
    result = poller.result()

    structured_output = extract_fields(result)

    return structured_output

def upload_invoice(request):
    if request.method == 'POST' and request.FILES.get('invoice'):
        invoice_file = request.FILES['invoice']

        # Read the content of the uploaded file
        file_content = invoice_file.read()

        # Analyze the layout and extract fields
        extracted_data = analyze_layout(file_content)

        # Render a template with the extracted data
        return render(request, 'invoice_data.html', {'extracted_data': extracted_data})

    return render(request, 'upload.html')

def update_data(request):
    if request.method == 'POST':
        # Get the edited data from the request body
        edited_data = json.loads(request.body)
        
        # Print the updated JSON data to the terminal
        print("Updated JSON data:", edited_data)
        
        # Respond with a success message
        return JsonResponse({'message': 'Updated JSON data received successfully'}, status=200)
    else:
        # Respond with an error message if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'}, status=405)
