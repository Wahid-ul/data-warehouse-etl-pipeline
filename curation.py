from flask import Flask,flash, render_template,request,jsonify
import requests

import pandas as pd 
import glob
import os
import re
import paramiko as pk
import warnings
import requests
import json
import numpy as np
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from server_main import db,app
from server_main import *
from admin_login import *
from admin_login import *
from etl_script import MicrobeDataTransfer

# Load server credentials
load_dotenv("decodeageserver.env")

# Load Salesforce credentials
load_dotenv("salesforce.env")

transfer=MicrobeDataTransfer(host="0.0.0.0",user="root",database="curation_normalization")
transfer.connect()
df_collect=transfer.get_data()
df_collect = df_collect.sort_values(by='MicrobeID')
transfer.disconnect()

app = Flask(__name__)



# KeyError: "['Category\\n(Commensal/Pathogen/Probiotic)', 'Inflammatory Nature\\n(Pro/Anti)'] 
# df=pd.DataFrame(rows,columns=["MicrobeID","MicrobeName","Domain","Category","Inflammatory Nature","Interpretation"])
df_collect.rename(columns={'MicrobeName': 'Microbes'}, inplace=True)
df_collect = df_collect.drop_duplicates(subset=['Microbes'])

# Split the DataFrame into three separate DataFrames based on the "Domain"
bacteria_curation = df_collect[df_collect['Domain'] == 'Bacteria']
archaea_curation = df_collect[df_collect['Domain'] == 'Archaea']
fungi_curation = df_collect[df_collect['Domain'] == 'Fungi']
# barcode_score1=barcode_score1[0][0]

class SpeciesCheckpoint:

    @staticmethod
    def species_filtering(df):
        # Ensure that 'Microbes' column is treated as string (convert NaNs or non-strings to empty strings)
        df['Microbes'] = df['Microbes'].fillna('').astype(str)

        species = df['Microbes']
        
        # Remove square brackets, and strip leading/trailing spaces
        species = species.apply(lambda s: re.sub(r'[\[\]]', '', s).strip())
        
        # Remove 'sp.' and any text after it
        species = species.apply(lambda s: re.sub(r'\bsp\.\s+.*', '', s).strip())

        # Remove 'aceae' and any word ending with it
        species = species.str.replace(r'\b\w*aceae\b', '', regex=True).str.strip()

        # Remove 'sp.' and any species name after it
        species = species.str.replace(r'\bsp\..*', '', regex=True).str.strip()

        # Removing strain Id
        strain_pattern = re.compile(r'\b[A-Z]+\d+\b|\b\d+[A-Z]+\b')
        
        # Remove strain names (e.g., "strain123", "Bacillus21")
        species = species.apply(lambda s: strain_pattern.sub('', s).strip())

        # Drop rows where 'Microbes' contains 'sp.' or 'aceae' or has strain names
        drop_condition = (
            df['Microbes'].str.contains(r'\bsp\.', regex=True) |
            df['Microbes'].str.contains(r'\b\w*aceae\b', regex=True) |
            df['Microbes'].apply(lambda s: bool(strain_pattern.search(s)) if s is not None else False)
        )

        # Only keep rows that do not match the drop condition
        df = df[~drop_condition].reset_index(drop=True)
        
        # Update the 'Microbes' column with cleaned species names
        df['Microbes'] = species
        
        # If the resulting dataframe is empty, return an empty dataframe to prevent further processing errors
        if df.empty:
            return df

        return df

    @staticmethod
    def archaea_count(archaea):
        if len(archaea['Microbes']) < 4:
            return archaea
        else:
            return archaea.head(4)

    @staticmethod
    def fungi_count(archaea, fungi):
        if archaea['Microbes'].count() == 1:
            return fungi.head(6)
        elif archaea['Microbes'].count() == 2:
            return fungi.head(5)
        elif archaea['Microbes'].count() == 3:
            return fungi.head(4)
        else:
            return fungi.head(3)
# @app.route(['/curation','/run status'],methods=['GET','POST'])

# Airflow API details
AIRFLOW_URL = "http://localhost:8080/api/v1/dags/bioinformatics_pipeline/dagRuns"
AIRFLOW_AUTH = ("airflow", "airflow")  # Change if using different credentials

# SSH Connection Details
SSH_HOST = os.getenv("SERVER_IP")
SSH_USERNAME = os.getenv("SSH_USERNAME")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")

# Connect to remote server
def connect_to_server():
    server = paramiko.SSHClient()
    server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    server.connect(SSH_HOST, username=SSH_USERNAME, password=SSH_PASSWORD)
    return server

# Function to trigger the pipeline in Airflow
@app.route('/trigger_pipeline', methods=['POST'])
def trigger_pipeline():
    response = requests.post(AIRFLOW_URL, json={"conf": {}}, auth=AIRFLOW_AUTH)

    if response.status_code == 200:
        return jsonify({"message": "Pipeline triggered successfully!"})
    else:
        return jsonify({"error": "Failed to trigger pipeline"}), 500

# Function to check DAG run status
@app.route('/run_status', methods=['GET'])
def check_run_status():
    response = requests.get(f"{AIRFLOW_URL}/latest_dag_run", auth=AIRFLOW_AUTH)

    if response.status_code == 200:
        dag_status = response.json()
        return jsonify(dag_status)
    else:
        return jsonify({"error": "Failed to fetch DAG status"}), 500

# Function to check missing curation
@app.route('/curation', methods=['GET', 'POST'])
def check_curation():
    server = connect_to_server()
    base_dir = "/media/decodeage/d1672139-af38-4080-8ce9-3acbf29c35a5/production/decode_biome/decode_biom_results/"
    
    run_dirs = [d for d in list_remote_files(server, base_dir) if re.match(r'RUN_\d+', d) and int(re.search(r'\d+', d).group()) > 133]
    
    checkpoint_df_bacteria = pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/checkpoint/Top_Most_Bacteria_Checkpoint.xlsx", sheet_name="Sheet1")
    checkpoint_df_archaea = pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/checkpoint/Top_Most_Archaea_Checkpoint.xlsx", sheet_name="Hum Gut")
    checkpoint_df_fungi = pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/checkpoint/Top_Most_Fungi_Checkpoint.xlsx", sheet_name="refseq")

    dataframes, dataframe2, dataframe3 = missing_curation_checking_with_taxonomy_dir(
        checkpoint_df_bacteria, checkpoint_df_archaea, checkpoint_df_fungi, server, run_dirs
    )

    missing_barcode_bac = [i[1] for i in dataframe_checking(dataframes)]
    missing_barcode_arc = [i[1] for i in dataframe_checking(dataframe2)]
    missing_barcode_fung = [i[1] for i in dataframe_checking(dataframe3)]

    server.close()
    
    return render_template('curation_index.html', missing_barcode_bac=missing_barcode_bac, 
                           missing_barcode_arc=missing_barcode_arc, missing_barcode_fung=missing_barcode_fung)
@app.route("/delete", methods=["GET", "POST"])
def delete_query():
    source=request.args.get('from')
    Barcode=request.args.get('Barcode')
    
    warnings.filterwarnings("ignore")
    try:
        comp_del = db.engine.execute("DELETE FROM `composition` WHERE Barcode = %s", (Barcode,))
        delete2 = db.engine.execute("DELETE FROM `archaea` WHERE Barcode = %s", (Barcode,))
        delete3 = db.engine.execute("DELETE FROM `bacteria` WHERE Barcode = %s", (Barcode,))
        delete4 = db.engine.execute("DELETE FROM `fungi` WHERE Barcode = %s", (Barcode,))
        delete5 = db.engine.execute("DELETE FROM `function` WHERE Barcode = %s", (Barcode,))
        delete6 = db.engine.execute("DELETE FROM `key_stone_1` WHERE Barcode = %s", (Barcode,))
        delete7 = db.engine.execute("DELETE FROM `pathogen_1` WHERE Barcode = %s", (Barcode,))
        delete8 = db.engine.execute("DELETE FROM `probiotic_1` WHERE Barcode = %s", (Barcode,))
        delete9 = db.engine.execute("DELETE FROM `score` WHERE Barcode = %s", (Barcode,))
        delete10 = db.engine.execute("DELETE FROM `most_abundance_files` WHERE Barcode = %s", (Barcode,))
        
        flash("Successfully deleted", "success")
    except Exception as e:
        flash(f"Error deleting records: {str(e)}", "error")
        return redirect(url_for("check_curation"))
    # return "Delete my existance"
    return redirect(url_for("run status"))

