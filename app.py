from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)
DB_PATH = 'immunisation.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def landing():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT MIN(year), MAX(year) FROM InfectionData")
    year_range = cur.fetchone()
    cur.execute("SELECT SUM(doses) FROM Vaccination")
    total_doses = cur.fetchone()[0]
    cur.execute("SELECT SUM(cases) FROM InfectionData")
    total_cases = cur.fetchone()[0]
    cur.execute("SELECT description FROM Infection_Type")
    diseases = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT COUNT(DISTINCT country) FROM InfectionData")
    total_countries = cur.fetchone()[0]
    conn.close()
    return render_template('landing.html',
        year_min=year_range[0], year_max=year_range[1],
        total_doses=int(total_doses), total_cases=int(total_cases),
        diseases=diseases, total_countries=total_countries)

@app.route('/mission')
def mission():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Persona")
    personas = cur.fetchall()
    cur.execute("SELECT * FROM TeamMember")
    team = cur.fetchall()
    conn.close()
    return render_template('mission.html', personas=personas, team=team)

@app.route('/vaccination-rates', methods=['GET'])
def vaccination_rates():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT AntigenID, name FROM Antigen ORDER BY name")
    antigens = cur.fetchall()
    cur.execute("SELECT RegionID, region FROM Region ORDER BY region")
    regions = cur.fetchall()
    cur.execute("SELECT DISTINCT year FROM Vaccination ORDER BY year DESC")
    years = [row['year'] for row in cur.fetchall()]
    sel_ant = request.args.get('antigen', 'MCV1')
    sel_yr  = request.args.get('year', '2023')
    sel_reg = request.args.get('region', '')
    q1 = '''SELECT c.name AS country, r.region, a.name AS antigen, v.year,
        v.doses, v.target_num,
        ROUND(CAST(v.doses AS FLOAT)/v.target_num*100,1) AS pct
        FROM Vaccination v
        JOIN Country c ON v.country=c.CountryID
        JOIN Region r ON c.region=r.RegionID
        JOIN Antigen a ON v.antigen=a.AntigenID
        WHERE v.antigen=? AND v.year=? AND v.target_num>0
        AND v.doses!='' AND CAST(v.doses AS FLOAT)/v.target_num*100>=90'''
    p1 = [sel_ant, sel_yr]
    if sel_reg:
        q1 += ' AND r.RegionID=?'
        p1.append(sel_reg)
    q1 += ' ORDER BY pct DESC'
    cur.execute(q1, p1)
    countries_met = cur.fetchall()
    cur.execute('''SELECT r.region, COUNT(*) AS countries_met,
        ROUND(AVG(CAST(v.doses AS FLOAT)/v.target_num*100),1) AS avg_pct
        FROM Vaccination v
        JOIN Country c ON v.country=c.CountryID
        JOIN Region r ON c.region=r.RegionID
        JOIN Antigen a ON v.antigen=a.AntigenID
        WHERE v.antigen=? AND v.year=? AND v.target_num>0
        AND v.doses!='' AND CAST(v.doses AS FLOAT)/v.target_num*100>=90
        GROUP BY r.region ORDER BY countries_met DESC''', [sel_ant, sel_yr])
    region_summary = cur.fetchall()
    conn.close()
    return render_template('vaccination_rates.html',
        antigens=antigens, regions=regions, years=years,
        sel_antigen=sel_ant, sel_year=int(sel_yr), sel_region=sel_reg,
        countries_met=countries_met, region_summary=region_summary)

@app.route('/infection-by-economy', methods=['GET'])
def infection_by_economy():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT economyID, phase FROM Economy ORDER BY economyID")
    economies = cur.fetchall()
    cur.execute("SELECT id, description FROM Infection_Type ORDER BY description")
    inf_types = cur.fetchall()
    cur.execute("SELECT DISTINCT year FROM InfectionData ORDER BY year DESC")
    years = [row['year'] for row in cur.fetchall()]
    sel_eco = request.args.get('economy', '')
    sel_inf = request.args.get('inf_type', 'MEA')
    sel_yr  = request.args.get('year', '2020')
    q1 = '''SELECT c.name AS country, e.phase AS economy,
        i.description AS disease, inf.year, inf.cases, cp.population,
        ROUND(inf.cases/(cp.population/100000.0),2) AS per_100k
        FROM InfectionData inf
        JOIN Country c ON inf.country=c.CountryID
        JOIN Economy e ON c.economy=e.economyID
        JOIN Infection_Type i ON inf.inf_type=i.id
        JOIN CountryPopulation cp ON cp.country=inf.country AND cp.year=inf.year
        WHERE inf.inf_type=? AND inf.year=? AND inf.cases>0 AND cp.population>0'''
    p1 = [sel_inf, sel_yr]
    if sel_eco:
        q1 += ' AND e.economyID=?'
        p1.append(sel_eco)
    q1 += ' ORDER BY per_100k DESC'
    cur.execute(q1, p1)
    country_rows = cur.fetchall()
    cur.execute('''SELECT e.phase AS economy, COUNT(DISTINCT inf.country) AS num_countries,
        SUM(inf.cases) AS total_cases,
        ROUND(SUM(inf.cases)/(SUM(cp.population)/100000.0),2) AS avg_per_100k
        FROM InfectionData inf
        JOIN Country c ON inf.country=c.CountryID
        JOIN Economy e ON c.economy=e.economyID
        JOIN Infection_Type i ON inf.inf_type=i.id
        JOIN CountryPopulation cp ON cp.country=inf.country AND cp.year=inf.year
        WHERE inf.inf_type=? AND inf.year=? AND inf.cases>0 AND cp.population>0
        GROUP BY e.phase, e.economyID ORDER BY e.economyID ASC''', [sel_inf, sel_yr])
    economy_summary = cur.fetchall()
    conn.close()
    return render_template('infection_by_economy.html',
        economies=economies, inf_types=inf_types, years=years,
        sel_economy=sel_eco, sel_inf_type=sel_inf, sel_year=int(sel_yr),
        country_rows=country_rows, economy_summary=economy_summary)

