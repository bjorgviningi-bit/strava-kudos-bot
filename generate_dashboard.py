import json
import os
from datetime import datetime

def generate_dashboard():
    # Read the JSON data file
    try:
        with open('running_data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: running_data.json not found. Run running_analysis.py first.")
        return
    
    monthly_data = data.get('monthly', {})
    overall = data.get('overall', {})
    
    # Prepare data for charts
    months_list = sorted(monthly_data.get('count', {}).keys())
    
    # Generate HTML dashboard
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Hlaupa Mælaborð - Running Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #FC4C02;
            text-align: center;
        }}
        .summary {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .summary-item {{
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border-left: 4px solid #FC4C02;
        }}
        .summary-item h3 {{
            margin: 0 0 5px 0;
            font-size: 14px;
            color: #666;
        }}
        .summary-item p {{
            margin: 0;
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .chart {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .updated {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <h1>🏃 Hlaupa Mælaborð</h1>
    
    <div class="summary">
        <h2>Heildaryfirlit</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <h3>Heildar hlaup</h3>
                <p>{overall.get('total_runs', 0):,.0f}</p>
            </div>
            <div class="summary-item">
                <h3>Heildar kílómetrar</h3>
                <p>{overall.get('total_distance_km', 0):,.1f} km</p>
            </div>
            <div class="summary-item">
                <h3>Heildar tími</h3>
                <p>{overall.get('total_time_hours', 0):,.1f} klst</p>
            </div>
            <div class="summary-item">
                <h3>Meðal km á hlaup</h3>
                <p>{overall.get('avg_distance_per_run', 0):.1f} km</p>
            </div>
            <div class="summary-item">
                <h3>Meðal hraði</h3>
                <p>{overall.get('avg_pace_min_per_km', 0):.2f} mín/km</p>
            </div>
            <div class="summary-item">
                <h3>Heildar hækkun</h3>
                <p>{overall.get('total_elevation_m', 0):,.0f} m</p>
            </div>
        </div>
    </div>
    
    <div class="chart" id="distance-chart"></div>
    <div class="chart" id="count-chart"></div>
    <div class="chart" id="pace-chart"></div>
    <div class="chart" id="hr-chart"></div>
    <div class="chart" id="treemap-distance"></div>
    <div class="chart" id="treemap-count"></div>
    
    <div class="updated">Uppfært: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    
    <script>
        const monthlyData = {json.dumps(monthly_data)};
        
        // Parse dates and prepare data
        const months = Object.keys(monthlyData.count || {{}}).sort();
        const distances = months.map(m => monthlyData.distance_km[m] || 0);
        const counts = months.map(m => monthlyData.count[m] || 0);
        const paces = months.map(m => monthlyData.pace_min_per_km[m] || null);
        const hrs = months.map(m => monthlyData.avg_hr_bpm[m] || null);
        
        // Distance over time
        Plotly.newPlot('distance-chart', [{{
            x: months,
            y: distances,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Mánaðarleg vegalengd',
            line: {{color: '#FC4C02', width: 3}},
            marker: {{size: 6}}
        }}], {{
            title: 'Mánaðarleg hlaupavegalengd (km)',
            xaxis: {{title: 'Mánuður'}},
            yaxis: {{title: 'Kílómetrar'}},
            hovermode: 'closest'
        }}, {{responsive: true}});
        
        // Run count over time
        Plotly.newPlot('count-chart', [{{
            x: months,
            y: counts,
            type: 'bar',
            name: 'Fjöldi hlaupa',
            marker: {{color: '#FC4C02'}}
        }}], {{
            title: 'Fjöldi hlaupa á mánuði',
            xaxis: {{title: 'Mánuður'}},
            yaxis: {{title: 'Fjöldi hlaupa'}},
            hovermode: 'closest'
        }}, {{responsive: true}});
        
        // Average pace over time
        Plotly.newPlot('pace-chart', [{{
            x: months,
            y: paces,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Meðal hraði',
            line: {{color: '#1E88E5', width: 2}},
            marker: {{size: 5}}
        }}], {{
            title: 'Meðal hlaupahraði (mín/km)',
            xaxis: {{title: 'Mánuður'}},
            yaxis: {{title: 'Mínútur á kílómetra', autorange: 'reversed'}},
            hovermode: 'closest'
        }}, {{responsive: true}});
        
        // Heart rate over time (if available)
        if (hrs.some(hr => hr !== null)) {{
            Plotly.newPlot('hr-chart', [{{
                x: months,
                y: hrs,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Meðal hjartsláttur',
                line: {{color: '#D32F2F', width: 2}},
                marker: {{size: 5}}
            }}], {{
                title: 'Meðal hjartsláttur (slög/mín)',
                xaxis: {{title: 'Mánuður'}},
                yaxis: {{title: 'Hjartsláttur (bpm)'}},
                hovermode: 'closest'
            }}, {{responsive: true}});
        }} else {{
            document.getElementById('hr-chart').innerHTML = '<p style="text-align:center;color:#999;">Hjartsláttagögn ekki tiltæk</p>';
        }}
        
        // Treemap for distance by year and month
        const treemapDistanceData = [];
        const yearMonthMap = {{}};
        
        months.forEach(monthKey => {{
            const [year, month] = monthKey.split('-');
            if (!yearMonthMap[year]) {{
                yearMonthMap[year] = [];
            }}
            yearMonthMap[year].push({{
                month: monthKey,
                distance: monthlyData.distance_km[monthKey] || 0,
                count: monthlyData.count[monthKey] || 0
            }});
        }});
        
        const labels = ['Allt'];
        const parents = [''];
        const values = [0];
        const colors = [];
        
        Object.keys(yearMonthMap).sort().reverse().forEach(year => {{
            labels.push(year);
            parents.push('Allt');
            let yearTotal = 0;
            yearMonthMap[year].forEach(m => yearTotal += m.distance);
            values.push(yearTotal);
            colors.push('#FC4C02');
            
            yearMonthMap[year].forEach(m => {{
                labels.push(m.month);
                parents.push(year);
                values.push(m.distance);
                colors.push('#FFA726');
            }});
        }});
        
        Plotly.newPlot('treemap-distance', [{{
            type: 'treemap',
            labels: labels,
            parents: parents,
            values: values,
            textinfo: 'label+value+percent parent',
            marker: {{colors: colors}},
            hovertemplate: '<b>%{{label}}</b><br>%{{value:.1f}} km<br>%{{percentParent}}<extra></extra>'
        }}], {{
            title: 'Vegalengd eftir ári og mánuði (km)',
            margin: {{t: 50, l: 0, r: 0, b: 0}}
        }}, {{responsive: true}});
        
        // Treemap for run count
        const labelsCount = ['Allt'];
        const parentsCount = [''];
        const valuesCount = [0];
        
        Object.keys(yearMonthMap).sort().reverse().forEach(year => {{
            labelsCount.push(year);
            parentsCount.push('Allt');
            let yearTotal = 0;
            yearMonthMap[year].forEach(m => yearTotal += m.count);
            valuesCount.push(yearTotal);
            
            yearMonthMap[year].forEach(m => {{
                labelsCount.push(m.month);
                parentsCount.push(year);
                valuesCount.push(m.count);
            }});
        }});
        
        Plotly.newPlot('treemap-count', [{{
            type: 'treemap',
            labels: labelsCount,
            parents: parentsCount,
            values: valuesCount,
            textinfo: 'label+value+percent parent',
            marker: {{colors: ['#1E88E5', '#42A5F5', '#90CAF9']}},
            hovertemplate: '<b>%{{label}}</b><br>%{{value}} hlaup<br>%{{percentParent}}<extra></extra>'
        }}], {{
            title: 'Fjöldi hlaupa eftir ári og mánuði',
            margin: {{t: 50, l: 0, r: 0, b: 0}}
        }}, {{responsive: true}});
    </script>
</body>
</html>
'''
    
    # Write HTML file
    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✓ Dashboard generated: dashboard.html")
    print("  Open this file in your browser to view the dashboard.")

if __name__ == "__main__":
    generate_dashboard()
