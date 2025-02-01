

# snowlfake schema
import pandas as pd
import mysql.connector as connector


class MicrobeDataTransfer:
    def __init__(self,host,user,database):
        self.host=host
        self.user=user
        self.database=database
        self.db_connection=None
        self.cursor=None

    def connect(self):
        """Estalish the connection to the database"""
        self.db_connection=connector.connect(
            host=self.host,
            user=self.user,
            database=self.database
        )
        self.cursor=self.db_connection.cursor()
    def disconnect(self):
        """Close the connection of database"""
        if self.cursor:
            self.cursor.close()
        if self.db_connection:
            self.db_connection.close()

    def get_data(self):
        """Fetch and return data from sql database as pandas dataframe"""
        if not self.db_connection or not self.cursor:
            raise Exception("Database connection is not established")

        # query to fetch required data from multiple tables
        query="""
            SELECT m.MicrobeID, m.MicrobeName, d.DomainName, c.CategoryName, n.NatureName, i.InterpretationText
            from Microbes m
            JOIN Domains d ON m.DomainID =d.DomainID
            JOIN Categories c ON m.CategoryId= c.CategoryID
            JOIN InflamatoryNature n ON m.NatureID=n.NatureID
            LEFT JOIN Interpretations i ON m.MicrobeID=i.MicrobeID
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        # create dataframe from query results
        df=pd.DataFrame(rows,columns=["MicrobeID","MicrobeName","Domain","Category","Inflammatory Nature","Interpretation"])
        return df
'''
class MicrobeDataAlter:
    def __init__(self,host,user,database):
        self.host=host
        self.user=user
        self.database=database
        self.db_connection=None
        self.cursor=None
    def connection(self):
        self.db_connection=connector.connect(
            host=self.host,
            user=self.user,
            database=self.database
        )
    self.cursor=self.db_connection.cursor()

    def disconnect(self):
        """Close the connection to the database"""
        if self.cursor:
            self.cursor.close()
        if self.db_connection:
            self.db_connection.close()

    def alter_data(self,microbe_id,category,inflammatory_nature,interpretation):
        """Update the microbe data in the database"""
        try:
            self.cursor.execute(
                """
                UPDATE Microbes 
                SET CategoryID =(SELECT CategoryID)

                """
            )

    def data_alter():

'''      
if __name__=="__main__":

    # extraction process from excel sheet into the sql in normalization tables
    '''
    # File paths for the Excel files
    file_paths = [
        "../test_report_db_V1.4/static/Production/Final Most Abundant Bacteria species Production (Curated by DC team).xlsx",
        "../test_report_db_V1.4/static/Production/Final Most Abundant Archaea species Production (Curated by DC team).xlsx",
        "../test_report_db_V1.4/static/Production/Final Most Abundant Fungal species Production (Curated by DC team).xlsx"
    ]
    sheet_name = "All Species"
    
    # Database credentials
    db_host = "0.0.0.0"
    db_user = "root"
    db_name = "curation_normalization"

    # Create an instance of the ETL process
    etl = MicrobeETL(file_paths, sheet_name, db_host, db_user, db_name)
    etl.run()
    '''
    transfer=MicrobeDataTransfer(host="0.0.0.0",user="root",database="curation_normalization")
    # connect to the database
    transfer.connect()

    # get the data as pandas dataframe
    df=transfer.get_data()

    # display the data as pandas dataframe
    print("Data loaded as dataframe:",df.columns)

    # disconnect from the database
    transfer.disconnect()

def get_db_connection():
    db_connection = connector.connect(
        host="0.0.0.0",
        user="root",
        database="curation_normalization"
    )
    return db_connection