@app.route('/biggest-improvement', methods=['GET'])
def biggest_improvement():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT AntigenID, name FROM Antigen ORDER BY name")
    antigens = cur.fetchall()
    cur.execute("SELECT DISTINCT year FROM Vaccination ORDER BY year ASC")
    years = [row['year'] for row in cur.fetchall()]
    sel_ant = request.args.get('antigen', 'MCV1')
    sel_sy  = request.args.get('start_year', '2000')
    sel_ey  = request.args.get('end_year', '2023')
    sel_n   = request.args.get('top_n', '10')
    try:
        top_n = max(1, min(50, int(sel_n)))
    except ValueError:
        top_n = 10
    results = []
    error_msg = None
    if int(sel_sy) >= int(sel_ey):
        error_msg = "Start year must be earlier than end year."
    else:
        cur.execute('''SELECT c.name AS country,
            v1.year AS start_year, v2.year AS end_year,
            ROUND(CAST(v1.doses AS FLOAT)/v1.target_num*100,1) AS start_pct,
            ROUND(CAST(v2.doses AS FLOAT)/v2.target_num*100,1) AS end_pct,
            ROUND((CAST(v2.doses AS FLOAT)/v2.target_num -
                   CAST(v1.doses AS FLOAT)/v1.target_num)*100,1) AS improvement
            FROM Vaccination v1
            JOIN Vaccination v2 ON v1.country=v2.country AND v1.antigen=v2.antigen
            JOIN Country c ON v1.country=c.CountryID
            WHERE v1.antigen=? AND v1.year=? AND v2.year=?
            AND v1.target_num>0 AND v2.target_num>0
            AND v1.doses!='' AND v2.doses!=''
            AND improvement>0
            ORDER BY improvement DESC LIMIT ?''',
            [sel_ant, sel_sy, sel_ey, top_n])
        results = cur.fetchall()
    conn.close()
    return render_template('biggest_improvement.html',
        antigens=antigens, years=years, sel_antigen=sel_ant,
        sel_start_year=int(sel_sy), sel_end_year=int(sel_ey),
        sel_top_n=top_n, results=results, error_msg=error_msg)

@app.route('/above-average', methods=['GET'])
def above_average():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, description FROM Infection_Type ORDER BY description")
    inf_types = cur.fetchall()
    cur.execute("SELECT DISTINCT year FROM InfectionData ORDER BY year DESC")
    years = [row['year'] for row in cur.fetchall()]
    sel_inf = request.args.get('inf_type', 'MEA')
    sel_yr  = request.args.get('year', '2020')
    subquery = '''SELECT SUM(inf2.cases)/(SUM(cp2.population)/100000.0)
        FROM InfectionData inf2
        JOIN CountryPopulation cp2 ON cp2.country=inf2.country AND cp2.year=inf2.year
        WHERE inf2.inf_type=? AND inf2.year=? AND inf2.cases>0 AND cp2.population>0'''
    cur.execute(subquery, [sel_inf, sel_yr])
    avg_row = cur.fetchone()
    global_avg = round(avg_row[0], 2) if avg_row and avg_row[0] else 0
    cur.execute(f'''SELECT c.name AS country, i.description AS disease, inf.year,
        inf.cases, cp.population,
        ROUND(inf.cases/(cp.population/100000.0),2) AS per_100k,
        ROUND(({subquery}),2) AS global_avg,
        ROUND(inf.cases/(cp.population/100000.0)-({subquery}),2) AS above_by
        FROM InfectionData inf
        JOIN Country c ON inf.country=c.CountryID
        JOIN Infection_Type i ON inf.inf_type=i.id
        JOIN CountryPopulation cp ON cp.country=inf.country AND cp.year=inf.year
        WHERE inf.inf_type=? AND inf.year=? AND inf.cases>0 AND cp.population>0
        AND inf.cases/(cp.population/100000.0)>({subquery})
        ORDER BY per_100k DESC''',
        [sel_inf, sel_yr, sel_inf, sel_yr, sel_inf, sel_yr, sel_inf, sel_yr])
    results = cur.fetchall()
    conn.close()
    return render_template('above_average.html',
        inf_types=inf_types, years=years,
        sel_inf_type=sel_inf, sel_year=int(sel_yr),
        global_avg=global_avg, results=results)

if __name__ == '__main__':
    app.run(debug=True)
