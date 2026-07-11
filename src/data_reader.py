import os
import sqlite3
import json

class Instance:
    def __init__(self,filename):
        self.filename = filename
        self.num_jobs = 0
        self.horizon = 0
        self.num_renewable = 0
        self.num_nonrenewable = 0

        self.successors = {}
        self.modes_data = {}
        self.res_capacities = {'R':[], 'N':[]}

        base_dir = os.path.dirname(os.path.abspath(filename))
        self.db_path = os.path.join(base_dir, 'mrcpsp_data.db')

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.load_mm_file_to_db(filename)
        self.fetch_from_db()

        self.predecessors = {i: [] for i in range(1, self.num_jobs+1)}
        for job, succs in self.successors.items():
            for succ in succs:
                self.predecessors[succ].append(job)
    
    def load_mm_file_to_db(self,filename):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.executescript('''
            DROP TABLE IF EXISTS Precedences;
            DROP TABLE IF EXISTS Modes;
            DROP TABLE IF EXISTS Capacities;

            CREATE TABLE Precedences (job_id INTEGER, successors TEXT);
            CREATE TABLE Modes (job_id INTEGER, mode_id INTEGER, duration INTEGER, req_R TEXT, req_N TEXT);
            CREATE TABLE Capacities (type TEXT, capacities TEXT);
        ''')

        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_section = None
        last_job_read = 0

        for line in lines:
            line = line.strip()
            if not line or line.startswith('*'):continue

            if "jobs (incl. supersource/sink ):" in line:
                self.num_jobs = int(line.split(":")[1])
            elif "horizon" in line:
                self.horizon = int(line.split(":")[1])
            elif "- renewable" in line:
                self.num_renewable = int(line.split(":")[1].split()[0])
            elif "- nonrenewable" in line:
                self.num_nonrenewable = int(line.split(":")[1].split()[0])
            
            if line == "PRECEDENCE RELATIONS:": current_section = "PRECEDENCE"
            elif line == "REQUESTS/DURATIONS:": current_section = "REQUESTS"
            elif line == "RESOURCEAVAILABILITIES:": current_section = "AVAILABILITIES"

            if current_section == "PRECEDENCE" and line and line[0].isdigit():
                parts = line.split()
                if len(parts) >= 3:
                    job_id = int(parts[0])
                    succs = [int(p) for p in parts[3:3+int(parts[2])]]
                    cursor.execute("INSERT INTO Precedences VALUES (?, ?)", (job_id, json.dumps(succs)))

            elif current_section == "REQUESTS" and line and line[0].isdigit():
                parts = line.split()
                if len(parts) >= 6:
                    if len(parts) == 6:
                        current_job, mode, duration, reqs = last_job_read, int(parts[0]), int(parts[1]), [int(p) for p in parts[2:]]
                    else:
                        current_job, last_job_read, mode, duration, reqs = int(parts[0]), int(parts[0]), int(parts[1]), int(parts[2]), [int(p) for p in parts[3:]]

                    req_r = reqs[:self.num_renewable]
                    req_n = reqs[self.num_renewable:]
                    cursor.execute("INSERT INTO Modes VALUES (?,?,?,?,?)",
                                    (current_job, mode, duration, json.dumps(req_r), json.dumps(req_n)))
            
            elif current_section == "AVAILABILITIES" and line and line[0].isdigit():
                parts = [int(p) for p in line.split()]
                cap_r = parts[:self.num_renewable]
                cap_n = parts[self.num_renewable:]
                cursor.execute("INSERT INTO Capacities VALUES (?,?)", ("R", json.dumps(cap_r)))
                cursor.execute("INSERT INTO Capacities VALUES (?,?)", ("N", json.dumps(cap_n)))
        
        conn.commit()
        conn.close()

    def fetch_from_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT job_id, successors FROM Precedences")
        for row in cursor.fetchall():
            self.successors[row[0]] = json.loads(row[1])

        cursor.execute("SELECT job_id, mode_id, duration, req_R, req_N FROM Modes")
        for row in cursor.fetchall():
            job_id, mode_id, duration, req_r, req_n = row
            if job_id not in self.modes_data:
                self.modes_data[job_id]={}
            self.modes_data[job_id][mode_id]={
                'duration': duration,
                'R': json.loads(req_r),
                'N': json.loads(req_n)
            }
        
        cursor.execute("SELECT type, capacities FROM Capacities")
        for row in cursor.fetchall():
            self.res_capacities[row[0]] = json.loads(row[1])
        
        conn.close()

class Solution:
    def __init__(self, instance):
        self.instance = instance
        self.sequence = []
        self.modes = {}
        self.start_times = {}
        self.makespan = 0.0
        self.is_feasible = False