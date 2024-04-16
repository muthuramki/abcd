from django.shortcuts import render
from django.http import HttpResponse
import os
import json
import base64
import asyncio
from aiohttp import ClientSession
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

endpoint = "https://savic-ocr-integration-document-intelligence.cognitiveservices.azure.com/"
key = "7be7b9df5d014fbd94c2d5ce7961925a"
model_id = "Almaya_Choithram_Shankar_Trading_Custom_Model"

desired_fields = ['Invoice Number', 'Invoice Date', 'Purchase Order Number', 'VendorName', 'VendorAddress', 'Vendor Tax Id', 'Customer Name', 'Customer Tax Id', 'SubTotal', 'Total Tax', 'Invoice Total', 'Amount', 'Description', 'ProductCode', 'Barcode', 'Quantity', 'Tax', 'TaxRate', 'Unit', 'UnitPrice']

def extract_fields(result):
    extracted_data = []

    for document in result.documents:
        fields_data = {}
        fields_data['Invoice Number'] = document.invoice_number.value if document.invoice_number else None
        fields_data['Invoice Date'] = document.invoice_date.value if document.invoice_date else None
        fields_data['Purchase Order Number'] = document.purchase_order_number.value if document.purchase_order_number else None
        fields_data['VendorName'] = document.vendor_name.value if document.vendor_name else None
        fields_data['VendorAddress'] = document.vendor_address.value if document.vendor_address else None
        fields_data['Vendor Tax Id'] = document.vendor_tax_id.value if document.vendor_tax_id else None
        fields_data['Customer Name'] = document.customer_name.value if document.customer_name else None
        fields_data['Customer Tax Id'] = document.customer_tax_id.value if document.customer_tax_id else None
        fields_data['SubTotal'] = document.sub_total.value if document.sub_total else None
        fields_data['Total Tax'] = document.total_tax.value if document.total_tax else None
        fields_data['Invoice Total'] = document.invoice_total.value if document.invoice_total else None
        fields_data['Amount'] = document.amount.value if document.amount else None
        fields_data['Description'] = document.description.value if document.description else None
        fields_data['ProductCode'] = document.product_code.value if document.product_code else None
        fields_data['Barcode'] = document.barcode.value if document.barcode else None
        fields_data['Quantity'] = document.quantity.value if document.quantity else None
        fields_data['Tax'] = document.tax.value if document.tax else None
        fields_data['TaxRate'] = document.tax_rate.value if document.tax_rate else None
        fields_data['Unit'] = document.unit.value if document.unit else None
        fields_data['UnitPrice'] = document.unit_price.value if document.unit_price else None

        extracted_data.append(fields_data)

    return extracted_data

async def analyze_layout_async(file_path, session):
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    with open(file_path, "rb") as file:
        content = file.read()

    poller = document_analysis_client.begin_analyze_document(
        model_id=model_id, document=content
    )
    result = await poller.result()

    structured_output = extract_fields(result)

    return structured_output

async def upload_invoice_async(request):
    if request.method == 'POST' and request.FILES['invoice']:
        invoice_file = request.FILES['invoice']
        temp_file_path = 'temp_invoice.pdf'
        
        with open(temp_file_path, 'wb') as f:
            for chunk in invoice_file.chunks():
                f.write(chunk)

        async with ClientSession() as session:
            extracted_data = await analyze_layout_async(temp_file_path, session)

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        else:
            print(f"File {temp_file_path} does not exist.")

        provided_data = {
            "ID": "1001",
            "BODY": []
        }

        for document in extracted_data:
            for row in document.get('Items', []):
                item_row = {
                    "VEN_NAME": document.get('VendorName', ''),
                    "EBELN": document.get('Purchase Order Number', ''),
                    "TXZ01": row.get('Description', ''),
                    "MENGE_PO": row.get('Quantity', ''),
                    "MENGE_GR": row.get('Quantity', '')  # Assuming both fields are the same
                }
                provided_data['BODY'].append(item_row)

        print(json.dumps(provided_data, indent=4))

        json_data = json.dumps(provided_data)

        sap_url = f"http://savic1909.savictech.com:8000/sap/bc/abap/zmigo_vk/rest/?sap-client=220&req={json_data}"

        username = "SAIP"
        password = "Praneeth@10"

        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

        async with session.get(sap_url, headers={'Authorization': 'Basic ' + credentials}) as response:
            if response.status == 200:
                print("JSON data retrieved successfully from SAP portal!")
                print("Response:", json.dumps(await response.json(), indent=4))
            else:
                print("Failed to push JSON data to SAP portal. Status code:", response.status)
                print("Error message:", await response.text())

        return render(request, 'invoice_data.html', {'extracted_data': extracted_data})

    return render(request, 'upload.html')
