* Assets folder contains  css, image, java script files. In assets folder [style.css](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/assets/css/style.css) is used for css design for home.html, dashboard.html.
Basically its a part of bootstrap template that I have been using.

* In the image folder it is  mainly for home page favicon and template design content

* Ohter files are additinally there which are integral part of bootstrap design

* **[sample_collection_script.js](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/sample_collection_script.js):**  This javascript is linked to the sample_collectiion.html template file. Using javascript it will throw directly into the Sample collection section in the form submission. Same logic is applied to other javascript files also eg.: [library_preparation_script.js](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/library_preparation_script.js) ,[DNA_extraction_script.js](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/DNA_extraction.js) ,[taxonomy_function_script.js](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/taxonomy_function_script.js)

* **Ajax javascript files:** There are five segments in the data submission  porcess (Barcode,Sample_collection,Dna_extraction,library_prep,taxonomy_functional upload). For each segment, an individual ajax javascript is allocated for sending data in the flask end in a batch form.
   
    1.[form1.js](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/form1.js): This javascript will send data for barcode
 
    2.[form2.js](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/form2.js):This javascript will send data from sample collection

    3.[form3.js](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/form3.js): This javascript will send data for DNA Extraction

    4.[form4.js](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/form4.js):This javascript will send data for Library preparation

    5.[upload.js](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/upload.js):This javascript will send uploaded zip folder containing both post function analysis and post taxonomic analysis files.
* **[style.css](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/static/style.css):** This is for  designing of multi_step_form.html. Using this style sheet (css), form integrity is made as multi-step-data-validation and all other form flexibility is maintained.