@app.route('/view_taxa_func', endpoint='view_taxa_func', methods=["GET", "POST"])
@app.route('/report_generation', endpoint='report_generation',methods=['GET','POST'])
@app.route('/database_upload', endpoint='database_upload',methods=['GET','POST'])
def report_generation():
    if request.method=="POST":
        # try:
        run=request.form.get('run_id')
        # global barcode
        barcode=request.form.get('barcode')
        print("Barcode from global value",barcode)
        barcode_from_score2=[]
        barcode_from_score=db.engine.execute("SELECT * FROM score")
        barcode_from_score1=barcode_from_score.fetchall()
        for i in barcode_from_score1:
            barcode_from_score2.append(i[0])
        if barcode not in barcode_from_score2:
            def upload_to_database():
                #---------------------------------File upload from the server----------------------------------------------#
                # ------Taxonomy upload----------------------------------#
                cmp="composition"
                # bsp="bacterial_relative"            
                dpro="Detected_probiotic"
                dpth="Detected_pathogen"
                ent="enterotype"
                kst="commensal"
                notpth="not_detected_pathogen"
                notpro="not_detected_probiotic"
                even="evenness"
                rich="richness"
                bact="bacteria_relative"
                arch="archaea_relative"
                fungi="fungi_relative"
                # virus="virus_relative"                
                gmhi="GMHI"
                # phylum_abundance="phylum_relative_abundance"
                # genus_abundance="genus_relative_abundance"
                taxo_command=f"ls  /media/decodeage/d1672139-af38-4080-8ce9-3acbf29c35a5/production/decode_biome/decode_biom_results/{run}/Taxonomy_{barcode}"
                function_command=f"ls  /media/decodeage/d1672139-af38-4080-8ce9-3acbf29c35a5/production/decode_biome/decode_biom_results/{run}/Function_{barcode}"
                # try:
                server=pk.client.SSHClient()
                server.set_missing_host_key_policy(pk.AutoAddPolicy())
                server.connect("192.168.130.245",username="decodeage",password="delete")
                stdin,_stdout,_stderr=server.exec_command(taxo_command)
                output_command=_stdout.read().decode()
                #print("Output command:",output_command)
                
                stdin, _stdout, _stderr = server.exec_command(taxo_command)
                # Wait for the command to complete
                exit_status1 = _stdout.channel.recv_exit_status()
                output_command = _stdout.read().decode()
                filenames = output_command.split()
                
                taxo_files = [filename for filename in filenames if filename.endswith(".csv") or filename.endswith(".xlsx")]
                dataframes=[]
                # #print("Taxonomy CSV files:",taxo_files)
                def file_reading(taxonomy_file):
                    # df=[]
                    for file in taxo_files:
                        # #print(f"Processing CSV file: {csv_file}")
                        if taxonomy_file in file:
                            # Read the CSV file content
                            stdin, stdout, stderr = server.exec_command(f"cat /media/decodeage/d1672139-af38-4080-8ce9-3acbf29c35a5/production/decode_biome/decode_biom_results/{run}/Taxonomy_{barcode}/{file}")
                            file_content = stdout.read()
                            if file.endswith(".csv"):
                                try:

                                    # Parse CSV content
                                    csv_data = StringIO(file_content.decode("utf-8"))
                                    df = pd.read_csv(csv_data)
                                except UnicodeDecodeError:
                                    # csv_data = StringIO(file_content.decode("utf-16").encode('utf-8').decode('utf-8'))
                                    csv_data = StringIO(file_content.decode("utf-16").encode('utf-8').decode('utf-8'))
                                    df = pd.read_csv(csv_data,delimiter="\t")
                            elif file.endswith(".xlsx"):
                                xlsx_data = BytesIO(file_content)
                                df = pd.read_excel(xlsx_data)
                        # dataframes.append(df)
                    # #print("Dataframe:",df)
                    # df=df[0]
                    return df
                def list_df_sql(file,table_name):
                    df=file
                    # assigning index value as global variable universal_Barcode in the dataframe
                    df1 = df.assign(Barcode=barcode)
                    # set index variable after assigning it 
                    df2=df1.set_index('Barcode')                
                    df2.head(10).to_sql(table_name,con=db.engine,if_exists='append')


                composition_file=file_reading(cmp)                   
                k_stone_file=file_reading(kst)                    
                Evenness_file=file_reading(even)                    
                enterotype_file=file_reading(ent)
                gmhi_file=file_reading(gmhi)
                richness_file=file_reading(rich)
                probiotic_detected=file_reading(dpro)
                pathogen_detected=file_reading(dpth)
                probiotic_not_detected=file_reading(notpro)
                pathogen_not_detected=file_reading(notpth)





                # Alpha_file1=file_reading(Alpha)  
                # from Alpha_file1 taking only Shannon_score,Simpson_score,Pielou_score column as a dataframe
                Evenness_file2=Evenness_file[['camargo', 'pielou','simpson','evar','bulla']]
                richness_file2=richness_file[["se.ACE","Shannon","dominance_simpson","InvSimpson","Fisher"]]
                # concatinating Alpha_file2, and gmhi_file to a single dataframe
                evenness_gmhi=pd.concat([Evenness_file2,richness_file2,gmhi_file[['GMHI_Score']]],axis=1)                               
                bacterial_profile_file=file_reading(bact)    
                bacterial_profile_file1=bacterial_profile_file[['Species','Relative_Abundance']] 
                archaea_profile_file=file_reading(arch)    
                archaea_profile_file1=archaea_profile_file[['Species','Relative_Abundance']] 
                fungi_profile_file=file_reading(fungi)    
                fungi_profile_file1=fungi_profile_file[['Species','Relative_Abundance']] 
                # virus_profile_file=file_reading(virus)    
                # virus_profile_file1=virus_profile_file[['Kingdom','Phylum','Class','Order','Family','Genus','Species','Abundance']]
                # df_test=bacterial_profile_file1.assign(Barcode=barcode)
                # df_test2=df_test.set_index('Barcode')
                # df_test2.head(10).to_sql('bacteria',con=db.engine,if_exists='append')
                list_df_sql(file=bacterial_profile_file1,table_name='bacteria')
                list_df_sql(file=archaea_profile_file1,table_name='archaea')
                list_df_sql(file=fungi_profile_file1,table_name='fungi')
                # list_df_sql(file=virus_profile_file1,table_name='virus')
                #---------------------Blob conversion-----------------------#

                list1=[barcode,pickle.dumps(bacterial_profile_file),pickle.dumps(archaea_profile_file),pickle.dumps(fungi_profile_file),pickle.dumps(pathogen_not_detected),pickle.dumps(probiotic_not_detected)]
                query1="INSERT INTO most_abundance_files VALUES ({})".format(",".join(["%s"] * len(list1)))
                db.engine.execute(query1,list1)
                #------------------------------------------------------------#
                print("Probiotic detected df",probiotic_detected.columns.tolist())
                # #print("Pathogen not df",pathogen_not_detected)


                #--------------------------------Dict to sql -------------------------------------------------#
                def taxonomy_database(table_name,df_file):
                    # object creating for factching table row
                    obj1=db.engine.execute('SELECT * FROM '+table_name)
                    # fetching header name list from the mentioned sql-table 
                    column_names = obj1.keys()
                    #comparing df_file as an input dataframe with each dataframe composition_file,k_stone_file,pathogen_file,probiotic_file
                    #using if-elif statement
                    if df_file.equals(composition_file):  
                        # converting into dictionary where Kingdome column will be key element and percent column will be value                           
                        dict=df_file.set_index('Kingdom')['percent'].to_dict()

                    elif df_file.equals(enterotype_file):
                        dict=df_file.set_index('Enterotype')['Relative_abundance'].to_dict()
                    # if input dataframe matches with k_stone_file dataframe it will read this statement
                    elif df_file.equals(k_stone_file):
                        # replacing Species column where value having <space> will be replaced to '_'
                        df_file['Species'] = df_file['Commensal_Species'].str.replace(' ', '_')
                        #taking Species column as key and Abundance column as corresponding value 
                        dict=df_file.set_index('Species')['Relative_Abundance'].to_dict()
                    # if input dataframe matches with pathogen_file dataframe it will read this statement
                    elif df_file.equals(pathogen_detected): 
                        # replacing Species column where value having <space> will be replaced to '_'
                        df_file['Detected_pathogen_species'] = df_file['Detected_pathogen_species'].str.replace(' ', '_')
                        #taking Species column as key and Abundance column as corresponding value 
                        dict=df_file.set_index('Detected_pathogen_species')['Relative_Abundance'].to_dict() 
                    # if input dataframe matches with probiotic_file dataframe it will read this statement
                    elif df_file.equals(probiotic_detected):
                        # replacing Species column where value having <space> will be replaced to '_'
                        df_file['Detected_probiotic_species'] = df_file['Detected_probiotic_species'].str.replace(' ', '_')
                        #taking Species column as key and Abundance column as corresponding value 
                        dict=df_file.set_index('Detected_probiotic_species')['Relative_Abundance'].to_dict() 
                    # creating an empty list to put all above dict parsing value
                    list1=[]
                    #using for loop iteration, checking sql-header name is matching with dict-key or not 
                    # if it matches it will append as an element to the empty list or else it will append a blank space 
                    for i in column_names:
                    
                        if i in dict.keys():
                            list1.append(dict[i])
                        else:
                            list1.append("")
                    # adding current barcode to the first postiong of the list
                    list1[0]=barcode
                    
                    #inserting into the respective sql-table
                    query1 = "INSERT INTO "+table_name+" VALUES ({})".format(", ".join(["%s"] * len(list1)))
                    #execution list elements 
                    db.engine.execute(query1, list1)
                #function calling
                taxonomy_database(table_name='composition',df_file=composition_file)
                taxonomy_database(table_name='key_stone_1',df_file=k_stone_file)
                taxonomy_database(table_name='pathogen_1',df_file=pathogen_detected)
                taxonomy_database(table_name='probiotic_1',df_file=probiotic_detected)
                taxonomy_database(table_name='enterotype',df_file=enterotype_file)
                #-----------------------------------------------------------------------------#


                #----------------------------Score----------------------------------------------#
                def df_sql(file,table_name):
                    file=file.assign(Barcode=barcode)
                    file=file.set_index('Barcode')
                    file.to_sql(table_name,con=db.engine,if_exists='append')
                df_sql(evenness_gmhi,table_name="score")
                server.close()
                #-------------------------------------------------------------------------------#

                #---------------------------enterotype---------------------------------------------#


                #---------------------------------------------------------------------------------#
                # ----------------------------------------function file upload--------------------------------------------------#
                server=pk.client.SSHClient()
                server.set_missing_host_key_policy(pk.AutoAddPolicy())
                server.connect("192.168.130.245",username="decodeage",password="delete")
                stdin, _stdout, _stderr = server.exec_command(function_command)
                # Wait for the command to complete
                exit_status2 = _stdout.channel.recv_exit_status()
                function_output_command = _stdout.read().decode()
                funciton_filenames = function_output_command.split()
                function_files = [filename for filename in funciton_filenames if filename.endswith(".csv") ]
                def fn_file_reading(function_file):
                    for file in function_files:
                        # #print(f"Processing CSV file: {csv_file}")
                        if function_file in file:
                            # Read the CSV file content
                            stdin, stdout, stderr = server.exec_command(f"cat /media/decodeage/d1672139-af38-4080-8ce9-3acbf29c35a5/production/decode_biome/decode_biom_results/{run}/Function_{barcode}/{file}")
                            file_content = stdout.read()
                            if file.endswith(".csv"):
                            # Parse CSV content
                                csv_data = StringIO(file_content.decode("utf-8"))
                                df = pd.read_csv(csv_data)
                    return df
                carb="carbs"
                gas="Gas"
                gutbrain="gutbrain"
                lpd="lipids"
                prt="protein"
                scfa="SCFA"
                vtm="vitamin"
                mtb="Metabolism"
                result="Result"
                result_file=fn_file_reading(result).reset_index(drop=True)
                #print("One function file is there so see it properly:",result_file)
                #creating a function for function -file analysis
                def function_database(metabolic_file):
                    # dict1=gut.set_index('METABOLIC_PROFILE')['OVERALL_RA'].to_dict()
                    # dict2=lipid.set_index('METABOLIC_PROFILE')['OVERALL_RA'].to_dict()
                    # dict3=gas.set_index('METABOLIC_PROFILE')['OVERALL_RA'].to_dict()
                    # dict4=SCFA.set_index('METABOLIC_PROFILE')['OVERALL_RA'].to_dict()
                    # vitamin['METABOLIC_PROFILE'] = vitamin['METABOLIC_PROFILE'].str.replace(' ', '_')
                    # dict5=vitamin.set_index('METABOLIC_PROFILE')['OVERALL_RA'].to_dict()
                    # dict6=metabolic.set_index('METABOLIC_PROFILE')['OVERALL_RA'].to_dict()
                    dict1=metabolic_file.set_index('METABOLITES')['RA'].to_dict()
                    obj=db.engine.execute('SELECT * FROM function')
                    table_column_names = obj.keys()
                    list2=[]
                    for i in table_column_names:                                                          
                        if i in dict1.keys():
                            list2.append(dict1[i])
                        # elif i in dict2.keys():
                        #     list2.append(dict2[i])
                        # elif i in dict3.keys():
                        #     list2.append(dict3[i])
                        # elif i in dict4.keys():
                        #     list2.append(dict4[i])
                        # elif i in dict5.keys():
                        #     list2.append(dict5[i])
                        # elif i in dict6.keys():
                        #     list2.append(dict6[i])
                        else:
                            list2.append(0)
                    list2[0]=barcode
                    #print("list2",list2)
                    query2 = "INSERT INTO function VALUES ({})".format(", ".join(["%s"] * len(list2)))
                    db.engine.execute(query2, list2)
                #function callling
                function_database(result_file) 
                #print("Function files uploaded successfully!")
                return "success"
        elif barcode in barcode_from_score2:

            #--------------------------------------------------------CSV generation ---------------------------------------------------#
            v1 = "'" + barcode + "'"

            a=db.engine.connect('db_test')
            b=a.execute("SHOW TABLES")
            # query function
            def biome_query(tableID,BarcodeID):
                var_table=db.engine.execute("SELECT * FROM %s where Barcode=%s"%(tableID,BarcodeID))
                var_table1=var_table.fetchall()
                return var_table1



            #---------------------------------GMHI----------------------------------------------------------#
            # ---------------------------Biome Score---------------------------------------------#
            score=biome_query(tableID='score',BarcodeID=v1)
            gmhi_index=["GMHI Score"]
            gmhi_score=round(score[0][11],2)
            gmhi_remarks=[]
            if  gmhi_score>0:
                gmhi_remarks.append("A high score indicates the dominance of disease-preventing bacteria over disease-promoting ones in your gut, protecting you from health issues. Keeping your score high is essential for maintaining good health.")
        
            else:
                gmhi_remarks.append("A low score indicates the dominance of disease-promoting bacteria over disease-preventing ones in your gut, making you more prone to health issues. But don't worry, you can improve your gut health with dietary & lifestyle changes.")
            # gmhi_column=["GMHI","Score","Remarks"]
            gmhi_df=pd.DataFrame({"GMHI":gmhi_index,"Score":gmhi_score,"Remarks":gmhi_remarks})
            # dictonary format to get the json structure
            biomeScore = {
                "key": "GMHI Score",
                "value": gmhi_score,
                "remark": " ".join(gmhi_remarks)
            }
                                                                                
            # #print("GMHI df")
            # #print(gmhi_df)
            #------------------------------------------------------------------------------------#
            #------------------------------------------------------------------------------------------------#
            #-----------------------------shannon score----------------------------------------------------#
            shannon_index=["Shannon index"]
            shannon_score=round(score[0][7],2)
            shannon_remarks=[]
            if shannon_score>3.50:
                shannon_remarks.append("High microbial diversity indicates a wide variety of different microbes in your gut, contributing to a strong & healthy gut environment. This supports overall gut function & helps you stay healthy.")
            else:
                shannon_remarks.append("Low microbial diversity in the gut indicates a lack of different types of microbes, making it susceptible to infections & linked to conditions i.e., IBD, obesity & metabolic disorders. Making healthy changes can help improve diversity.")

            shannon_df=pd.DataFrame({"Diversity Index":shannon_index,"Score":shannon_score,"Remarks":shannon_remarks})
            diversityIndeces=[{
                "key": "Shannon index",
                "value": shannon_score,
                "remark": " ".join(shannon_remarks)
            }]
            #------------------------------------------------------------------------------------------------#
            #----------------------------------------Composition-----------------------------------------------------#
            composition=biome_query(tableID='composition',BarcodeID=v1)
            kingdoms = ['Bacteria', 'Archaea', 'Fungi']
            percentages = [round(val, 2) for val in composition[0][1:]]
            composition_dict = {'Kingdom': kingdoms, 'Percentage': percentages}
            composition_df = pd.DataFrame(composition_dict)
            composition_json=[
                { "kingdom": "Bacteria", "percentage": composition[0][1] },
                { "kingdom": "Archaea", "percentage": composition[0][2] },
                { "kingdom": "Fungi", "percentage": composition[0][3] }
                ]
            #---------------------------------------------------------------------------------------------------------#
            #-----------------------------------FIltering claas----------------------------------------------------#
            class SpeciesCheckpoint:
                def species_filtering(df):
                    species=df['microbes']
                    species=species.apply(lambda s:re.sub(r'[\[\]]', '', s).strip())
                    species=species.apply(lambda s: re.sub(r'\bsp\.\s+.*', '', s).strip())
                    species=species.str.replace(r'\b\w*aceae\b', '', regex=True).str.strip()
                    # remove sp.
                    species=species.str.replace(r'\bsp\..*', '', regex=True).str.strip()
                    # removing strain Id 
                    strain_pattern = re.compile(r'\b[A-Z]+\d+\b|\b\d+[A-Z]+\b')
                    # Remove species with strain names
                    species = species.apply(lambda s: strain_pattern.sub('', s).strip())
                    # Drop rows where 'Species' contains 'sp.' or 'aceae' or has strain names
                    drop_condition = (
                        df['microbes'].str.contains(r'\bsp\.', regex=True) |
                        df['microbes'].str.contains(r'\b\w*aceae\b', regex=True) |
                        df['microbes'].apply(lambda s: bool(strain_pattern.search(s)))
                    )
                    df = df[~drop_condition].reset_index(drop=True)
                    df['microbes']=species
                    return df

                def archaea_count(archaea):
                    if len(archaea['microbes'])<4:
                        return archaea
                    else:
                        return archaea.head(4)

                def fungi_count(archaea,fungi):
                    if archaea['microbes'].count()==1:
                        return fungi.head(6)
                    elif archaea['microbes'].count()==2:
                        return fungi.head(5)
                    elif archaea['microbes'].count()==3:
                        return fungi.head(4)
                    else:
                        return fungi.head(3)
            #------------------------------------------------------------------------------------------------------#
            # -----------------Most abundance merge and their RA value------------------------------#
            bacteria_data=db.engine.execute("SELECT * FROM  most_abundance_files where Barcode=%s"%(v1))
            bacteria_data1=bacteria_data.fetchall()
            bacteria_data2=pickle.loads(bacteria_data1[0][1])
            bacteria_data2["Domain"]="Bacteria"
            archaea_data=db.engine.execute("SELECT * FROM  most_abundance_files where Barcode=%s"%(v1))
            archaea_data1=archaea_data.fetchall()
            archaea_data2=pickle.loads(archaea_data1[0][2])
            archaea_data2["Domain"]="Archaea"

            fungi_data=db.engine.execute("SELECT * FROM  most_abundance_files where Barcode=%s"%(v1))
            fungi_data1=fungi_data.fetchall()
            fungi_data2=pickle.loads(fungi_data1[0][3])
            fungi_data2["Domain"]="Fungi"

            all_domain=pd.concat([bacteria_data2,archaea_data2,fungi_data2] ,axis=0, join='outer')
            domain_sums=all_domain["Absolute_abundance"].sum()
            all_domain['Relative_Abundance'] = (all_domain['Absolute_abundance'] / domain_sums) * 100
            df_archaea = all_domain[all_domain['Domain'] == 'Archaea']
            df_bacteria = all_domain[all_domain['Domain'] == 'Bacteria']
            df_fungi = all_domain[all_domain['Domain'] == 'Fungi']
            #--------------------------------------------------------------------------------------#
            #-----------------------------top most abundance species----------------------------------#
            # Curation is under processing

            # take directly from the file
            # bacteria_data=db.engine.execute("SELECT * FROM  most_abundance_files where Barcode=%s"%(v1))
            # bacteria_data1=bacteria_data.fetchall()
            # bacteria_data2=pickle.loads(bacteria_data1[0][1])
            bacteria_data3=df_bacteria[[ 'Species', 'Relative_Abundance']]
            # print("Bacteria before curation",bacteria_data3.head(15))
            bacteria1=biome_query(tableID='bacteria',BarcodeID=v1)
            def top10_df(profile_file):
                profile_file1=[( t[-2:]) for t in profile_file]
                columns = [  'Species', 'Abundance']
                profile_file1_df = pd.DataFrame(profile_file1, columns=columns)
                # profile_file1_df['Genus Species']=profile_file1_df['Genus'] + ' ' + profile_file1_df['Species']
                # profile_file1_df.drop(['Genus', 'Species'], axis=1, inplace=True)
                # profile_file1_df[['Genus Species','Abundance']]
                return profile_file1_df
            bacteria_df=top10_df(bacteria1)
            checkpoint_df_bacteria=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/checkpoint/Top_Most_Bacteria_Checkpoint.xlsx",sheet_name="Sheet1")
            
            bacterial_merged_with_checkpoint=pd.merge(checkpoint_df_bacteria,bacteria_data3,left_on="species",right_on="Species",how="inner")
            bacterial_merged_with_checkpoint['Species'] = bacterial_merged_with_checkpoint.apply(lambda row: row['Unnamed: 4'] if pd.notna(row['Unnamed: 4']) else row['Species'], axis=1)
            bacterial_merged_with_checkpoint=bacterial_merged_with_checkpoint[[ 'Species', 'Relative_Abundance']]
            bacterial_merged_with_checkpoint=bacterial_merged_with_checkpoint.sort_values('Relative_Abundance',ascending=False)
            # print("Bacteria after checkpoint",bacterial_merged_with_checkpoint.sort_values('Relative_Abundance',ascending=False).head(10))
            # bacteria_curation=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/Production/Final Most Abundant Bacteria species Production (Curated by DC team).xlsx",sheet_name="All Species")
            bacterial_merged=pd.merge(bacteria_curation,bacterial_merged_with_checkpoint,left_on="Microbes",right_on="Species",how="right")
            # bacterial_merged=bacterial_merged[["Category\n(Commensal/Pathogen/Probiotic)","Species","Relative_Abundance","Inflammatory Nature\n(Pro/Anti)","Interpretation"]]
            bacterial_merged=bacterial_merged[["Category","Species","Relative_Abundance","Inflammatory Nature","Interpretation"]]
            bacterial_merged['Interpretation']=bacterial_merged['Interpretation'].str.replace('\n\n', ' ')
            # bacterial_merged.rename(columns = {'Category\n(Commensal/Pathogen/Probiotic)':'category','Inflammatory Nature\n(Pro/Anti)':'inflammatoryNature','Relative_Abundance':'relativeAbundance','Species':'microbes','Interpretation':'interpretation'}, inplace = True)
            bacterial_merged.rename(columns = {'Category':'category','Inflammatory Nature':'inflammatoryNature','Relative_Abundance':'relativeAbundance','Species':'microbes','Interpretation':'interpretation'}, inplace = True)
            bacterial_merged_sorted=bacterial_merged.sort_values('relativeAbundance',ascending=False)
            bacterial_merged_sorted1=bacterial_merged_sorted.head(9)
            bacterial_merged_sorted1['inflammatoryNature'] = bacterial_merged_sorted1['inflammatoryNature'].replace('EmptyNature', np.nan)
            topSpeciesBacteria=bacterial_merged_sorted1.to_dict('records')
            
            #archaea count
            # archaea_data=db.engine.execute("SELECT * FROM  most_abundance_files where Barcode=%s"%(v1))
            # archaea_data1=archaea_data.fetchall()
            # archaea_data2=pickle.loads(archaea_data1[0][2])
            archaea_data3=df_archaea[[ 'Species', 'Relative_Abundance']]

            checkpoint_df_archaea=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/checkpoint/Top_Most_Archaea_Checkpoint.xlsx",sheet_name="Hum Gut")
            # bacteria1=biome_query(tableID='bacteria',BarcodeID=v1)
            archaea_merged_with_checkpoint=pd.merge(checkpoint_df_archaea,archaea_data3,left_on="Archaea",right_on="Species",how="inner")
            archaea_merged_with_checkpoint["Species"]=archaea_merged_with_checkpoint.apply(lambda row:row['Unnamed: 4'] if pd.notna(row['Unnamed: 4']) else row['Species'],axis=1)
            archaea_merged_with_checkpoint=archaea_merged_with_checkpoint[[ 'Species', 'Relative_Abundance']]
            archaea_merged_with_checkpoint=archaea_merged_with_checkpoint.sort_values('Relative_Abundance',ascending=False)
            
            
            
            
            archaea1=biome_query(tableID='archaea',BarcodeID=v1)
            archaea_df=top10_df(archaea1)
            # archaea_curation=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/Production/Final Most Abundant Archaea species Production (Curated by DC team).xlsx",sheet_name="All Species")
            # archaea_curation=archaea_curation.drop_duplicates()

            archaea_merged=pd.merge(archaea_curation,archaea_merged_with_checkpoint,left_on="Microbes",right_on="Species",how="right")
            archaea_merged=archaea_merged[['Category', 'Species', 'Relative_Abundance', 'Inflammatory Nature', 'Interpretation']]
            archaea_merged.rename(columns = {'Category':'category','Inflammatory Nature':'inflammatoryNature','Relative_Abundance':'relativeAbundance','Species':'microbes','Interpretation':'interpretation'}, inplace = True)
            # archaea_merged = archaea_merged.drop_duplicates()
            archaea_merged_sorted=archaea_merged.sort_values('relativeAbundance',ascending=False)
            archaea_merged_sorted['inflammatoryNature'] = archaea_merged_sorted['inflammatoryNature'].replace('EmptyNature', np.nan)
            archaea_1st_filtering=SpeciesCheckpoint.species_filtering(archaea_merged_sorted)
            
            topSpeciesArchaea=SpeciesCheckpoint.archaea_count(archaea_1st_filtering).to_dict('records')
            # archaea_merged=archaea_merged['Interpretation'].str.replace('\n\n', ' ')
            # fungi_data=db.engine.execute("SELECT * FROM  most_abundance_files where Barcode=%s"%(v1))
            # fungi_data1=fungi_data.fetchall()
            # fungi_data2=pickle.loads(fungi_data1[0][3])
            fungi_data3=df_fungi[[ 'Species', 'Relative_Abundance']]
            
            checkpoint_df_fungi=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/checkpoint/Top_Most_Fungi_Checkpoint.xlsx",sheet_name="refseq")
            fungi_merged_with_checkpoint=pd.merge(checkpoint_df_fungi,fungi_data3,left_on="species",right_on="Species",how="inner")
            fungi_merged_with_checkpoint["Species"]=fungi_merged_with_checkpoint.apply(lambda row:row['Unnamed: 4'] if pd.notna(row['Unnamed: 4']) else row['Species'],axis=1)
            fungi_merged_with_checkpoint=fungi_merged_with_checkpoint[[ 'Species', 'Relative_Abundance']]
            fungi_merged_with_checkpoint=fungi_merged_with_checkpoint.sort_values('Relative_Abundance',ascending=False)
            # print("Fungi Chekpoint",fungi_merged_with_checkpoint)
            fungi1=biome_query(tableID='fungi',BarcodeID=v1)
            fungi_df=top10_df(fungi1)
            # fungi_curation=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/Production/Final Most Abundant Fungal species Production (Curated by DC team).xlsx",sheet_name="All Species")
            # print("Fungi curation",fungi_curation.iloc[2,])
            fungi_merged=pd.merge(fungi_curation,fungi_merged_with_checkpoint,left_on="Microbes",right_on="Species",how="right")
            # print("Fungi Merge curation sheet",fungi_merged)
            fungi_merged=fungi_merged[['Category', 'Species', 'Relative_Abundance', 'Inflammatory Nature', 'Interpretation']]
            fungi_merged.rename(columns = {'Category':'category','Inflammatory Nature':'inflammatoryNature','Relative_Abundance':'relativeAbundance','Species':'microbes','Interpretation':'interpretation'}, inplace = True)
            # fungi_merged.dropna(inplace=True)
            fungi_merged_sorted=fungi_merged.sort_values('relativeAbundance',ascending=False)
            fungi_merged_sorted['inflammatoryNature'] = fungi_merged_sorted['inflammatoryNature'].replace('EmptyNature', np.nan)
            
            fungi_1st_filtering=SpeciesCheckpoint.species_filtering(fungi_merged_sorted)
            fungi_2nd_filtering=SpeciesCheckpoint.fungi_count(SpeciesCheckpoint.archaea_count(archaea_1st_filtering),fungi_1st_filtering)
            topSpeciesFungi=fungi_2nd_filtering.to_dict('records')
            # print("fungi_merged_sorted",fungi_merged_sorted)
            # fungi_merged=fungi_merged['Interpretation'].str.replace('\n\n', ' ')
            #-------------------------------------------------------------------------------------------#
            #-------------------------Pathogen (Detected and not detected)---------------------------------------#
            #-----Detected----------------------------------------------------------------------------------------#
            pathogen_1=db.engine.execute("SELECT * FROM pathogen_1 where Barcode=%s"%(v1))
            pathogen_db=biome_query(tableID='pathogen_1',BarcodeID=v1)
            pathogen_dataframe=pd.DataFrame({"Bacteria":pathogen_1.keys(),"Abundance":pathogen_db[0]})
            pathogen_dataframe["Pathogen Species Name"]=pathogen_dataframe['Bacteria'].str.replace('[','').str.replace(']','').str.replace('_',' ')
            pathogen_dataframe['Abundance']=pathogen_dataframe['Abundance'].apply(pd.to_numeric, errors='coerce')
            pathogen_dataframe1=pathogen_dataframe.dropna()
            pathogen_curation=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/Production/Final Pathogen species Production (Curated by DC team).xlsx",sheet_name="All Species")
            pathogen_curation=pathogen_curation[["Pathogen Species Name","Domain","Category (True/Opportunistic)","Interpretations"]]
            pathogen_merged=pd.merge(pathogen_curation,pathogen_dataframe1,left_on="Pathogen Species Name",right_on="Pathogen Species Name",how="inner")
            pathogen_merged.dropna(inplace=True)
            pathogen_merged['Interpretations'] = pathogen_merged['Interpretations'].str.replace('\n\n', ' ')
            pathogen_merged=pathogen_merged[["Pathogen Species Name","Abundance","Domain","Category (True/Opportunistic)","Interpretations"]]
            pathogen_merged=pathogen_merged.rename(columns={'Abundance':'relativeAbundance',"Pathogen Species Name":'pathogen','Domain':'domain','Category (True/Opportunistic)':'category','Interpretations':'interpretation'})
            pathogen_merged_sorted=pathogen_merged.sort_values('relativeAbundance',ascending=False)
            pathogen_dict=pathogen_merged_sorted.head(15).to_dict('records')
            # #print("pathogen_merged dataframe",pathogen_merged)

            
            # pathogen_df.columns = pathogen_df.iloc[0]
            # pathogen_df = pathogen_df.iloc[1:].reset_index(drop=True)
            #------------------------------------------------------------------------------------------------------#
            #-------Not Detected------------------------------------------------------------------------------------#
            not_detected_pathogen=db.engine.execute("SELECT * FROM most_abundance_files where Barcode=%s"%(v1))
            
            not_detected_pathogen1=not_detected_pathogen.fetchall()
            # if not
            not_detected_pathogen_df=pickle.loads(not_detected_pathogen1[0][4])
            not_detected_pathogen_df=not_detected_pathogen_df[["Not_pathogen_species"]]
            # not_detected_pathogen_df
            not_detected_pathogen_df['Not_pathogen_species'] = not_detected_pathogen_df['Not_pathogen_species'].str.replace(r'\[(.*?)\]', r'\1', regex=True)
            # not_detected_pathogen_curation_sheet=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/Production/Final Pathogen species Production (Curated by DC team).xlsx",sheet_name="Not Detected")
            not_detected_pathogen_df=not_detected_pathogen_df.rename(columns={'Not_pathogen_species':'pathogen'})
            not_detected_pathogen_dict=not_detected_pathogen_df.head(8).to_dict('records')
            # not_detected_pathogen_merged=pd.merge(not_detected_pathogen_df,not_detected_pathogen_curation_sheet,left_on="Not_pathogen_species",right_on="Pathogens Not Detected Species Name ",how="inner")
            # not_detected_pathogen_merged=not_detected_pathogen_merged[["Not_pathogen_species"]]
            # not_detected_pathogen1=not_detected_pathogen[0][5]
            # not_detected_pathogen_df=pickle.loads(not_detected_pathogen1)
            
            #------------------------------------------------------------------------------------------------------#
            #-----------------------------------------------------------------------------------------------------#
            
            
            
            #----------------------------------------Probiotic -----------------------------------------------------------------#
            #-------Detected------------------------------------------------------------------------------------------------#
            probiotic_1=db.engine.execute("SELECT * FROM probiotic_1 where Barcode=%s"%(v1))
            probiotic_db=biome_query(tableID='probiotic_1',BarcodeID=v1)
            probiotic_dataframe=pd.DataFrame({"Bacteria":probiotic_1.keys(),"Relative Abundance":probiotic_db[0]})
            probiotic_dataframe["Species Name"]=probiotic_dataframe['Bacteria'].str.replace('[','').str.replace(']','').str.replace('_',' ')
            probiotic_dataframe['Relative Abundance']=probiotic_dataframe['Relative Abundance'].apply(pd.to_numeric, errors='coerce')
            #print("Probiotic before dropping",probiotic_dataframe)
            probiotic_dataframe1=probiotic_dataframe.dropna()
            #print("Probiotic after dropping",probiotic_dataframe1)
            probiotic_curation=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/Production/Final Probiotic species Production (Curated by DC team).xlsx",sheet_name="Probiotic species List")
            probiotic_curation=probiotic_curation[["Species Name","Domain","Interpretations"]]
            probiotic_merged=pd.merge(probiotic_curation,probiotic_dataframe1,left_on="Species Name",right_on="Species Name",how="right")
            probiotic_merged=probiotic_merged[["Species Name","Relative Abundance","Domain","Interpretations"]]
            probiotic_merged=probiotic_merged.rename(columns={'Relative Abundance':'relativeAbundance',"Species Name":'species','Domain':'domain','Interpretations':'interpretation'})
            probiotic_merged_sorted=probiotic_merged.sort_values('relativeAbundance',ascending=False)
            probiotic_json=probiotic_merged_sorted.head(15).to_dict('records')
            # probiotic_merged=probiotic_merged.rename(columns={'Abundance':'Relative Abundance'})
            # probiotic_merged.dropna(inplace=True)
            # print("Probiotic merged :",probiotic_merged)
            #-------Not Detected------------------------------------------------------------------------------------#
            not_detected_probiotic=db.engine.execute("SELECT * FROM most_abundance_files where Barcode=%s"%(v1))
            not_detected_probiotic1=not_detected_probiotic.fetchall()
            not_detected_probiotic2=not_detected_probiotic1[0][5]
            not_detected_probiotic_df=pickle.loads(not_detected_probiotic2)
            not_detected_probiotic_df=not_detected_probiotic_df[["Not_detected_species"]]
            not_detected_probiotic_df['Not_detected_species'] = not_detected_probiotic_df['Not_detected_species'].str.replace(r'\[(.*?)\]', r'\1', regex=True)
            not_detected_probiotic_df=not_detected_probiotic_df.rename(columns={'Not_detected_species':'species'})
            not_detected_probiotic_json=not_detected_probiotic_df.head(8).to_dict('records')
            # not_detected_probiotic_curation_sheet=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/Production/Final Probiotic species Production (Curated by DC team).xlsx",sheet_name="Imp Species (For Not Detected)")

            # not_detected_probiotic_merged=pd.merge(not_detected_probiotic_df,not_detected_probiotic_curation_sheet,left_on="Not_detected_species",right_on="Important Probiotic Species Name ",how="inner")
            # not_detected_probiotic_merged=not_detected_probiotic_merged[["Not_detected_species"]]
            #------------------------------------------------------------------------------------------------------#
            #-----------------------------------------------------------------------------------------------------#
            #----------------------------------Commensal(key-stone)-----------------------------------------------------------#
            #-------------------------------Keystone species--------------------------------------#
            key_stone_range=db.engine.execute("SELECT * FROM keystone_db__1_")
            key_stone_range1=key_stone_range.fetchall()
            key_stone_1=db.engine.execute("SELECT * FROM key_stone_1 where Barcode=%s"%(v1))
            kstone1=biome_query(tableID='key_stone_1',BarcodeID=v1)
            key_stone_dataframe=pd.DataFrame({"Bacteria":key_stone_1.keys(),"Abundance":kstone1[0]})
            key_stone_dataframe["Species"]=key_stone_dataframe['Bacteria'].str.replace('[','').str.replace(']','').str.replace('_',' ')
            # #print("Key stone with new column checking null value")
            key_stone_dataframe['Abundance']=key_stone_dataframe['Abundance'].apply(pd.to_numeric, errors='coerce')
            keystonedatabase1=key_stone_dataframe.dropna()
            # #print("keystonedatabase1:")
            # #print(keystonedatabase1)
            # #print(key_stone_dataframe['Abundance'])
            # #print("Keystone from google sheet")
            # #print(key_stone_df)
            # key stone range dfdf = pd.DataFrame
            key_stone_range_df=pd.DataFrame(key_stone_range1, columns=['Species', 'Min', 'Max'])
            merged_df = pd.merge(key_stone_range_df, keystonedatabase1, left_on='Species',right_on='Species', how='inner')
            merged_df.dropna(inplace=True)
            merged_df[['Abundance', 'Min', 'Max']] = merged_df[['Abundance', 'Min', 'Max']].apply(pd.to_numeric, errors='coerce')
            # #print("Key stone range df")
            def check_range(row):
                if pd.isnull(row['Abundance']) or pd.isnull(row['Min']) or pd.isnull(row['Max']):
                    return 'NaN'  # Handle NaN values
                elif row['Abundance'] >= row['Min'] and row['Abundance'] <= row['Max']:
                    return 'In Range'
                elif row['Abundance'] > row['Max']:
                    return 'High'
                else:
                    return 'Low'
            merged_df['Range'] = merged_df.apply(check_range, axis=1)
            def get_content(row):
                if row['Range'] == 'High Range':
                    return key_stone_df.loc[key_stone_df['Keystone Species'] == row['Species'], 'High'].iloc[0]
                elif row['Range'] == 'Low Range':
                    return key_stone_df.loc[key_stone_df['Keystone Species'] == row['Species'], 'Low'].iloc[0]
                else:
                    return ''
            # merged_df['Recommendation (Low/High)'] = merged_df.apply(get_content, axis=1)
            final_keystone_df=merged_df[["Bacteria","Abundance","Range"]]
            final_keystone_df=final_keystone_df.rename(columns={'Abundance':'relativeAbundance','Bacteria':'bacteria','Range':'range'})
            final_keystone_sorted=final_keystone_df.sort_values('relativeAbundance',ascending=False)
            # #print("Final keystone df",final_keystone_df)
            
            key_stone_json=final_keystone_sorted.head(22).to_dict('records')
            #-------------------------------------------------------------------------------------#
            #-----------------------------------------------------------------------------------------------------#
            #-------------------------Enterotype-------------------------------------------------------#
            enterotype=biome_query(tableID='enterotype',BarcodeID=v1)
            enterotype_index=["Prevotella","Bacteroides","Ruminococcus"]
            enterotype_score=[round(val,2) for val in enterotype[0][1:]]
            enterotype_remarks=[]
            if enterotype_score[0]> enterotype_score[1] and enterotype_score[0]> enterotype_score[2]:
                enterotype_remarks.append("Enterotype 2 is characterized by the dominance of Prevotella species and indicates that your gut has adapted to a diet rich in carbohydrates (specifically fibre), allowing efficient digestion of these food sources.")
            else:
                enterotype_remarks.append("")
            if enterotype_score[1]> enterotype_score[0] and enterotype_score[1]> enterotype_score[2]:
                enterotype_remarks.append("Enterotype 1 is characterized by the dominance of Bacteroides species. This indicates your gut has adapted high protein and animal fat diet, facilitating efficient digestion of these food sources.")
            else:
                enterotype_remarks.append("")
            if enterotype_score[2]> enterotype_score[0] and enterotype_score[2]> enterotype_score[1]:
                enterotype_remarks.append("Enterotype 3 is characterized by the dominance of Ruminococcus species and indicates that your gut has adapted to a mixed diet, including resistant starch, unsaturated fat, and to a lesser extent, protein, enabling efficient digestion of these food sources.")
            else:
                enterotype_remarks.append("")
            enterotype_df=pd.DataFrame({"enterotype":enterotype_index,"score":enterotype_score,"remarks":enterotype_remarks})
            enterotype_json=enterotype_df.to_dict('records')
            # #print("enterotype df")
            # #print(enterotype_df)
            #-----------------------------------------------------------------------------------------------#
            # return "kuch bhi"

            
            # -------------------------Species filtering process ----------------------------------- #
            class SpeciesCheckpoint:
                def species_filtering(df):
                    species=df['microbes']
                    species=species.apply(lambda s:re.sub(r'[\[\]]', '', s).strip())
                    species=species.apply(lambda s: re.sub(r'\bsp\.\s+.*', '', s).strip())
                    species=species.str.replace(r'\b\w*aceae\b', '', regex=True).str.strip()
                    # remove sp.
                    species=species.str.replace(r'\bsp\..*', '', regex=True).str.strip()
                    # removing strain Id 
                    strain_pattern = re.compile(r'\b[A-Z]+\d+\b|\b\d+[A-Z]+\b')
                    # Remove species with strain names
                    species = species.apply(lambda s: strain_pattern.sub('', s).strip())
                    # Drop rows where 'Species' contains 'sp.' or 'aceae' or has strain names
                    drop_condition = (
                        df['microbes'].str.contains(r'\bsp\.', regex=True) |
                        df['microbes'].str.contains(r'\b\w*aceae\b', regex=True) |
                        df['microbes'].apply(lambda s: bool(strain_pattern.search(s)))
                    )
                    df = df[~drop_condition].reset_index(drop=True)
                    df['microbes']=species
                    return df

                def archaea_count(archaea):
                    if len(archaea['microbes'])<4:
                        return archaea
                    else:
                        return archaea.head(4)

                def fungi_count(archaea,fungi):
                    if archaea['microbes'].count()==1:
                        return fungi.head(6)
                    elif archaea['microbes'].count()==2:
                        return fungi.head(5)
                    elif archaea['microbes'].count()==3:
                        return fungi.head(4)
                    else:
                        return fungi.head(3)
                    
            # --------------------------------------------------------------------------------------- #
            # -------------------------Taxonomy csv/json file system-----------------------------------#
            
            # concatenated_df = pd.concat([bacteria_df, fungi_df,archaea_df,composition_df,virus_df, score_df,gmhi_df,enterotype_df,final_keystone_df,final_probiotic_df,pathogen_merged,genus_df,phylum_df], ignore_index=True)
            # final_csv=concatenated_df.to_csv( index=False)
            # #print("Composition:",composition)
            import csv,io
            import csv 
            from flask import Response
            global output
            output=io.BytesIO()
            #print("Bacteria merged column name:",bacterial_merged.columns.tolist())
            #print("Archaea clomun name:",archaea_merged.columns.tolist())
            #print("Fungi column name:",fungi_merged.columns.tolist())
            #-----------------------------------------filtering process(from checkpoint sheet)------------------------------------------------------#
            # checkpoint_df=pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/checkpoint/Top Most Bacteria (Our DB)_Checkpoint.xlsx",sheet_name="Sheet1")
            # bacterial_merged_with_checkpoint=pd.merge(checkpoint_df,bacterial_merged,left_on="species",right_on="Species",how="inner")
            
            #---------------------------------------------------------------------------------------------------------------------------------------#
            archaea_1st_filtering=SpeciesCheckpoint.species_filtering(archaea_merged_sorted)
            fungi_1st_filtering=SpeciesCheckpoint.species_filtering(fungi_merged_sorted)
            all_dataframes = {
                "Gut Microbiome Health Index": gmhi_df,
                "Gut Microbiome Diversity Score(Shannon Index)": shannon_df,
                "Gut Microbial Community": composition_df,
                # top most abundance
                "Bacteria":bacterial_merged_sorted1,
                # "Bacteria":SpeciesCheckpoint.species_filtering(bacterial_merged),
                "Archaea":SpeciesCheckpoint.archaea_count(archaea_1st_filtering),
                "Fungi":SpeciesCheckpoint.fungi_count(SpeciesCheckpoint.archaea_count(archaea_1st_filtering),fungi_1st_filtering),
                # "Fungi":fungi_merged_sorted,
                # "Pathogen":'',
                "Detected Pathogen": pathogen_merged_sorted.head(15),
                "Not Detected": not_detected_pathogen_df.head(8),
                "Detected Probiotic": probiotic_merged_sorted.head(15),
                "Not detected probiotic": not_detected_probiotic_df.head(8),
                "Commensal (key-species)": final_keystone_sorted.head(22),
                "Enterotype": enterotype_df,

                
            }
            all_dataframes_json = {}

            for title, df in all_dataframes.items():
                if isinstance(df, pd.DataFrame):
                    all_dataframes_json[title] = df.to_dict(orient="records")
                else:
                    all_dataframes_json[title] = df  # If not a DataFrame, include as-is
                '''elif isinstance(probiotic_recommendation, list):  # Check if it's a DataFrame
                    # output.write("Recommendation:")  # Add title for Recommendation
                    output.write(','.join([','.join(probiotic_recommendation)]).encode('utf-8') + b'\n')
                    # output.write('"'+','.join(probiotic_recommendation)+'"'.encode('utf-8')+b'\n')'''
                '''else:
                    pass'''
            
            
            output.seek(0)
            #print("File is ready!!!")
            # server.close()

            
            
                
            # v1 = "'" + barcode + "'"
            function=db.engine.execute("SELECT * FROM function where Barcode=%s"%(v1))
            function1=function.fetchall()
            #print('function',function1)
            fc= pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/Production/Function Interpretation.xlsx",sheet_name="Metabolite Production ")
            fm= pd.read_excel("../DecodeBiomeDb/test_report_db_V1.4/static/Production/Function Interpretation.xlsx",sheet_name="Macronutrient Metabolism  ")
            
            if function1 !=[]:
                
                def curate_value(positiion,low,high,fc_row):
                    # list1=[]
                    for i in fc:
                        
                        if function1[0][positiion]<=low:
                            #list1=[i[fc_position_low] for i in fc]
                            #list1 = list(filter(lambda x: x != '', list1))
                            #list1=list1[0].split(',')
                            #return list1
                            # return list1.append(fc.iloc[fc_row,1])
                            return list(("Low",fc.iloc[fc_row,1]))
                            # return list1.append((fc.iloc[fc_row,1],"Low"))
                        elif function1[0][positiion] >high:
                            
                            # return list1.append((fc.iloc[fc_row,3],"Excess"))
                            return list(("Excess",fc.iloc[fc_row,3]))
                        else:
                            
                            # return list1.append((fc.iloc[fc_row,2],"Ideal"))
                            return list(("Ideal",fc.iloc[fc_row,2]))
                
                def metabolism_value(positiion,low,high,fc_row):

                    for i in fm:
                            
                        if function1[0][positiion]<=low:
                            #list1=[i[fc_position_low] for i in fc]
                            #list1 = list(filter(lambda x: x != '', list1))
                            #list1=list1[0].split(',')
                            return list(("Low",fm.iloc[fc_row,1]))
                            # return list1.append((fm.iloc[fc_row,1],"Low"))
                            # return list1.append(fm.iloc[fc_row,1])
                        elif function1[0][positiion] >high:
                            
                            # return list1.append((fm.iloc[fc_row,3],"Excess"))
                            # return list1.append(fm.iloc[fc_row,3])
                            return list(("Excess",fm.iloc[fc_row,3]))
                        else:
                            
                            # return list1.append((fm.iloc[fc_row,2],"Ideal"))
                            # return list1.append(fm.iloc[fc_row,2])
                            return list(("Ideal",fm.iloc[fc_row,2]))

                    
                acetate_value=curate_value(10,15.52,17.9,1)
                #print("Acetate type with value",acetate_value)
                butyrate_value=curate_value(11,43.04,46.88,3)
                propionate_value=curate_value(12,36.49,40.28,2)
                Gaba_value=curate_value(1,0.188,0.238,7)
                serotonin_value=curate_value(2,0.0025,0.0075,9)
                dopamin_value=curate_value(3,0.0025,0.0075,8)
                ammonina_value=curate_value(7,0.07,0.111,5)
                # ammonina_value=ammonia_curate_value(7,0.127,39,41,40)
                methane_value=curate_value(8,0.952,1.091,4)
                # methane_value=methane_curate_value(8,1.35,42,44,43)
                sulfid_value=curate_value(9,0.064,0.15,6)
                # file 2
                cholesterol_value=metabolism_value(4,0.043,0.115,5)
                phospholipid_value=metabolism_value(5,0.068,0.136,3)
                triglycerides_value=metabolism_value(6,0.0025,0.0075,4)
                carb_value=metabolism_value(17,51.89,53.67,1)
                protein_value=metabolism_value(18,35.21,36.86,2)
                # lipid_value=metabolism_value(21,63,77,9,11,10)
                # vitamin_value=metabolism_value(22,63,77,9,11,10)
                
                riboflavin_value=curate_value(13,16.6,22.83,10)
                biotin_value=curate_value(14,18.62,24.84,11)
                folate_value=curate_value(15,55.31,58.04,12)
                cobalamin_value=curate_value(16,1.42,2.6,13)
                # #print("acetate_value:::",str(acetate_value))
                
                scfa_data = [
                    ("Acetate", function1[0][10], "15.52-17.9", acetate_value[0],acetate_value[1]),
                    ("Butyrate", function1[0][11], "43.04-46.88", butyrate_value[0],butyrate_value[1]),
                    ("Propionate", function1[0][12], "36.49-40.28", propionate_value[0],propionate_value[1])
                ]

                # Create DataFrame
                scfa_df = pd.DataFrame(scfa_data, columns=["metabolicProfile", "relativeAbundance", "range","remarks", "interpretations"])
                scfa_json=scfa_df.to_dict('records')
                


                gutbrain_data = [
                    ("GABA", function1[0][1], "0.188-0.238", Gaba_value[0], Gaba_value[1]),
                    ("Serotonin", function1[0][2], "0.0025-0.0075", serotonin_value[0], serotonin_value[1]),
                    ("Dopamine", function1[0][3], "0.0025-0.0075", dopamin_value[0], dopamin_value[1])
                ]

                # Create DataFrame
                gutbrain_df = pd.DataFrame(gutbrain_data, columns=["metabolicProfile", "relativeAbundance", "range", "remarks", "interpretations"])
                gutbrain_json=gutbrain_df.to_dict('records')
                ammonina_value[1] = ammonina_value[1].replace("NH3", "NH₃")
                methane_value[1]= methane_value[1].replace("CH4", "CH₄")
                sulfid_value[1]=sulfid_value[1].replace("H2S", "H₂S")
                print("Ammonia",ammonina_value[1])
                # Data for the DataFrame
                gas_data = [
                    ("Ammonia", function1[0][7], "0.07-0.111", ammonina_value[0], ammonina_value[1]),
                    ("Methane", function1[0][8], "0.952-1.091", methane_value[0], methane_value[1]),
                    ("Hydrogen Sulfide", function1[0][9], "0.064-0.15", sulfid_value[0], sulfid_value[1])
                ]

                # Create DataFrame
                gas_df = pd.DataFrame(gas_data, columns=["metabolicProfile", "relativeAbundance", "range", "remarks", "interpretations"])
                gas_json=gas_df.to_dict('records')
            
                lipid_data = [
                    ("Cholesterol", function1[0][4], "0.043-0.115", cholesterol_value[0], cholesterol_value[1]),
                    ("Phospholipid", function1[0][5], "0.068-0.136", phospholipid_value[0], phospholipid_value[1]),
                    ("Triglycerides", function1[0][6], "0.0025-0.0075", triglycerides_value[0], triglycerides_value[1])
                ]
                
                # Create DataFrame
                lipid_df = pd.DataFrame(lipid_data, columns=["metabolicProfile", "relativeAbundance", "range", "remarks", "interpretations"])
                lipid_json=lipid_df.to_dict('records')
                
                metabolism_data = [
                    ("Carbohydrate", function1[0][17], "51.89-53.67", carb_value[0], carb_value[1]),
                    ("Protein", function1[0][18], "35.21-36.86", protein_value[0], protein_value[1])
                ]

                # Create DataFrame
                metabolism_df = pd.DataFrame(metabolism_data, columns=["metabolicProfile", "relativeAbundance", "range", "remarks", "interpretations"])
                metabolism_json=metabolism_df.to_dict('records')
                
                vitamin_data = [
                    ("Riboflavin", function1[0][13], "16.6-22.83", riboflavin_value[0], riboflavin_value[1]),
                    ("Biotin", function1[0][14], "18.62-24.84", biotin_value[0], biotin_value[1]),
                    ("Folate", function1[0][15], "55.31-58.04", folate_value[0], folate_value[1]),
                    ("Cobalamine", function1[0][16], "1.42-2.6", cobalamin_value[0], cobalamin_value[1])
                ]

                # Create DataFrame
                vitamin_df  = pd.DataFrame(vitamin_data, columns=["metabolicProfile", "relativeAbundance", "range", "remarks", "interpretations"])
                vitamin_json=vitamin_df.to_dict('records')
                
            # #print(vitamin_df)
            global function_output
            function_output=io.BytesIO()
            funct_dataframes=[scfa_df,gutbrain_df,gas_df,lipid_df,metabolism_df,vitamin_df]

            function_dataframe={
                "metabolism":metabolism_df,
                "lipid":lipid_df,
                "scfa":scfa_df,
                "gas":gas_df,
                "gutBrain":gutbrain_df,
                "vitamin":vitamin_df
            }
            function_dataframe_json = {}
            for title, df in function_dataframe.items():
                if isinstance(df, pd.DataFrame):
                    function_dataframe_json[title] = df.to_dict(orient="records")
                else:
                    function_dataframe_json[title] = df

            '''for i, df in enumerate(funct_dataframes):
                if i==0:
                    function_output.write(','.join(df.columns.tolist()).encode('utf-8')+b'\n')
                function_output.write(df.to_csv(index=False,header=False).encode('utf-8'))'''
            function_output.seek(0)
            # print("Content in function_output (before ZIP):", function_output.getvalue().decode('utf-8'))

            # server.close()
            v1_barcode=v1.split('_')[1]
            final_output = {
                "biomeScore": biomeScore,
                "diversityIndices": diversityIndeces,
                "gutComposition":composition_json,
                "topSpeciesBacteria":topSpeciesBacteria,
                "topSpeciesArchaea":topSpeciesArchaea,
                "topSpeciesFungi":topSpeciesFungi,
                "pathogen":pathogen_dict,
                "notDetectedPathogen" :not_detected_pathogen_dict,
                "probiotic":probiotic_json,
                "notDetectedProbiotic":not_detected_probiotic_json,
                "keystoneSpecies":key_stone_json,
                "enterotype":enterotype_json,
                "enterotypeRemarks":''.join(list(filter(None,enterotype_remarks))),
                "scfa":scfa_json,
                "gutBrain":gutbrain_json,
                "gas":gas_json,
                "lipid":lipid_json,
                "metabolism":metabolism_json,
                "vitamin":vitamin_json,
                

                }
            # print("Final json file",final_output)
            def replace_nan_with_empty_string(obj):
                if isinstance(obj, dict):
                    return {key: replace_nan_with_empty_string(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [replace_nan_with_empty_string(item) for item in obj]
                elif isinstance(obj, float) and pd.isna(obj):
                    return ""
                else:
                    return obj

            final_output_clean = replace_nan_with_empty_string(final_output)
            print("Enterotype remarks:",list(filter(None,enterotype_remarks)))
            json_output = json.dumps(final_output_clean, ensure_ascii=False, indent=4)
        # print("json_output formatting:",json_output)
        # return Response(json_output, mimetype='application/json')
        # return send_file(final_output_clean,mimetype='application/json',download_name="Json_report_%s.csv"%(v1),as_attachment=True)
        if request.endpoint=="report_generation":
            return final_output_clean
        elif request.endpoint=="view_taxa_func":
            html_tables = {title: df.to_html(classes='table table-striped', index=False) for title, df in all_dataframes.items() if isinstance(df, pd.DataFrame)}
            function_tables={title: df.to_html(classes='table table-striped',index=False) for title, df in function_dataframe.items() if isinstance(df,pd.DataFrame) }
            # return render_template('view_csv.html', tables=html_tables,function_tables=function_tables)
            return jsonify({
                "status": "success",
                "html_tables": html_tables,
                "function_tables": function_tables
            })
            # return "Babaji ka dullu"
        elif request.endpoint=="database_upload":
            # return "success"
            return upload_to_database()
# @app.route("/missing_curation",methods=['GET','POST'])
# def missing_curation():
#     return render_template("missing_curation.html")


salesforce_client_id = os.getenv("SALESFORCE_CLIENT_ID")
salesforce_client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
salesforce_username = os.getenv("SALESFORCE_USERNAME")
salesforce_password = os.getenv("SALESFORCE_PASSWORD")

@app.route('/handle_salesforce_integration', methods=['POST'])
def handle_salesforce_integration():
    # Get JSON data from the request
    # barcode=request.form.get('barcode')
    kit_barcode=barcode.split('_')[1]
    json_data = request.json
    
    # Salesforce OAuth2 Token Endpoint for Sandbox
    # 'client_id': '3MVG9GOcETU7CVrjKsZZw9XcY0k.GujdykhAzKE4APHhXJFQGgE9pGJB_anX9SQ3QImBAurwP37UGKxRlKt.4',
    # 'client_secret': '0CC33FAC69568B23D49F06170F5E84C7B25B17EB63AC0B14B62552738ECE8D92'
    # 'username': 'integrationuser@decodeage.com.partial',
    # 'password': 'Decode@2024GBpUgEBF3xPKg3OLjoIwcSoW'  
    # token_url = 'https://decodeage-health--partial.sandbox.my.salesforce.com/services/oauth2/token'
    # salesforce token
    token_url="https://decodeage-health.my.salesforce.com/services/oauth2/token"
    token_params = {
        'grant_type': os.getenv("SALESFORCE_GRANT_TYPE"),
        'client_id': os.getenv("SALESFORCE_CLIENT_ID"),
        'client_secret': os.getenv("SALESFORCE_CLIENT_SECRET"),
        'username': os.getenv("SALESFORCE_USERNAME"),
        'password': os.getenv("SALESFORCE_PASSWORD")
    }

    # Get the access token
    token_response = requests.post(token_url, data=token_params)
    if token_response.status_code == 200:
        token_data = token_response.json()
        access_token = token_data['access_token']

        # Prepare the PATCH request
        # patch_url = f"https://decodeage-health--partial.sandbox.my.salesforce.com/services/data/v61.0/sobjects/Report_Generation__c/Sample_Tube_Bar_Code__c/{kit_barcode}"
        patch_url=f"https://decodeage-health.my.salesforce.com/services/data/v61.0/sobjects/Report_Generation__c/Sample_Tube_Bar_Code__c/{kit_barcode}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            "Bio_Informatics_report_data_JSON__c": json.dumps(json_data)
        }

        # Make the PATCH request to Salesforce
        patch_response = requests.patch(patch_url, headers=headers, json=payload)
        if patch_response.status_code == 200:
            return jsonify({"message": "Salesforce update successful"}), 200
        else:
            return jsonify({"error": patch_response.text}), patch_response.status_code
    else:
        return jsonify({"Error": token_response.text}), token_response.status_code


'''
@app.route("/_updated_data",methods=["POST"])
def data_update():


    return "Something is not meaning"'''


@app.route("/_adding_curation_data",methods=['GET','POST'])
def adding_curation():
    
    try:
        # Assuming you have the data passed from the frontend (like from AJAX)
        data = request.get_json()  # Parse JSON request data
        
        microbe_name = data.get('microbes')
        domain = data.get('domain')
        print("Domain",domain)
        category = data.get('category')
        inflammatory_nature = data.get('inflammatoryNature')
        interpretation = data.get('interpretation')
        
        # Database connection setup
        db_connection = get_db_connection()
        cursor = db_connection.cursor()

        # Step 1: Get the existing DomainID, CategoryID, and NatureID for references
        cursor.execute("""
            SELECT DomainID FROM Domains WHERE DomainName = %s
        """, (domain,))
        domain_id = cursor.fetchone()
        if not domain_id:
            return jsonify({"status": "error", "message": "Domain not found"})

        cursor.execute("""
            SELECT CategoryID FROM Categories WHERE CategoryName = %s
        """, (category,))
        category_id = cursor.fetchone()
        if not category_id:
            return jsonify({"status": "error", "message": "Category not found"})

        cursor.execute("""
            SELECT NatureID FROM InflamatoryNature WHERE NatureName = %s
        """, (inflammatory_nature,))
        nature_id = cursor.fetchone()
        if not nature_id:
            return jsonify({"status": "error", "message": "Inflammatory nature not found"})

        # Step 2: Insert the new Microbe into the Microbes table using references
        cursor.execute("""
            INSERT INTO Microbes (MicrobeName, DomainID, CategoryID, NatureID)
            VALUES (%s, %s, %s, %s)
        """, (microbe_name, domain_id[0], category_id[0], nature_id[0]))
        
        # Get the inserted MicrobeID (this assumes you have auto-increment enabled on MicrobeID)
        cursor.execute("SELECT LAST_INSERT_ID()")
        microbe_id = cursor.fetchone()[0]  # Fetch the last inserted microbe ID
        
        # Step 3: Insert interpretation if provided
        if interpretation:
            cursor.execute("""
                INSERT INTO Interpretations (MicrobeID, InterpretationText)
                VALUES (%s, %s)
            """, (microbe_id, interpretation))
        
        # Commit the changes
        db_connection.commit()

        # Return success response
        return jsonify({"status": "success", "message": "Data added successfully", "addedData": data})

    except Exception as e:
        db_connection.rollback()  # Rollback in case of error
        return jsonify({"status": "error", "message": str(e)})

    finally:
        cursor.close()
        db_connection.close()
    return "Success in updating"
@app.route("/logo")
def logo():
    return render_template("logo.html")
if __name__=="__main__":
    app.run(debug=True,host="192.168.130.245",port=5552)
    