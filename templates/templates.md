# File description:
* **[home.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/home.html):** This is the initial page after starting the API

* **[login.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/login.html):** User login page for registered account, page field contains username and password. Password is encrypted. ***page route(url) is "/login"***.

* **[register.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/register.html):** This page contains all field details Username, email Id, password ,confirm password for a new user account.***page route  (url) is **"/register"**.

* **[dashboard.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/dashboard.html):** After successfully loged in, user account will be directed to this page.***page route  (url) is **"/dashboard"**.

***if user is not signed in, one cannot access any of these pages. So sign in is mandatory***

* **[multi_step_form.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/multi_step_form.html):** This page is for data-submission-process. Its a multi step form. Total contains five section of data submission.***page route  (url) is **"/index"**.

* **[datafetch.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/datafetch.html):** This page contains status table from the data-submission-process. Status table appears in such a way that in the multi-step form, each step data submission is noted by "completed" or "incompleted" status. If data is successfully submitted from a section in the multi-step form, it will appear as completed by its user name or else status will appear as incomplete with a hyper-link which will throw directly to that section in the form. For that incomplete process four different html pages are made. Which are described below.

    1. [sample_collection.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/sample_collection.html): If incomplete status appears in the status table in the Sample Collection Section. This incomplete href link will direct to this step. Basically its a multi_step_form.html having an editable form.

    2. [DNA_extraction.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/DNA_extraction.html): If incomplete status appears in the status table in the DNA extraction Section. This incomplete href link will direct to this step. Basically its a multi_step_form.html having an editable form.

    3. [library_preparation.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/library_preparation.html): If incomplete status appears in the status table in the Library preparation Section. This incomplete href link will direct to this step. Basically its a multi_step_form.html having an editable form.

    3. [taxonomy_function.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/taxonomy_function.html): If incomplete status appears in the status table in the Taxonomy and function Section. This incomplete href link will direct to this step. Basically its a multi_step_form.html having an editable form.

    4. [report.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/report.html):In the report section from the status table a href link is added which will throw to the report.html page, this page is dedicated for report generation of taxonomy analysis.

    5. [curation.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/curation.html): In the Function section from the status table a href link is added which will throw to the curation.html page, this page is dedicated for report generation of function Recommendation and Interpretation analysis.
    
    5. [tax_curation.html](https://github.com/DecodeAge-Lab/decode-biome-db/blob/main/templates/tax_curation.html): In the Taxonomy curation section from the status table a href link is added which will throw to the tax_curation.html page, this page is dedicated for report generation of Taxonomy Recommendation and interpretaion analysis.

    
