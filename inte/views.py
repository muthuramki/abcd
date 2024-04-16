
from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import requests
import base64
import json
from django.http import JsonResponse
from io import BytesIO
 
endpoint = "https://savic-ocr-integration-document-intelligence.cognitiveservices.azure.com/"
key = "7be7b9df5d014fbd94c2d5ce7961925a"
model_id = "Almaya_Choithram_Shankar_Trading_Custom_Model"
 
desired_fields = ['Invoice Number', 'Invoice Date', 'Purchase Order Number', 'VendorName', 'VendorAddress', 'Vendor Tax Id', 'Customer Name', 'Customer Tax Id', 'SubTotal', 'Total Tax', 'Invoice Total', 'Amount', 'Description', 'ProductCode', 'Barcode', 'Quantity', 'Tax', 'TaxRate', 'Unit', 'UnitPrice']
 
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
 
def analyze_layout(content):
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    poller = document_analysis_client.begin_analyze_document(
        model_id=model_id, document=content
    )
    result = poller.result()
    structured_output = extract_fields(result)
    return structured_output
 
def upload_invoice(request):
    if request.method == 'POST' and request.FILES['invoice']:
        invoice_file = request.FILES['invoice']
        invoice_content = invoice_file.read()
        extracted_data = analyze_layout(invoice_content)
        provided_data = {"ID": "1001", "BODY": []}
        for document in extracted_data:
            for row in document.get('Items', []):
                item_row = {
                    "VEN_NAME": document.get('VendorName', ''),
                    "EBELN": document.get('Purchase Order Number', ''),
                    "TXZ01": row.get('Description', ''),
                    "MENGE_PO": row.get('Quantity', ''),
                    "MENGE_GR": row.get('Quantity', ''),
                }
                provided_data['BODY'].append(item_row)
        print(json.dumps(provided_data, indent=4))
        json_data = json.dumps(provided_data)
        sap_url = f"http://savic1909.savictech.com:8000/sap/bc/abap/zmigo_vk/rest/?sap-client=220&req={json_data}"
        username = "SAIP"
        password = "Praneeth@10"
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        response = requests.get(sap_url, headers={'Authorization': 'Basic ' + credentials})
        if response.status_code == 200:
            print("JSON data retrieved successfully from SAP portal!")
            print("Response:", json.dumps(response.json(), indent=4))
        else:
            print("Failed to push JSON data to SAP portal. Status code:", response.status_code)
            print("Error message:", response.text)
        return render(request, 'invoice_data.html', {'extracted_data': extracted_data})
    return render(request, 'upload.html')
 