from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime, timedelta
import os
import paramiko
import pandas as pd
import re

# Load environment variables
from dotenv import load_dotenv
load_dotenv("../decodeageserver.env")

ssh_host = os.getenv("SERVER_IP")
ssh_username = os.getenv("SSH_USERNAME")
ssh_password = os.getenv("SSH_PASSWORD")

# Function to connect to remote server
def connect_to_server():
    server = paramiko.SSHClient()
    server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    server.connect(ssh_host, username=ssh_username, password=ssh_password)
    return server

# Function 1: Extract QC Data
def extract_qc_data(**kwargs):
    ti = kwargs['ti']
    server = connect_to_server()
    _stdin, _stdout, _stderr = server.exec_command("ls /path/to/ont_qc")
    all_runs = _stdout.read().decode().split('\n')
    run_dict = {run: [] for run in all_runs if run.startswith("RUN_")}
    
    for run_id in run_dict.keys():
        _stdin, _stdout, _stderr = server.exec_command(f"ls /path/to/ont_qc/{run_id}")
        files = _stdout.read().decode().split('\n')
        run_dict[run_id] = files
    
    ti.xcom_push(key='qc_data', value=run_dict)

# Function 2: Extract Taxonomy Data
def extract_taxonomy_data(**kwargs):
    ti = kwargs['ti']
    server = connect_to_server()
    _stdin, _stdout, _stderr = server.exec_command("ls /path/to/taxonomy_results")
    taxonomy_list = _stdout.read().decode().split('\n')
    
    ti.xcom_push(key='taxonomy_data', value=taxonomy_list)

# Function 3: Check Missing Curation
def check_missing_curation(**kwargs):
    ti = kwargs['ti']
    qc_data = ti.xcom_pull(task_ids='extract_qc_data', key='qc_data')
    taxonomy_data = ti.xcom_pull(task_ids='extract_taxonomy_data', key='taxonomy_data')

    missing_data = []
    for run, files in qc_data.items():
        if f"Taxonomy_{run}" not in taxonomy_data:
            missing_data.append(run)

    ti.xcom_push(key='missing_data', value=missing_data)

# Function 4: Generate Report
def generate_report(**kwargs):
    ti = kwargs['ti']
    missing_data = ti.xcom_pull(task_ids='check_missing_curation', key='missing_data')
    
    if missing_data:
        report_df = pd.DataFrame({'Missing Run': missing_data})
        report_df.to_csv("/tmp/missing_curation_report.csv", index=False)

# Define Airflow DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'bioinformatics_pipeline',
    default_args=default_args,
    description='Bioinformatics Data Extraction & Curation Check',
    schedule_interval=None,
    catchup=False,
)

task_extract_qc = PythonOperator(
    task_id='extract_qc_data',
    python_callable=extract_qc_data,
    provide_context=True,
    dag=dag,
)

task_extract_taxonomy = PythonOperator(
    task_id='extract_taxonomy_data',
    python_callable=extract_taxonomy_data,
    provide_context=True,
    dag=dag,
)

task_check_curation = PythonOperator(
    task_id='check_missing_curation',
    python_callable=check_missing_curation,
    provide_context=True,
    dag=dag,
)

task_generate_report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_report,
    provide_context=True,
    dag=dag,
)

# Define DAG Task Dependencies
task_extract_qc >> task_extract_taxonomy >> task_check_curation >> task_generate_report
