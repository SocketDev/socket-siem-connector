import sqlite3
from sqlite3 import Error
from core.socket_reports.classes import Report
import json
from core import log


class DatabaseNotExists(Exception):
    """Raised when the Sqlite3 DB does not exist"""
    def __init__(self, file, message="DB File does not exist"):
        self.file = file
        self.message = f"{message}: {self.file}"
        super().__init__(self.message)


class MissingSQLQuery(Exception):
    """Raised when the SQL Query is not passed to the function"""
    def __init__(self, query, message="SQL Query not provided"):
        self.query = query
        self.message = f"{message}: {query}"
        super().__init__(self.message)


class SqliteDB:

    def __init__(
            self,
            column_names: list,
            file_name="reports.db",
            reports_table="reports"
    ):
        self.log = log
        self.conn = None
        self.column_names = column_names
        self.reports_table = reports_table
        self.file_name = file_name
        self.check_for_db_file()
        self.create_reports_table()

    def check_for_db_file(self):
        """
        check_for_db_file Checks to see if the DB exists, errors if it doesn't
        :return:
        """
        # db_exists = os.path.exists(self.db_path)
        # if not db_exists:
        #     raise DatabaseNotExists(self.db_path)
        self.create_connection()

    def create_connection(self):
        """ create a database connection to a SQLite database """
        try:
            conn = sqlite3.connect(self.file_name)
            self.conn = conn
        except Error as e:
            self.log.error("Error connecting to patent DB", e)

    def run_sql_query(self, query, values=()):
        """
        run_query runs the provided query with values
        :param query: String type of the SQL Query
        :param values: Tuple list of the values for the SQL Query
        :return:
        """
        is_error = False
        if self.conn is None:
            self.create_connection()
        try:
            c = self.conn.cursor()
            c.execute(query, values)
            rows = c.fetchall()
            self.conn.commit()

            return is_error, rows
        except Error as e:
            is_error = True
            msg = {"error": f"{e}"}
            return is_error, msg

    def create_reports_table(self):
        """

        :return:
        """
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.reports_table} (
            id varchar(60) PRIMARY KEY,
            url text not null,
            repo varchar(200),
            branch varchar(200),
            `commit` varchar(50),
            pull_requests text,
            created_at varchar(25),
            processed bool default false
        );
        """
        is_error, result = self.run_sql_query(query)

        if is_error:
            err_msg_one = f"ERROR: Something went wrong creating table {self.reports_table}"
            err_msg_two = f"ERROR: {result}"
            self.log.error(err_msg_one)
            self.log.error(err_msg_two)
            exit(1)

    def add_reports_data(self, report: Report, column_names: list) -> None:
        column_str = ", ".join(column_names)
        values = ()
        for name in column_names:
            value = getattr(report, name)
            if name == "pull_requests":
                value = json.dumps(value)
            if value == "":
                value = None
            values += (value,)
        total_values = len(values)
        values_str = SqliteDB.create_value_string(total_values)
        query = f"INSERT INTO {self.reports_table} ({column_str}) VALUES {values_str} ON CONFLICT DO NOTHING"
        is_error, results = self.run_sql_query(query, values)
        if is_error:
            self.log.error(f"Unable to insert data into {self.reports_table} for {report.id}")
            self.log.error(results)

    def check_for_report(self, report: Report) -> bool:
        query = f"SELECT id FROM {self.reports_table} WHERE id = ?"
        values = (report.id,)
        is_error, results = self.run_sql_query(query, values)
        report_exists = False
        if is_error:
            self.log.error(f"Unable to run query for {self.reports_table} for {report.id}")
            self.log.error(results)
        else:
            if len(results) == 1:
                report_exists = True
        return report_exists

    def get_all_reports(self, column_names: list, processed: bool = False) -> list:
        column_str = ",".join(column_names)
        query = f"SELECT {column_str} FROM {self.reports_table} WHERE processed = ?"
        values = (processed,)
        is_error, results = self.run_sql_query(query, values)
        reports = []
        if is_error:
            self.log.error(f"Unable to retrieve reports")
            self.log.error(results)
        else:
            for item in results:
                report_data = {}
                for index, value in enumerate(item):
                    column = column_names[index]
                    if column == "pull_requests":
                        value = json.loads(value)
                    report_data[column] = value
                report = Report(**report_data)
                reports.append(report)
        return reports

    def update_report_state(self, report: Report, processed) -> None:
        query = f"UPDATE {self.reports_table} SET processed = ? WHERE id = ?"
        values = (processed, report.id)
        is_error, results = self.run_sql_query(query, values)
        if is_error:
            self.log.error(f"Unable to update report state for {report.id}")
            self.log.error(results)

    @staticmethod
    def create_value_string(number_of_values):
        counter = 0
        value_string = "("
        while counter != number_of_values:
            value_string += "?, "
            counter += 1
        value_string = value_string.rstrip(", ")
        value_string += ")"
        return value_string
