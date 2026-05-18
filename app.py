from flask import Flask, render_template
import database as db

app = Flask(__name__)

@app.route('/')
def landing():
    conn = db.get_db_connection()
    
    # 4 facts cho Landing Page (Level 1A)
    total_countries = conn.execute("SELECT COUNT(DISTINCT country) FROM countries").fetchone()[0]
    years = conn.execute("SELECT MIN(year), MAX(year) FROM vaccination").fetchone()
    diseases = conn.execute("SELECT DISTINCT disease FROM infections").fetchall()
    
    conn.close()

    facts = {
        'total_countries': total_countries,
        'year_range': f"{years[0]} - {years[1]}",
        'num_diseases': len(diseases),
        'diseases': [d[0] for d in diseases[:6]]  # Lấy 6 bệnh đầu
    }

    return render_template('level1/landing.html', facts=facts)

@app.route('/mission')
def mission():
    return render_template('level1/mission.html')

if __name__ == '__main__':
    app.run(debug=True)